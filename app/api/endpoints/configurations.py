"""
配置管理API路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models import get_db
from app.models.models import Configuration, Device, GitConfig, BackupSchedule
from app.models.backup_task import BackupTask, BackupTaskStatus
from app.schemas.schemas import (Configuration as ConfigurationSchema, 
                                 ConfigurationCreate, 
                                 BackupSchedule as BackupScheduleSchema,
                                 BackupScheduleCreate,
                                 BackupScheduleUpdate)
from app.schemas.backup_schemas import (
    BackupFilter, BackupTaskResponse, BackupTaskDetailResponse,
    BackupTaskListResponse, CancelTaskResponse, BackupResultItem
)
from app.services.netmiko_service import get_netmiko_service, NetmikoService
from app.services.git_service import get_git_service, GitService
from app.services.backup_scheduler import get_backup_scheduler, BackupSchedulerService
from app.services.backup_executor import backup_executor

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[ConfigurationSchema])
def get_configurations(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取配置列表
    """
    query = db.query(Configuration, Device.hostname.label('device_name')).join(
        Device, Configuration.device_id == Device.id
    )
    
    if device_id:
        query = query.filter(Configuration.device_id == device_id)
    
    if start_date:
        query = query.filter(Configuration.config_time >= start_date)
    
    if end_date:
        query = query.filter(Configuration.config_time <= end_date)
    
    results = query.order_by(Configuration.config_time.desc()).offset(skip).limit(limit).all()
    
    # 转换为配置模式列表
    configurations = []
    for config, device_name in results:
        config_dict = {
            'id': config.id,
            'device_id': config.device_id,
            'device_name': device_name,
            'config_content': config.config_content,
            'config_time': config.config_time,
            'version': config.version,
            'change_description': config.change_description,
            'git_commit_id': config.git_commit_id,
            'created_at': config.created_at
        }
        configurations.append(ConfigurationSchema(**config_dict))
    
    return configurations


@router.get("/{config_id}", response_model=ConfigurationSchema)
def get_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    获取配置详情
    """
    result = db.query(Configuration, Device.hostname.label('device_name')).join(
        Device, Configuration.device_id == Device.id
    ).filter(Configuration.id == config_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with id {config_id} not found"
        )
    
    config, device_name = result
    config_dict = {
        'id': config.id,
        'device_id': config.device_id,
        'device_name': device_name,
        'config_content': config.config_content,
        'config_time': config.config_time,
        'version': config.version,
        'change_description': config.change_description,
        'git_commit_id': config.git_commit_id,
        'created_at': config.created_at
    }
    return ConfigurationSchema(**config_dict)


@router.post("/", response_model=ConfigurationSchema, status_code=status.HTTP_201_CREATED)
def create_configuration(configuration: ConfigurationCreate, db: Session = Depends(get_db)):
    """
    创建配置记录
    """
    device = db.query(Device).filter(Device.id == configuration.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {configuration.device_id} not found"
        )
    
    db_configuration = Configuration(**configuration.model_dump())
    db.add(db_configuration)
    db.commit()
    db.refresh(db_configuration)
    
    config_dict = {
        'id': db_configuration.id,
        'device_id': db_configuration.device_id,
        'device_name': device.hostname,
        'config_content': db_configuration.config_content,
        'config_time': db_configuration.config_time,
        'version': db_configuration.version,
        'change_description': db_configuration.change_description,
        'git_commit_id': db_configuration.git_commit_id,
        'created_at': db_configuration.created_at
    }
    return ConfigurationSchema(**config_dict)


@router.get("/device/{device_id}/latest", response_model=ConfigurationSchema)
def get_latest_configuration(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备最新配置
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    result = db.query(Configuration, Device.hostname.label('device_name')).join(
        Device, Configuration.device_id == Device.id
    ).filter(
        Configuration.device_id == device_id
    ).order_by(Configuration.config_time.desc()).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration found for device {device_id}"
        )
    
    config, device_name = result
    config_dict = {
        'id': config.id,
        'device_id': config.device_id,
        'device_name': device_name,
        'config_content': config.config_content,
        'config_time': config.config_time,
        'version': config.version,
        'change_description': config.change_description,
        'git_commit_id': config.git_commit_id,
        'created_at': config.created_at
    }
    return ConfigurationSchema(**config_dict)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    删除配置记录
    """
    configuration = db.query(Configuration).filter(Configuration.id == config_id).first()
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with id {config_id} not found"
        )
    
    db.delete(configuration)
    db.commit()
    return None


