"""
配置管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models import get_db
from app.models.models import Configuration, Device
from app.schemas.schemas import Configuration as ConfigurationSchema, ConfigurationCreate
from app.services.oxidized_service import get_oxidized_service, OxidizedService

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
    query = db.query(Configuration)
    
    if device_id:
        query = query.filter(Configuration.device_id == device_id)
    
    if start_date:
        query = query.filter(Configuration.config_time >= start_date)
    
    if end_date:
        query = query.filter(Configuration.config_time <= end_date)
    
    configurations = query.order_by(Configuration.config_time.desc()).offset(skip).limit(limit).all()
    return configurations


@router.get("/{config_id}", response_model=ConfigurationSchema)
def get_configuration(config_id: int, db: Session = Depends(get_db)):
    """
    获取配置详情
    """
    configuration = db.query(Configuration).filter(Configuration.id == config_id).first()
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration with id {config_id} not found"
        )
    return configuration


@router.post("/", response_model=ConfigurationSchema, status_code=status.HTTP_201_CREATED)
def create_configuration(configuration: ConfigurationCreate, db: Session = Depends(get_db)):
    """
    创建配置记录
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == configuration.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {configuration.device_id} not found"
        )
    
    # 创建配置记录
    db_configuration = Configuration(**configuration.model_dump())
    db.add(db_configuration)
    db.commit()
    db.refresh(db_configuration)
    return db_configuration


@router.get("/device/{device_id}/latest", response_model=ConfigurationSchema)
def get_latest_configuration(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备最新配置
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 获取最新配置
    configuration = db.query(Configuration).filter(
        Configuration.device_id == device_id
    ).order_by(Configuration.config_time.desc()).first()
    
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No configuration found for device {device_id}"
        )
    
    return configuration


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
    
    # 保存配置到数据库
    device = db.query(Device).filter(Device.id == device_id).first()
    if device:
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content
        )
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return {
            "success": True,
            "message": "Config fetched from Oxidized and saved",
            "config_id": new_config.id
        }
    
    return {"success": False, "message": "Device not found"}