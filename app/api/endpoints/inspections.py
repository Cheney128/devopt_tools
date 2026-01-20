"""
巡检管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import get_db
from app.models.models import Inspection, Device
from app.schemas.schemas import Inspection as InspectionSchema, InspectionCreate, InspectionResult

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[InspectionSchema])
def get_inspections(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    获取巡检结果列表
    """
    query = db.query(Inspection)
    
    if device_id:
        query = query.filter(Inspection.device_id == device_id)
    
    if status:
        query = query.filter(Inspection.status == status)
    
    if start_date:
        query = query.filter(Inspection.inspection_time >= start_date)
    
    if end_date:
        query = query.filter(Inspection.inspection_time <= end_date)
    
    inspections = query.order_by(Inspection.inspection_time.desc()).offset(skip).limit(limit).all()
    return inspections


@router.get("/{inspection_id}", response_model=InspectionSchema)
def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """
    获取巡检结果详情
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with id {inspection_id} not found"
        )
    return inspection


@router.post("/", response_model=InspectionSchema, status_code=status.HTTP_201_CREATED)
def create_inspection(inspection: InspectionCreate, db: Session = Depends(get_db)):
    """
    创建巡检记录
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == inspection.device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {inspection.device_id} not found"
        )
    
    # 创建巡检记录
    db_inspection = Inspection(**inspection.model_dump())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection


@router.post("/run/{device_id}", response_model=InspectionResult)
def run_inspection(device_id: int, db: Session = Depends(get_db)):
    """
    执行设备巡检
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    # 模拟巡检过程
    # 实际项目中，这里会使用Netmiko等库连接设备执行命令
    try:
        # 模拟巡检结果
        inspection_data = {
            "cpu_usage": 25.5,
            "memory_usage": 45.2,
            "interface_status": {
                "GigabitEthernet1/0/1": "up",
                "GigabitEthernet1/0/2": "up",
                "GigabitEthernet1/0/3": "down"
            },
            "error_logs": ""
        }
        
        # 保存巡检结果
        db_inspection = Inspection(
            device_id=device_id,
            cpu_usage=inspection_data["cpu_usage"],
            memory_usage=inspection_data["memory_usage"],
            interface_status=inspection_data["interface_status"],
            error_logs=inspection_data["error_logs"],
            status="completed"
        )
        db.add(db_inspection)
        db.commit()
        
        return InspectionResult(
            success=True,
            message=f"Inspection completed for device {device.hostname}",
            data=inspection_data
        )
    except Exception as e:
        return InspectionResult(
            success=False,
            message=f"Inspection failed: {str(e)}",
            data=None
        )


@router.post("/batch/run", response_model=dict)
def batch_run_inspection(device_ids: List[int], db: Session = Depends(get_db)):
    """
    批量执行巡检
    """
    success_count = 0
    failed_count = 0
    failed_devices = []
    inspection_results = []
    
    for device_id in device_ids:
        try:
            # 检查设备是否存在
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                failed_count += 1
                failed_devices.append(f"Device {device_id} not found")
                continue
            
            # 模拟巡检过程
            inspection_data = {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "interface_status": {
                    "GigabitEthernet1/0/1": "up",
                    "GigabitEthernet1/0/2": "up"
                },
                "error_logs": ""
            }
            
            # 保存巡检结果
            db_inspection = Inspection(
                device_id=device_id,
                cpu_usage=inspection_data["cpu_usage"],
                memory_usage=inspection_data["memory_usage"],
                interface_status=inspection_data["interface_status"],
                error_logs=inspection_data["error_logs"],
                status="completed"
            )
            db.add(db_inspection)
            
            success_count += 1
            inspection_results.append({
                "device_id": device_id,
                "hostname": device.hostname,
                "result": inspection_data
            })
        except Exception as e:
            failed_count += 1
            failed_devices.append(f"Device {device_id}: {str(e)}")
    
    db.commit()
    
    return {
        "success": failed_count == 0,
        "message": f"Batch inspection completed: {success_count} success, {failed_count} failed",
        "total": len(device_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_devices": failed_devices if failed_devices else None,
        "results": inspection_results if inspection_results else None
    }