@router.post("/batch/delete", response_model=dict)
def batch_delete_configurations(config_ids: List[int], db: Session = Depends(get_db)):
    """
    批量删除配置记录
    """
    success_count = 0
    failed_count = 0
    failed_configs = []
    
    for config_id in config_ids:
        try:
            configuration = db.query(Configuration).filter(Configuration.id == config_id).first()
            if configuration:
                db.delete(configuration)
                success_count += 1
            else:
                failed_count += 1
                failed_configs.append(f"Configuration {config_id} not found")
        except Exception as e:
            failed_count += 1
            failed_configs.append(f"Configuration {config_id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": failed_count == 0,
        "message": f"Batch delete completed: {success_count} success, {failed_count} failed",
        "total": len(config_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_configs": failed_configs if failed_configs else None
    }


@router.post("/device/{device_id}/collect", response_model=Dict[str, Any])
async def collect_config_from_device(
    device_id: int,
    db: Session = Depends(get_db),
    netmiko_service: NetmikoService = Depends(get_netmiko_service),
    git_service: GitService = Depends(get_git_service)
):
    """
    直接从设备获取配置
    """
    try:
        # 检查设备是否存在
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"success": False, "message": "Device not found"}
        
        # 从设备获取配置
        config_content = await netmiko_service.collect_running_config(device)
        if not config_content:
            return {"success": False, "message": "Failed to get config from device"}
        
        # 获取设备最新配置
        latest_config = db.query(Configuration).filter(
            Configuration.device_id == device_id
        ).order_by(Configuration.config_time.desc()).first()
        
        # 检查配置是否有变化
        if latest_config and latest_config.config_content == config_content:
            return {
                "success": True,
                "message": "配置无变化，已成功登录并验证",
                "config_id": latest_config.id,
                "config_changed": False,
                "config_size": len(config_content) if config_content else 0
            }
        
        # 生成版本号
        new_version = "1.0"
        if latest_config:
            # 简单的版本号递增逻辑
            current_version = latest_config.version
            try:
                major, minor = map(int, current_version.split("."))
                new_version = f"{major}.{minor + 1}"
            except:
                new_version = "1.0"
        
        # 创建新的配置记录
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content,
            version=new_version,
            change_description="Auto-collected from device"
        )
        
        # 检查是否有Git配置，如果有则提交到Git（添加错误处理）
        try:
            git_config = db.query(GitConfig).filter(GitConfig.is_active == True).first()
            if git_config:
                # 为每个设备创建新的GitService实例，避免单例模式下的资源冲突
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
                        new_config.git_commit_id = commit_id
                    device_git_service.close()
        except Exception as git_error:
            print(f"Git operation error: {str(git_error)}")
            # Git操作失败不影响配置获取，继续执行
        
        # 保存到数据库
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        return {
            "success": True,
            "message": "Config collected from device and saved",
            "config_id": new_config.id,
            "version": new_config.version
        }
    except Exception as e:
        print(f"Error in collect_config_from_device: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to collect config: {str(e)}"
        }


@router.get("/diff/{config_id1}/{config_id2}", response_model=Dict[str, Any])
def get_config_diff(
    config_id1: int,
    config_id2: int,
    db: Session = Depends(get_db)
):
    """
    获取两个配置版本之间的差异
    """
    # 获取两个配置
    config1 = db.query(Configuration).filter(Configuration.id == config_id1).first()
    config2 = db.query(Configuration).filter(Configuration.id == config_id2).first()
    
    if not config1:
        return {"success": False, "message": f"Configuration {config_id1} not found"}
    
    if not config2:
        return {"success": False, "message": f"Configuration {config_id2} not found"}
    
    # 确保两个配置属于同一设备
    if config1.device_id != config2.device_id:
        return {"success": False, "message": "Configurations belong to different devices"}
    
    # 生成diff
    import difflib
    
    if not config1.config_content:
        config1.config_content = ""
    if not config2.config_content:
        config2.config_content = ""
    
    diff = difflib.unified_diff(
        config1.config_content.splitlines(),
        config2.config_content.splitlines(),
        fromfile=f"Version {config1.version} ({config1.config_time.strftime('%Y-%m-%d %H:%M:%S')})",
        tofile=f"Version {config2.version} ({config2.config_time.strftime('%Y-%m-%d %H:%M:%S')})",
        lineterm=""
    )
    
    diff_content = "\n".join(diff)
    
    return {
        "success": True,
        "diff": diff_content,
        "config1": {
            "id": config1.id,
            "version": config1.version,
            "config_time": config1.config_time
        },
        "config2": {
            "id": config2.id,
            "version": config2.version,
            "config_time": config2.config_time
        }
    }


