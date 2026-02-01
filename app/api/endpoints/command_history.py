"""
命令执行历史API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import get_db
from app.models.models import CommandHistory, Device
from app.schemas.schemas import CommandHistory as CommandHistorySchema

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[CommandHistorySchema])
def get_command_history(
    page: int = 1,
    page_size: int = 10,
    device_id: Optional[int] = None,
    success: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取命令执行历史列表
    """
    # 转换page和page_size为skip和limit
    skip = (page - 1) * page_size
    limit = page_size
    
    query = db.query(CommandHistory)
    
    if device_id:
        query = query.filter(CommandHistory.device_id == device_id)
    
    if success is not None:
        query = query.filter(CommandHistory.success == success)
    
    if start_time:
        query = query.filter(CommandHistory.execution_time >= start_time)
    
    if end_time:
        query = query.filter(CommandHistory.execution_time <= end_time)
    
    # 默认按执行时间倒序
    query = query.order_by(CommandHistory.execution_time.desc())
    
    # 获取总记录数
    total = query.count()
    # 获取分页数据
    history = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "history": history,
        "page": page,
        "page_size": page_size
    }


@router.get("/{history_id}", response_model=CommandHistorySchema)
def get_command_history_detail(
    history_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个命令执行历史详情
    """
    history = db.query(CommandHistory).filter(CommandHistory.id == history_id).first()
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command history with id {history_id} not found"
        )
    return history


@router.get("/device/{device_id}", response_model=List[CommandHistorySchema])
def get_device_command_history(
    device_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """
    获取特定设备的命令执行历史
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 转换page和page_size为skip和limit
    skip = (page - 1) * page_size
    limit = page_size
    
    query = db.query(CommandHistory).filter(CommandHistory.device_id == device_id)
    query = query.order_by(CommandHistory.execution_time.desc())
    
    # 获取总记录数
    total = query.count()
    # 获取分页数据
    history = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "history": history,
        "page": page,
        "page_size": page_size
    }


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_command_history(
    history_id: int,
    db: Session = Depends(get_db)
):
    """
    删除命令执行历史记录
    """
    history = db.query(CommandHistory).filter(CommandHistory.id == history_id).first()
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command history with id {history_id} not found"
        )
    
    db.delete(history)
    db.commit()
    return None


@router.delete("/device/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_command_history(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    删除特定设备的所有命令执行历史记录
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 删除该设备的所有命令历史
    db.query(CommandHistory).filter(CommandHistory.device_id == device_id).delete()
    db.commit()
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_old_command_history(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    删除指定天数之前的命令执行历史记录
    """
    # 计算截止时间
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 删除截止时间之前的所有命令历史
    db.query(CommandHistory).filter(CommandHistory.execution_time < cutoff_date).delete()
    db.commit()
    return None
