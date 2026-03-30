# -*- coding: utf-8 -*-
"""
ARP 表采集 API 路由

提供 ARP 表采集功能，采集结果写入 arp_current 表。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models import get_db
from app.models.models import Device
from app.models.ip_location_current import ARPEntry
from app.services.netmiko_service import netmiko_service
from app.schemas.schemas import DeviceCollectionResult

# 创建路由器
router = APIRouter(prefix="/api/arp-collection", tags=["ARP 采集"])


@router.post("/{device_id}/collect", response_model=DeviceCollectionResult)
async def collect_arp_table(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集单个设备的 ARP 表
    
    Args:
        device_id: 设备 ID
        db: 数据库会话
        
    Returns:
        采集结果
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    try:
        # 采集 ARP 表
        arp_table = await netmiko_service.collect_arp_table(device)
        
        if not arp_table:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect ARP table for device {device.hostname}",
                data=None
            )
        
        # 清空现有 ARP 数据（当前设备）
        db.query(ARPEntry).filter(ARPEntry.device_id == device_id).delete()
        
        # 保存新的 ARP 数据
        for arp_entry in arp_table:
            entry = ARPEntry(
                ip_address=arp_entry['ip_address'],
                mac_address=arp_entry['mac_address'],
                arp_device_id=device_id,
                vlan_id=arp_entry.get('vlan_id'),
                arp_interface=arp_entry.get('interface'),
                last_seen=datetime.now(),
                collection_batch_id=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            )
            db.add(entry)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"ARP table collected successfully for device {device.hostname}",
            data={"arp_entries_count": len(arp_table)}
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting ARP table: {str(e)}",
            data=None
        )


@router.post("/batch/collect", response_model=DeviceCollectionResult)
async def batch_collect_arp(
    device_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    批量采集 ARP 表
    
    Args:
        device_ids: 设备 ID 列表
        db: 数据库会话
        
    Returns:
        批量采集结果
    """
    # 获取设备列表
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
    
    if not devices:
        return DeviceCollectionResult(
            success=False,
            message="No valid devices found",
            data=None
        )
    
    try:
        # 批量采集
        results = await netmiko_service.batch_collect_arp_table(devices)
        
        # 处理采集结果并保存到数据库
        total_entries = 0
        for detail in results['details']:
            if detail['success'] and 'arp_table' in detail['data']:
                device_id = detail['device_id']
                arp_table = detail['data']['arp_table']
                
                # 清空现有 ARP 数据
                db.query(ARPEntry).filter(ARPEntry.device_id == device_id).delete()
                
                # 保存新的 ARP 数据
                for arp_entry in arp_table:
                    entry = ARPEntry(
                        ip_address=arp_entry['ip_address'],
                        mac_address=arp_entry['mac_address'],
                        arp_device_id=device_id,
                        vlan_id=arp_entry.get('vlan_id'),
                        arp_interface=arp_entry.get('interface'),
                        last_seen=datetime.now(),
                        collection_batch_id=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    )
                    db.add(entry)
                
                total_entries += len(arp_table)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Batch ARP collection completed: {results['success']} success, {results['failed']} failed",
            data={
                "total_arp_entries": total_entries,
                "details": results['details']
            }
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error in batch ARP collection: {str(e)}",
            data=None
        )