@router.post("/{config_id}/commit-git", response_model=Dict[str, Any])
def commit_config_to_git(
    config_id: int,
    db: Session = Depends(get_db),
    git_service: GitService = Depends(get_git_service)
):
    """
    手动将配置提交到Git仓库
    """
    try:
        # 获取配置和设备信息
        result = db.query(Configuration, Device).join(
            Device, Configuration.device_id == Device.id
        ).filter(Configuration.id == config_id).first()
        
        if not result:
            return {"success": False, "message": "Configuration not found"}
        
        config, device = result
        
        # 检查是否已经提交到Git
        if config.git_commit_id:
            return {"success": False, "message": "Configuration already committed to Git"}
        
        # 获取活跃的Git配置
        git_config = db.query(GitConfig).filter(GitConfig.is_active == True).first()
        if not git_config:
            return {"success": False, "message": "No active Git configuration found"}
        
        # 执行Git操作
        if git_service.init_repo(git_config):
            commit_id = git_service.commit_config(
                device.hostname,
                config.config_content,
                f"Manual commit for {device.hostname} at {datetime.now()}"
            )
            if commit_id:
                if git_service.push_to_remote():
                    # 更新配置记录的git_commit_id
                    config.git_commit_id = commit_id
                    db.commit()
                    git_service.close()
                    return {
                        "success": True,
                        "message": "Config successfully committed to Git",
                        "commit_id": commit_id
                    }
                else:
                    git_service.close()
                    return {"success": False, "message": "Failed to push to Git remote"}
            else:
                git_service.close()
                return {"success": False, "message": "Failed to commit to Git"}
        else:
            return {"success": False, "message": "Failed to initialize Git repo"}
    except Exception as e:
        print(f"Git commit error: {str(e)}")
        return {"success": False, "message": f"Git operation failed: {str(e)}"}


@router.post("/backup-schedules", response_model=Dict[str, Any])
async def create_backup_schedule(
    schedule: BackupScheduleCreate,
    db: Session = Depends(get_db),
    backup_scheduler: BackupSchedulerService = Depends(get_backup_scheduler),
    netmiko_service: NetmikoService = Depends(get_netmiko_service),
    git_service: GitService = Depends(get_git_service)
):
    """
    创建备份任务
    """
    try:
        # 检查设备是否存在
        device = db.query(Device).filter(Device.id == schedule.device_id).first()
        if not device:
            return {"success": False, "message": "Device not found"}
        
        # 创建备份任务
        db_schedule = BackupSchedule(**schedule.model_dump())
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        # 立即执行一次备份
        backup_result = await collect_config_from_device(
            schedule.device_id, db, netmiko_service, git_service
        )
        
        # 备份完成后，将任务添加到调度器
        if db_schedule.is_active:
            backup_scheduler.add_schedule(db_schedule, db)
        
        # 返回结果，包含备份结果
        return {
            "success": True,
            "message": "Backup schedule created successfully and initial backup completed",
            "schedule_id": db_schedule.id,
            "backup_result": backup_result
        }
    except Exception as e:
        print(f"Create backup schedule error: {str(e)}")
        return {"success": False, "message": f"Failed to create backup schedule: {str(e)}"}


