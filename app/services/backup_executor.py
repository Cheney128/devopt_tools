"""
批量备份执行器服务
支持并发控制和失败重试机制
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Device
from app.models.backup_task import BackupTask, BackupTaskStatus
from app.services.config_collection_service import collect_device_config
from app.services.netmiko_service import NetmikoService
from app.services.git_service import GitService

logger = logging.getLogger(__name__)


class BackupExecutor:
    """批量备份执行器 - 支持并发控制和失败重试"""
    
    def __init__(self, max_concurrent: int = 3, timeout: int = 300):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._cancelled_tasks: set = set()
    
    def cancel_task(self, task_id: str):
        """标记任务为取消状态"""
        self._cancelled_tasks.add(task_id)
    
    def is_task_cancelled(self, task_id: str) -> bool:
        """检查任务是否被取消"""
        return task_id in self._cancelled_tasks
    
    async def execute_backup_all(
        self,
        task_id: str,
        device_ids: List[int],
        db: Session,
        retry_count: int = 2
    ) -> Dict[str, Any]:
        """执行批量备份"""
        task = db.query(BackupTask).filter(BackupTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        task.status = BackupTaskStatus.RUNNING
        task.started_at = datetime.now()
        db.commit()
        
        results = []
        
        async def execute_with_retry(device_id: int) -> Dict[str, Any]:
            """执行单个设备备份，带重试机制"""
            async with self.semaphore:
                if self.is_task_cancelled(task_id):
                    return {
                        "device_id": device_id,
                        "success": False,
                        "error_message": "任务已取消",
                        "error_code": "TASK_CANCELLED"
                    }
                
                for attempt in range(retry_count + 1):
                    try:
                        result = await self._execute_single_backup(
                            device_id, db, task_id
                        )
                        
                        task.completed += 1
                        if result.get("success"):
                            task.success_count += 1
                        else:
                            task.failed_count += 1
                        db.commit()
                        
                        return result
                    except Exception as e:
                        logger.warning(
                            f"设备 {device_id} 第 {attempt + 1} 次备份失败: {str(e)}"
                        )
                        if attempt == retry_count:
                            task.completed += 1
                            task.failed_count += 1
                            db.commit()
                            return {
                                "device_id": device_id,
                                "success": False,
                                "error_message": str(e),
                                "error_code": "MAX_RETRIES_EXCEEDED"
                            }
                        await asyncio.sleep(2 ** attempt)
                
                return {"device_id": device_id, "success": False, "error_message": "未知错误"}
        
        tasks = [execute_with_retry(device_id) for device_id in device_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        errors = []
        for r in results:
            if isinstance(r, Exception):
                error_result = {
                    "device_id": None,
                    "success": False,
                    "error_message": str(r),
                    "error_code": "EXECUTION_ERROR"
                }
                processed_results.append(error_result)
                errors.append(error_result)
            else:
                processed_results.append(r)
                if not r.get("success"):
                    errors.append(r)
        
        if self.is_task_cancelled(task_id):
            task.status = BackupTaskStatus.CANCELLED
        elif task.failed_count == 0:
            task.status = BackupTaskStatus.COMPLETED
        elif task.success_count == 0:
            task.status = BackupTaskStatus.FAILED
        else:
            task.status = BackupTaskStatus.COMPLETED
        
        task.completed_at = datetime.now()
        task.error_details = {"errors": errors} if errors else None
        db.commit()
        
        self._cancelled_tasks.discard(task_id)
        
        return {
            "task_id": task_id,
            "total": len(device_ids),
            "completed": task.completed,
            "success_count": task.success_count,
            "failed_count": task.failed_count,
            "results": processed_results
        }
    
    async def _execute_single_backup(
        self,
        device_id: int,
        db: Session,
        task_id: str
    ) -> Dict[str, Any]:
        """执行单个设备备份"""
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {
                "device_id": device_id,
                "success": False,
                "error_message": f"设备不存在: {device_id}",
                "error_code": "DEVICE_NOT_FOUND"
            }
        
        start_time = datetime.now()

        try:
            # 创建服务实例并调用配置采集服务函数（M6：不再调用 API 函数）
            netmiko_service = NetmikoService()
            git_service = GitService()
            result = await collect_device_config(device_id, db, netmiko_service, git_service)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "device_id": device_id,
                "device_name": device.hostname or device.name,
                "success": result.get("success", False),
                "config_id": result.get("config_id"),
                "execution_time": execution_time,
                "config_size": result.get("config_size", 0),
                "git_commit_id": result.get("git_commit_id"),
                "error_message": result.get("error")
            }
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"设备 {device_id} 备份失败: {str(e)}")
            
            return {
                "device_id": device_id,
                "device_name": device.hostname or device.name,
                "success": False,
                "error_message": str(e),
                "execution_time": execution_time,
                "error_code": "BACKUP_ERROR"
            }
    
    async def cleanup(self):
        """清理资源"""
        pass


backup_executor = BackupExecutor()
