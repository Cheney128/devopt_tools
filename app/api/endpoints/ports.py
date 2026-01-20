"""
端口管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db
from app.models.models import Port, Device
from app.schemas.schemas import Port as PortSchema, PortCreate, PortUpdate

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[PortSchema])
def get_ports(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取端口列表
    """
    query = db.query(Port)
    
    if device_id:
        query = query.filter(Port.device_id == device_id)
    
    if status:
        query = query.filter(Port.status == status)
    
    ports = query.offset(skip).limit(limit).all()
    return ports


@router.get("/{port_id}", response_model=PortSchema)
def get_port(port_id: int, db: Session = Depends(get_db)):
    """
    获取端口详情
    """
    port = db.query(Port).filter(Port.id == port_id).first()
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Port with id {port_id} not found"
        )
    return port


@router.post("/", response_model=PortSchema, status_code=status.HTTP_201_CREATED)
def create_port(port: PortCreate, db: Session = Depends(get_db)):
    """
    创建端口
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == port.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {port.device_id} not found"
        )
    
    # 检查端口名称是否已存在
    existing_port = db.query(Port).filter(
        Port.device_id == port.device_id,
        Port.port_name == port.port_name
    ).first()
    if existing_port:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Port {port.port_name} already exists on device {port.device_id}"
        )
    
    # 创建端口
    db_port = Port(**port.model_dump())
    db.add(db_port)
    db.commit()
    db.refresh(db_port)
    return db_port


@router.put("/{port_id}", response_model=PortSchema)
def update_port(port_id: int, port: PortUpdate, db: Session = Depends(get_db)):
    """
    更新端口
    """
    db_port = db.query(Port).filter(Port.id == port_id).first()
    if not db_port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Port with id {port_id} not found"
        )
    
    # 更新端口信息
    update_data = port.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_port, field, value)
    
    db.commit()
    db.refresh(db_port)
    return db_port


@router.delete("/{port_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_port(port_id: int, db: Session = Depends(get_db)):
    """
    删除端口
    """
    db_port = db.query(Port).filter(Port.id == port_id).first()
    if not db_port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Port with id {port_id} not found"
        )
    
    db.delete(db_port)
    db.commit()
    return None


@router.post("/batch/delete", response_model=dict)
def batch_delete_ports(port_ids: List[int], db: Session = Depends(get_db)):
    """
    批量删除端口
    """
    success_count = 0
    failed_count = 0
    failed_ports = []
    
    for port_id in port_ids:
        try:
            db_port = db.query(Port).filter(Port.id == port_id).first()
            if db_port:
                db.delete(db_port)
                success_count += 1
            else:
                failed_count += 1
                failed_ports.append(f"Port {port_id} not found")
        except Exception as e:
            failed_count += 1
            failed_ports.append(f"Port {port_id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": failed_count == 0,
        "message": f"Batch delete completed: {success_count} success, {failed_count} failed",
        "total": len(port_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_ports": failed_ports if failed_ports else None
    }