@router.get("/backup-schedules", response_model=List[BackupScheduleSchema])
def get_backup_schedules(
    device_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取备份任务列表
    """
    query = db.query(BackupSchedule, Device.hostname.label('device_name')).join(
        Device, BackupSchedule.device_id == Device.id
    )
    
    if device_id:
        query = query.filter(BackupSchedule.device_id == device_id)
    
    if is_active is not None:
        query = query.filter(BackupSchedule.is_active == is_active)
    
    results = query.order_by(BackupSchedule.created_at.desc()).all()
    
    # 转换为备份任务模式列表
    schedules = []
    for schedule, device_name in results:
        schedule_dict = {
            'id': schedule.id,
            'device_id': schedule.device_id,
            'device_name': device_name,
            'schedule_type': schedule.schedule_type,
            'time': schedule.time,
            'day': schedule.day,
            'is_active': schedule.is_active,
            'created_at': schedule.created_at,
            'updated_at': schedule.updated_at
        }
        schedules.append(BackupScheduleSchema(**schedule_dict))
    
    return schedules


@router.get("/backup-schedules/{schedule_id}", response_model=BackupScheduleSchema)
def get_backup_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个备份任务详情
    """
    result = db.query(BackupSchedule, Device.hostname.label('device_name')).join(
        Device, BackupSchedule.device_id == Device.id
    ).filter(BackupSchedule.id == schedule_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup schedule {schedule_id} not found"
        )
    
    schedule, device_name = result
    schedule_dict = {
        'id': schedule.id,
        'device_id': schedule.device_id,
        'device_name': device_name,
        'schedule_type': schedule.schedule_type,
        'time': schedule.time,
        'day': schedule.day,
        'is_active': schedule.is_active,
        'created_at': schedule.created_at,
        'updated_at': schedule.updated_at
    }
    
    return BackupScheduleSchema(**schedule_dict)


@router.put("/backup-schedules/{schedule_id}", response_model=Dict[str, Any])
def update_backup_schedule(
    schedule_id: int,
    schedule_update: BackupScheduleUpdate,
    db: Session = Depends(get_db),
    backup_scheduler: BackupSchedulerService = Depends(get_backup_scheduler)
):
    """
    更新备份任务
    """
    try:
        db_schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
        if not db_schedule:
            return {"success": False, "message": "Backup schedule not found"}
        
        # 更新字段
        update_data = schedule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)
        
        db.commit()
        db.refresh(db_schedule)
        
        # 更新调度器
        backup_scheduler.update_schedule(db_schedule, db)
        
        return {
            "success": True,
            "message": "Backup schedule updated successfully"
        }
    except Exception as e:
        print(f"Update backup schedule error: {str(e)}")
        return {"success": False, "message": f"Failed to update backup schedule: {str(e)}"}


@router.delete("/backup-schedules/{schedule_id}", response_model=Dict[str, Any])
def delete_backup_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    backup_scheduler: BackupSchedulerService = Depends(get_backup_scheduler)
):
    """
    删除备份任务
    """
    try:
        db_schedule = db.query(BackupSchedule).filter(BackupSchedule.id == schedule_id).first()
        if not db_schedule:
            return {"success": False, "message": "Backup schedule not found"}
        
        # 从调度器中移除
        backup_scheduler.remove_schedule(schedule_id)
        
        db.delete(db_schedule)
        db.commit()
        
        return {
            "success": True,
            "message": "Backup schedule deleted successfully"
        }
    except Exception as e:
        print(f"Delete backup schedule error: {str(e)}")
        return {"success": False, "message": f"Failed to delete backup schedule: {str(e)}"}


