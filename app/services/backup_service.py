
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Device, Configuration, GitConfig, BackupSchedule, BackupExecutionLog
from app.services.netmiko_service import NetmikoService
from app.services.git_service import GitService

logger = logging.getLogger(__name__)


class BackupService:
    def __init__(self):
        self.netmiko_service = NetmikoService()
        self.git_service = GitService()
    
    async def collect_config(
        self, 
        device_id: int, 
        db: Session
    ) -> Dict[str, Any]:
        logger.info(f"[BackupService] Querying device {device_id}...")
        
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            logger.warning(f"[BackupService] Device {device_id} not found")
            return {"success": False, "message": "Device not found"}
        
        logger.info(f"[BackupService] Collecting config from device {device.hostname}...")
        
        config_content = await self.netmiko_service.collect_running_config(device)
        if not config_content:
            logger.warning(f"[BackupService] Failed to get config from device {device.hostname}")
            return {"success": False, "message": "Failed to get config from device"}
        
        latest_config = db.query(Configuration).filter(
            Configuration.device_id == device_id
        ).order_by(Configuration.config_time.desc()).first()
        
        if latest_config and latest_config.config_content == config_content:
            logger.info(f"[BackupService] Config unchanged for device {device.hostname}")
            return {
                "success": True,
                "message": "配置无变化，已成功登录并验证",
                "config_id": latest_config.id,
                "config_changed": False,
                "config_size": len(config_content) if config_content else 0
            }
        
        logger.info(f"[BackupService] Config changed for device {device.hostname}")
        
        new_version = "1.0"
        if latest_config:
            current_version = latest_config.version
            try:
                major, minor = map(int, current_version.split("."))
                new_version = f"{major}.{minor + 1}"
            except:
                new_version = "1.0"
        
        logger.info(f"[BackupService] Creating new version {new_version} for device {device.hostname}")
        
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content,
            version=new_version,
            change_description="Auto-collected from device"
        )
        
        git_commit_id = None
        try:
            git_config = db.query(GitConfig).filter(GitConfig.is_active == True).first()
            if git_config:
                logger.info(f"[BackupService] Git config found, committing to Git...")
                from app.services.git_service import GitService
                device_git_service = GitService()
                if device_git_service.init_repo(git_config):
                    commit_id = device_git_service.commit_config(
                        device.hostname,
                        config_content,
                        f"Auto-update config for {device.hostname} at {datetime.now()}"
                    )
                    if commit_id:
                        device_git_service.push_to_remote()
                        git_commit_id = commit_id
                        new_config.git_commit_id = commit_id
                        logger.info(f"[BackupService] Git commit successful: {commit_id}")
                    device_git_service.close()
        except Exception as git_error:
            logger.error(f"[BackupService] Git operation error: {str(git_error)}")
        
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        logger.info(f"[BackupService] Config saved successfully, config_id: {new_config.id}")
        
        return {
            "success": True,
            "message": "Config collected from device and saved",
            "config_id": new_config.id,
            "config_changed": True,
            "config_size": len(config_content) if config_content else 0,
            "git_commit_id": git_commit_id,
            "version": new_version
        }
    
    async def execute_scheduled_backup(
        self, 
        device_id: int, 
        db: Session,
        task_id: str
    ) -> Dict[str, Any]:
        logger.info(f"[BackupService] Executing scheduled backup, task_id={task_id}")
        
        started_at = datetime.now()
        execution_log = None
        
        try:
            logger.info(f"[BackupService] Calling collect_config()...")
            result = await self.collect_config(device_id, db)
            
            execution_time = (datetime.now() - started_at).total_seconds()
            
            logger.info(f"[BackupService] Querying backup schedule for device {device_id}...")
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()
            
            config_changed = result.get("config_changed", True)
            logger.info(f"[BackupService] Config changed: {config_changed}")
            
            error_message = None
            if not config_changed:
                error_message = "配置无变化，已成功登录并验证设备配置"
            
            logger.info(f"[BackupService] Creating execution log...")
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="success" if result.get("success") else "failed",
                execution_time=execution_time,
                trigger_type="scheduled",
                config_id=result.get("config_id"),
                config_size=result.get("config_size", 0),
                git_commit_id=result.get("git_commit_id"),
                error_message=error_message if not result.get("success") else None,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)
            
            if schedule and result.get("success"):
                logger.info(f"[BackupService] Updating schedule last_run_time...")
                schedule.last_run_time = datetime.now()
            
            db.commit()
            
            logger.info(f"[BackupService] Scheduled backup completed, success={result.get('success')}")
            
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "config_id": result.get("config_id"),
                "execution_time": execution_time
            }
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"[BackupService] Scheduled backup failed: {error_message}")
            
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()
            
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="failed",
                execution_time=(datetime.now() - started_at).total_seconds(),
                trigger_type="scheduled",
                error_message=error_message,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)
            db.commit()
            
            return {
                "success": False,
                "message": error_message,
                "config_id": None,
                "execution_time": (datetime.now() - started_at).total_seconds()
            }

