"""
VLAN管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db
from app.models.models import VLAN, Device
from app.schemas.schemas import VLAN as VLANSchema, VLANCreate, VLANUpdate

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[VLANSchema])
def get_vlans(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取VLAN列表
    """
    query = db.query(VLAN)
    
    if device_id:
        query = query.filter(VLAN.device_id == device_id)
    
    vlans = query.offset(skip).limit(limit).all()
    return vlans


@router.get("/{vlan_id}", response_model=VLANSchema)
def get_vlan(vlan_id: int, db: Session = Depends(get_db)):
    """
    获取VLAN详情
    """
    vlan = db.query(VLAN).filter(VLAN.id == vlan_id).first()
    if not vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN with id {vlan_id} not found"
        )
    return vlan


@router.post("/", response_model=VLANSchema, status_code=status.HTTP_201_CREATED)
def create_vlan(vlan: VLANCreate, db: Session = Depends(get_db)):
    """
    创建VLAN
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == vlan.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {vlan.device_id} not found"
        )
    
    # 创建VLAN
    db_vlan = VLAN(**vlan.model_dump())
    db.add(db_vlan)
    db.commit()
    db.refresh(db_vlan)
    return db_vlan


@router.put("/{vlan_id}", response_model=VLANSchema)
def update_vlan(vlan_id: int, vlan: VLANUpdate, db: Session = Depends(get_db)):
    """
    更新VLAN
    """
    db_vlan = db.query(VLAN).filter(VLAN.id == vlan_id).first()
    if not db_vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN with id {vlan_id} not found"
        )
    
    # 更新VLAN信息
    update_data = vlan.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vlan, field, value)
    
    db.commit()
    db.refresh(db_vlan)
    return db_vlan


@router.delete("/{vlan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vlan(vlan_id: int, db: Session = Depends(get_db)):
    """
    删除VLAN
    """
    db_vlan = db.query(VLAN).filter(VLAN.id == vlan_id).first()
    if not db_vlan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VLAN with id {vlan_id} not found"
        )
    
    db.delete(db_vlan)
    db.commit()
    return None


@router.post("/batch/delete", response_model=dict)
def batch_delete_vlans(vlan_ids: List[int], db: Session = Depends(get_db)):
    """
    批量删除VLAN
    """
    success_count = 0
    failed_count = 0
    failed_vlans = []
    
    for vlan_id in vlan_ids:
        try:
            db_vlan = db.query(VLAN).filter(VLAN.id == vlan_id).first()
            if db_vlan:
                db.delete(db_vlan)
                success_count += 1
            else:
                failed_count += 1
                failed_vlans.append(f"VLAN {vlan_id} not found")
        except Exception as e:
            failed_count += 1
            failed_vlans.append(f"VLAN {vlan_id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": failed_count == 0,
        "message": f"Batch delete completed: {success_count} success, {failed_count} failed",
        "total": len(vlan_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_vlans": failed_vlans if failed_vlans else None
    }