@router.post("/backup-schedules/batch", response_model=dict)
async def batch_create_backup_schedules(
    request: dict,
    db: Session = Depends(get_db),
    backup_scheduler: BackupSchedulerService = Depends(get_backup_scheduler),
    netmiko_service: NetmikoService = Depends(get_netmiko_service),
    git_service: GitService = Depends(get_git_service)
):
    """
    批量创建备份任务
    """
    import asyncio
    
    try:
        device_ids = request.get("device_ids", [])
        if not device_ids:
            return {"success": False, "message": "No device ids provided"}
        
        backup_config = {
            "schedule_type": request.get("schedule_type", "daily"),
            "time": request.get("time"),
            "day": request.get("day", 1),
            "is_active": request.get("is_active", True)
        }
        
        # 先创建所有备份任务记录
        created_schedules = []
        invalid_devices = []
        
        for device_id in device_ids:
            try:
                # 检查设备是否存在
                device = db.query(Device).filter(Device.id == device_id).first()
                if not device:
                    invalid_devices.append(f"Device {device_id}: not found")
                    continue
                
                # 创建备份任务记录
                db_schedule = BackupSchedule(
                    device_id=device_id,
                    schedule_type=backup_config["schedule_type"],
                    time=backup_config["time"],
                    day=backup_config["day"],
                    is_active=backup_config["is_active"]
                )
                db.add(db_schedule)
                db.commit()
                db.refresh(db_schedule)
                
                created_schedules.append(db_schedule)
            except Exception as e:
                invalid_devices.append(f"Device {device_id}: {str(e)}")
        
        # 并发执行所有设备的备份任务
        async def backup_device(device_id):
            try:
                result = await collect_config_from_device(
                    device_id, db, netmiko_service, git_service
                )
                return {"device_id": device_id, "success": result["success"], "message": result["message"]}
            except Exception as e:
                return {"device_id": device_id, "success": False, "message": str(e)}
        
        # 使用asyncio.gather并发执行，return_exceptions=True确保单个设备失败不影响整体
        backup_results = await asyncio.gather(
            *[backup_device(schedule.device_id) for schedule in created_schedules],
            return_exceptions=True
        )
        
        # 处理备份结果
        backup_success_count = 0
        backup_failed_count = 0
        backup_failed_devices = []
        
        for i, result in enumerate(backup_results):
            schedule = created_schedules[i]
            if isinstance(result, Exception):
                # 处理asyncio.gather返回的异常
                backup_failed_count += 1
                backup_failed_devices.append(f"Device {schedule.device_id}: {str(result)}")
            else:
                if result["success"]:
                    backup_success_count += 1
                else:
                    backup_failed_count += 1
                    backup_failed_devices.append(f"Device {result['device_id']}: {result['message']}")
            
            # 无论备份成功与否，都将任务添加到调度器
            if schedule.is_active:
                backup_scheduler.add_schedule(schedule, db)
        
        # 计算整体结果
        total = len(device_ids)
        schedule_success_count = len(created_schedules)
        schedule_failed_count = len(invalid_devices)
        
        return {
            "success": schedule_failed_count == 0,
            "message": f"Batch create completed: {schedule_success_count} schedules created, {backup_success_count} backups succeeded, {backup_failed_count} backups failed",
            "total": total,
            "schedule_success_count": schedule_success_count,
            "schedule_failed_count": schedule_failed_count,
            "backup_success_count": backup_success_count,
            "backup_failed_count": backup_failed_count,
            "invalid_devices": invalid_devices if invalid_devices else None,
            "backup_failed_devices": backup_failed_devices if backup_failed_devices else None
        }
    except Exception as e:
        print(f"Batch create backup schedules error: {str(e)}")
        return {"success": False, "message": f"Failed to create batch backup schedules: {str(e)}"}


@router.post("/device/{device_id}/backup-now", response_model=Dict[str, Any])
async def backup_now(
    device_id: int,
    db: Session = Depends(get_db),
    netmiko_service: NetmikoService = Depends(get_netmiko_service),
    git_service: GitService = Depends(get_git_service)
):
    """
    立即执行设备备份
    """
    try:
        # 直接调用现有的collect_config_from_device函数执行备份
        result = await collect_config_from_device(device_id, db, netmiko_service, git_service)
        return result
    except Exception as e:
        print(f"Backup now error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to execute backup: {str(e)}"
        }


def get_backup_task_db(task_id: str, db: Session) -> Optional[BackupTask]:
    """从数据库获取备份任务"""
    return db.query(BackupTask).filter(BackupTask.task_id == task_id).first()


