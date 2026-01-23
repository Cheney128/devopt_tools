"""
配置管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models import get_db
from app.models.models import Configuration, Device, GitConfig, BackupSchedule
from app.schemas.schemas import (Configuration as ConfigurationSchema, 
                                 ConfigurationCreate, 
                                 BackupSchedule as BackupScheduleSchema,
                                 BackupScheduleCreate,
                                 BackupScheduleUpdate)
from app.services.oxidized_service import get_oxidized_service, OxidizedService
from app.services.netmiko_service import get_netmiko_service, NetmikoService
from app.services.git_service import get_git_service, GitService
from app.services.backup_scheduler import get_backup_scheduler, BackupSchedulerService

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


@router.get("/oxidized/status", response_model=Dict[str, Any])
async def get_oxidized_status(
    oxidized_service: OxidizedService = Depends(get_oxidized_service)
):
    """
    获取Oxidized服务状态
    """
    return await oxidized_service.get_oxidized_status()


@router.post("/oxidized/sync", response_model=Dict[str, Any])
async def sync_with_oxidized(
    db: Session = Depends(get_db),
    oxidized_service: OxidizedService = Depends(get_oxidized_service)
):
    """
    与Oxidized同步设备信息
    """
    return await oxidized_service.sync_with_oxidized(db)


@router.get("/oxidized/{device_id}", response_model=Dict[str, Any])
async def get_config_from_oxidized(
    device_id: int,
    db: Session = Depends(get_db),
    oxidized_service: OxidizedService = Depends(get_oxidized_service)
):
    """
    从Oxidized获取设备配置
    """
    config_content = await oxidized_service.get_device_config(device_id, db)
    if not config_content:
        return {"success": False, "message": "Failed to get config from Oxidized"}
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if device:
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content,
            version="1.0",
            change_description="Fetched from Oxidized"
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return {
            "success": True,
            "message": "Config fetched from Oxidized and saved",
            "config_id": new_config.id,
            "version": new_config.version
        }
    
    return {"success": False, "message": "Device not found"}


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
                "message": "Config has not changed",
                "config_id": latest_config.id
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