@router.post("/backup-all", response_model=BackupTaskResponse)
async def backup_all_devices(
    filter_params: BackupFilter,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None)
):
    """
    备份所有设备或符合条件的设备
    - 异步执行：立即返回任务ID，后台执行备份
    - 同步执行：等待所有设备备份完成返回结果
    - 支持并发控制和失败重试
    - 支持幂等性保护（通过Idempotency-Key请求头）
    """
    if idempotency_key:
        existing_task = db.query(BackupTask).filter(
            BackupTask.idempotency_key == idempotency_key
        ).first()
        if existing_task:
            return {
                "task_id": existing_task.task_id,
                "status": existing_task.status.value if hasattr(existing_task.status, 'value') else existing_task.status,
                "total": existing_task.total,
                "completed": existing_task.completed,
                "success_count": existing_task.success_count,
                "failed_count": existing_task.failed_count,
                "message": "重复请求，返回已存在的任务",
                "progress_percentage": existing_task.progress_percentage if hasattr(existing_task, 'progress_percentage') else 0.0
            }
    
    query = db.query(Device)
    
    if filter_params.filter_status:
        query = query.filter(Device.status == filter_params.filter_status)
    
    if filter_params.filter_vendor:
        query = query.filter(Device.vendor == filter_params.filter_vendor)
    
    devices = query.all()
    total = len(devices)
    
    if total == 0:
        return {
            "task_id": str(uuid.uuid4()),
            "status": BackupTaskStatus.COMPLETED.value if hasattr(BackupTaskStatus.COMPLETED, 'value') else BackupTaskStatus.COMPLETED,
            "total": 0,
            "completed": 0,
            "success_count": 0,
            "failed_count": 0,
            "message": "没有符合条件的设备",
            "progress_percentage": 100.0
        }
    
    task = BackupTask(
        idempotency_key=idempotency_key,
        total=total,
        filters={
            "filter_status": filter_params.filter_status,
            "filter_vendor": filter_params.filter_vendor
        },
        max_concurrent=filter_params.max_concurrent,
        timeout=filter_params.timeout,
        retry_count=filter_params.retry_count,
        notify_on_complete=1 if filter_params.notify_on_complete else 0,
        priority=filter_params.priority.value if hasattr(filter_params.priority, 'value') else filter_params.priority
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    if filter_params.async_execute:
        background_tasks.add_task(
            _execute_backup_task_async,
            task.task_id,
            [d.id for d in devices],
            filter_params
        )
        
        return {
            "task_id": task.task_id,
            "status": BackupTaskStatus.PENDING.value if hasattr(BackupTaskStatus.PENDING, 'value') else BackupTaskStatus.PENDING,
            "total": total,
            "completed": 0,
            "success_count": 0,
            "failed_count": 0,
            "message": f"已启动批量备份任务，共 {total} 个设备",
            "progress_percentage": 0.0
        }
    else:
        results = await _execute_backup_task_sync(
            task.task_id,
            [d.id for d in devices],
            filter_params,
            db
        )
        
        return {
            "task_id": task.task_id,
            "status": task.status.value if hasattr(task.status, 'value') else task.status,
            "total": total,
            "completed": task.completed,
            "success_count": task.success_count,
            "failed_count": task.failed_count,
            "message": f"备份完成，成功 {task.success_count} 个，失败 {task.failed_count} 个",
            "progress_percentage": task.progress_percentage if hasattr(task, 'progress_percentage') else 0.0
        }


async def _execute_backup_task_async(
    task_id: str,
    device_ids: List[int],
    filter_params: BackupFilter
):
    """异步执行备份任务"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    executor = None
    try:
        executor = BackupExecutor(
            max_concurrent=filter_params.max_concurrent,
            timeout=filter_params.timeout
        )
        await executor.execute_backup_all(
            task_id=task_id,
            device_ids=device_ids,
            db=db,
            retry_count=filter_params.retry_count
        )
    except Exception as e:
        logger.error(f"备份任务执行失败: {task_id}, 错误: {str(e)}")
        task = get_backup_task_db(task_id, db)
        if task:
            task.status = BackupTaskStatus.FAILED
            task.error_details = {"error": str(e), "phase": "async_execution"}
            task.completed_at = datetime.now()
            db.commit()
    finally:
        if executor:
            await executor.cleanup()
        db.close()


async def _execute_backup_task_sync(
    task_id: str,
    device_ids: List[int],
    filter_params: BackupFilter,
    db: Session
):
    """同步执行备份任务"""
    executor = BackupExecutor(
        max_concurrent=filter_params.max_concurrent,
        timeout=filter_params.timeout
    )
    return await executor.execute_backup_all(
        task_id=task_id,
        device_ids=device_ids,
        db=db,
        retry_count=filter_params.retry_count
    )


@router.get("/backup-tasks", response_model=BackupTaskListResponse)
async def list_backup_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取备份任务列表"""
    query = db.query(BackupTask)
    
    if status:
        query = query.filter(BackupTask.status == status)
    
    total = query.count()
    tasks = query.order_by(BackupTask.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return {
        "tasks": [{
            "task_id": task.task_id,
            "status": task.status.value if hasattr(task.status, 'value') else task.status,
            "total": task.total,
            "completed": task.completed,
            "success_count": task.success_count,
            "failed_count": task.failed_count,
            "message": "",
            "progress_percentage": 0.0
        } for task in tasks],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/backup-tasks/{task_id}", response_model=Dict[str, Any])
async def get_backup_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取备份任务状态和详情"""
    task = get_backup_task_db(task_id, db)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "status": task.status.value if hasattr(task.status, 'value') else task.status,
        "total": task.total,
        "completed": task.completed,
        "success_count": task.success_count,
        "failed_count": task.failed_count,
        "message": "",
        "filters": task.filters,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "error_details": task.error_details,
        "progress_percentage": 0.0
    }


@router.post("/backup-tasks/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_backup_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """取消备份任务"""
    task = get_backup_task_db(task_id, db)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    current_status = task.status.value if hasattr(task.status, 'value') else task.status
    
    if current_status == BackupTaskStatus.COMPLETED.value if hasattr(BackupTaskStatus.COMPLETED, 'value') else BackupTaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务已完成，无法取消")
    
    if current_status == BackupTaskStatus.CANCELLED.value if hasattr(BackupTaskStatus.CANCELLED, 'value') else BackupTaskStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="任务已取消")
    
    task.status = BackupTaskStatus.CANCELLED
    task.completed_at = datetime.now()
    db.commit()
    
    backup_executor.cancel_task(task_id)
    
    return {"message": "任务已取消", "task_id": task_id}


# ==================== 监控统计API ====================

@router.get("/monitoring/statistics", response_model=Dict[str, Any])
async def get_backup_statistics(
    db: Session = Depends(get_db)
):
    """获取备份统计信息"""
    from sqlalchemy import func
    from app.models.models import BackupExecutionLog, BackupSchedule, Device
    
    total_devices = db.query(func.count(Device.id)).scalar() or 0
    total_schedules = db.query(func.count(BackupSchedule.id)).scalar() or 0
    active_schedules = db.query(func.count(BackupSchedule.id)).filter(
        BackupSchedule.is_active == True
    ).scalar() or 0
    
    total_executions = db.query(func.count(BackupExecutionLog.id)).scalar() or 0
    successful_executions = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.status == "success"
    ).scalar() or 0
    failed_executions = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.status == "failed"
    ).scalar() or 0
    
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
    
    avg_time = db.query(func.avg(BackupExecutionLog.execution_time)).filter(
        BackupExecutionLog.execution_time.isnot(None)
    ).scalar() or 0
    
    last_execution = db.query(func.max(BackupExecutionLog.created_at)).scalar()
    
    return {
        "total_devices": total_devices,
        "total_schedules": total_schedules,
        "active_schedules": active_schedules,
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "success_rate": round(success_rate, 2),
        "average_execution_time": round(avg_time, 2),
        "last_execution_time": last_execution
    }


@router.get("/monitoring/dashboard", response_model=Dict[str, Any])
async def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    """获取仪表盘摘要"""
    from sqlalchemy import func
    from app.models.models import BackupExecutionLog, BackupSchedule, Device
    from datetime import datetime, timedelta
    
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats_response = await get_backup_statistics(db)
    
    failed_today = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.status == "failed",
        BackupExecutionLog.created_at >= today_start
    ).scalar() or 0
    
    scheduled_today = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.trigger_type == "scheduled",
        BackupExecutionLog.created_at >= today_start
    ).scalar() or 0
    
    devices_backup_today = db.query(func.count(func.distinct(BackupExecutionLog.device_id))).filter(
        BackupExecutionLog.created_at >= today_start
    ).scalar() or 0
    
    recent_logs = db.query(BackupExecutionLog).order_by(
        BackupExecutionLog.created_at.desc()
    ).limit(10).all()
    
    recent_executions = []
    for log in recent_logs:
        device = db.query(Device).filter(Device.id == log.device_id).first()
        recent_executions.append({
            "id": log.id,
            "task_id": log.task_id,
            "device_id": log.device_id,
            "device_name": device.hostname if device else None,
            "schedule_id": log.schedule_id,
            "status": log.status,
            "execution_time": log.execution_time,
            "trigger_type": log.trigger_type,
            "config_id": log.config_id,
            "error_message": log.error_message,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "created_at": log.created_at
        })
    
    return {
        "statistics": stats_response,
        "recent_executions": recent_executions,
        "failed_today": failed_today,
        "scheduled_today": scheduled_today,
        "devices_backup_today": devices_backup_today
    }


@router.get("/monitoring/execution-logs", response_model=List[Dict[str, Any]])
async def get_execution_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    trigger_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """获取执行日志列表"""
    from app.models.models import BackupExecutionLog, Device
    from sqlalchemy import func
    
    query = db.query(BackupExecutionLog)
    
    if status:
        query = query.filter(BackupExecutionLog.status == status)
    
    if device_id:
        query = query.filter(BackupExecutionLog.device_id == device_id)
    
    if trigger_type:
        query = query.filter(BackupExecutionLog.trigger_type == trigger_type)
    
    if start_date:
        query = query.filter(BackupExecutionLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(BackupExecutionLog.created_at <= end_date)
    
    total = query.count()
    
    logs = query.order_by(BackupExecutionLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    result = []
    for log in logs:
        device = db.query(Device).filter(Device.id == log.device_id).first()
        result.append({
            "id": log.id,
            "task_id": log.task_id,
            "device_id": log.device_id,
            "device_name": device.hostname if device else None,
            "schedule_id": log.schedule_id,
            "status": log.status,
            "execution_time": log.execution_time,
            "trigger_type": log.trigger_type,
            "config_id": log.config_id,
            "error_message": log.error_message,
            "error_details": log.error_details,
            "config_size": log.config_size,
            "git_commit_id": log.git_commit_id,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "created_at": log.created_at
        })
    
    return {
        "logs": result,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/monitoring/trends", response_model=List[Dict[str, Any]])
async def get_backup_trends(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """获取备份趋势数据"""
    from sqlalchemy import func
    from app.models.models import BackupExecutionLog
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    logs = db.query(
        func.date(BackupExecutionLog.created_at).label('date'),
        func.count(BackupExecutionLog.id).label('total'),
        func.sum(func.IF(BackupExecutionLog.status == 'success', 1, 0)).label('success'),
        func.sum(func.IF(BackupExecutionLog.status == 'failed', 1, 0)).label('failed')
    ).filter(
        BackupExecutionLog.created_at >= start_date
    ).group_by(
        func.date(BackupExecutionLog.created_at)
    ).order_by('date').all()
    
    result = []
    for log in logs:
        total = log.total or 0
        success = log.success or 0
        success_rate = (success / total * 100) if total > 0 else 0
        result.append({
            "date": str(log.date),
            "total": total,
            "success": success,
            "failed": log.failed or 0,
            "success_rate": round(success_rate, 2)
        })
    
    return result


@router.get("/monitoring/devices/statistics", response_model=List[Dict[str, Any]])
async def get_device_backup_statistics(
    db: Session = Depends(get_db)
):
    """获取设备备份统计"""
    from sqlalchemy import func
    from app.models.models import BackupExecutionLog, Device
    
    devices = db.query(Device).all()
    result = []
    
    for device in devices:
        stats = db.query(
            func.count(BackupExecutionLog.id).label('total'),
            func.sum(func.IF(BackupExecutionLog.status == 'success', 1, 0)).label('success'),
            func.sum(func.IF(BackupExecutionLog.status == 'failed', 1, 0)).label('failed'),
            func.max(BackupExecutionLog.created_at).label('last_backup'),
            func.avg(BackupExecutionLog.execution_time).label('avg_time')
        ).filter(
            BackupExecutionLog.device_id == device.id
        ).first()
        
        total = stats.total or 0
        success = stats.success or 0
        success_rate = (success / total * 100) if total > 0 else 0
        
        result.append({
            "device_id": device.id,
            "device_name": device.hostname,
            "total_backups": total,
            "successful_backups": success,
            "failed_backups": stats.failed or 0,
            "success_rate": round(success_rate, 2),
            "last_backup_time": stats.last_backup,
            "average_execution_time": round(stats.avg_time or 0, 2)
        })
    
    return result