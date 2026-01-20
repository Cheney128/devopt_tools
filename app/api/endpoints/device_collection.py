"""
设备信息采集API路由
提供基于Netmiko的设备信息采集功能
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db
from app.models.models import Device, DeviceVersion, Port, MACAddress
from app.services.netmiko_service import netmiko_service, get_netmiko_service
from app.schemas.schemas import (
    DeviceCollectionResult, 
    DeviceCollectionRequest,
    MACAddress as MACAddressSchema,
    DeviceVersion as DeviceVersionSchema
)


# 创建路由器
router = APIRouter()


@router.post("/{device_id}/collect/version", response_model=DeviceCollectionResult)
async def collect_device_version(
    device_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    采集设备版本信息
    
    Args:
        device_id: 设备ID
        background_tasks: 后台任务
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
        # 采集版本信息
        version_info = await netmiko_service.collect_device_version(device)
        
        if not version_info:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect version info for device {device.hostname}",
                data=None
            )
        
        # 更新设备表中的版本信息
        if version_info.get('software_version'):
            device.os_version = version_info['software_version']
            db.commit()
        
        # 保存到版本信息表
        device_version = DeviceVersion(**version_info)
        db.add(device_version)
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Version info collected successfully for device {device.hostname}",
            data=version_info
        )
        
    except Exception as e:
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting version info: {str(e)}",
            data=None
        )


@router.post("/{device_id}/collect/serial", response_model=DeviceCollectionResult)
async def collect_device_serial(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集设备序列号
    
    Args:
        device_id: 设备ID
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
        # 采集序列号
        serial = await netmiko_service.collect_device_serial(device)
        
        if not serial:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect serial number for device {device.hostname}",
                data=None
            )
        
        # 更新设备表中的序列号
        device.sn = serial
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Serial number collected successfully for device {device.hostname}",
            data={"serial": serial}
        )
        
    except Exception as e:
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting serial number: {str(e)}",
            data=None
        )


@router.post("/{device_id}/collect/interfaces", response_model=DeviceCollectionResult)
async def collect_interfaces_info(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集接口信息
    
    Args:
        device_id: 设备ID
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
        # 采集接口信息
        interfaces_info = await netmiko_service.collect_interfaces_info(device)
        
        if not interfaces_info:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect interfaces info for device {device.hostname}",
                data=None
            )
        
        # 清空现有接口信息
        db.query(Port).filter(Port.device_id == device_id).delete()
        
        # 保存新的接口信息
        for interface_info in interfaces_info:
            port = Port(**interface_info)
            db.add(port)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Interfaces info collected successfully for device {device.hostname}",
            data={"interfaces_count": len(interfaces_info)}
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting interfaces info: {str(e)}",
            data=None
        )


@router.post("/{device_id}/collect/mac-table", response_model=DeviceCollectionResult)
async def collect_mac_table(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    采集MAC地址表
    
    Args:
        device_id: 设备ID
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
        # 采集MAC地址表
        mac_table = await netmiko_service.collect_mac_table(device)
        
        if not mac_table:
            return DeviceCollectionResult(
                success=False,
                message=f"Failed to collect MAC table for device {device.hostname}",
                data=None
            )
        
        # 清空现有MAC地址表
        db.query(MACAddress).filter(MACAddress.device_id == device_id).delete()
        
        # 保存新的MAC地址表
        for mac_entry in mac_table:
            mac_address = MACAddress(**mac_entry)
            db.add(mac_address)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"MAC table collected successfully for device {device.hostname}",
            data={"mac_entries_count": len(mac_table)}
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error collecting MAC table: {str(e)}",
            data=None
        )


@router.post("/batch/collect", response_model=DeviceCollectionResult)
async def batch_collect_device_info(
    collection_request: DeviceCollectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量采集设备信息
    
    Args:
        collection_request: 批量采集请求
        background_tasks: 后台任务
        db: 数据库会话
        
    Returns:
        批量采集结果
    """
    # 获取设备列表
    devices = db.query(Device).filter(Device.id.in_(collection_request.device_ids)).all()
    
    if not devices:
        return DeviceCollectionResult(
            success=False,
            message="No valid devices found",
            data=None
        )
    
    try:
        # 执行批量采集
        results = await netmiko_service.batch_collect_device_info(
            devices, 
            collection_request.collect_types
        )
        
        # 处理采集结果并保存到数据库
        for detail in results['details']:
            if detail['success']:
                device_id = detail['device_id']
                
                # 保存版本信息
                if 'version' in detail['data']:
                    version_info = detail['data']['version']
                    device_version = DeviceVersion(**version_info)
                    db.add(device_version)
                    
                    # 更新设备表中的版本信息
                    device = db.query(Device).filter(Device.id == device_id).first()
                    if device and version_info.get('software_version'):
                        device.os_version = version_info['software_version']
                
                # 保存序列号
                if 'serial' in detail['data']:
                    serial = detail['data']['serial']
                    device = db.query(Device).filter(Device.id == device_id).first()
                    if device:
                        device.sn = serial
                
                # 保存接口信息
                if 'interfaces' in detail['data']:
                    interfaces = detail['data']['interfaces']
                    # 清空现有接口信息
                    db.query(Port).filter(Port.device_id == device_id).delete()
                    # 保存新的接口信息
                    for interface_info in interfaces:
                        port = Port(**interface_info)
                        db.add(port)
                
                # 保存MAC地址表
                if 'mac_table' in detail['data']:
                    mac_table = detail['data']['mac_table']
                    # 清空现有MAC地址表
                    db.query(MACAddress).filter(MACAddress.device_id == device_id).delete()
                    # 保存新的MAC地址表
                    for mac_entry in mac_table:
                        mac_address = MACAddress(**mac_entry)
                        db.add(mac_address)
        
        db.commit()
        
        return DeviceCollectionResult(
            success=True,
            message=f"Batch collection completed: {results['success']} success, {results['failed']} failed",
            data=results
        )
        
    except Exception as e:
        db.rollback()
        return DeviceCollectionResult(
            success=False,
            message=f"Error in batch collection: {str(e)}",
            data=None
        )


@router.get("/mac-addresses", response_model=List[MACAddressSchema])
def get_mac_addresses(
    device_id: Optional[int] = None,
    mac_address: Optional[str] = None,
    vlan_id: Optional[int] = None,
    interface: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取MAC地址表
    
    Args:
        device_id: 设备ID（可选）
        mac_address: MAC地址（可选）
        vlan_id: VLAN ID（可选）
        interface: 接口名称（可选）
        skip: 跳过记录数
        limit: 限制记录数
        db: 数据库会话
        
    Returns:
        MAC地址列表
    """
    query = db.query(MACAddress)
    
    if device_id:
        query = query.filter(MACAddress.device_id == device_id)
    
    if mac_address:
        query = query.filter(MACAddress.mac_address == mac_address)
    
    if vlan_id:
        query = query.filter(MACAddress.vlan_id == vlan_id)
    
    if interface:
        query = query.filter(MACAddress.interface == interface)
    
    mac_addresses = query.order_by(MACAddress.last_seen.desc()).offset(skip).limit(limit).all()
    return mac_addresses


@router.post("/mac-addresses/search", response_model=List[MACAddressSchema])
def search_mac_addresses(
    search_mac: str,
    db: Session = Depends(get_db)
):
    """
    搜索MAC地址
    
    Args:
        search_mac: 要搜索的MAC地址（支持模糊匹配）
        db: 数据库会话
        
    Returns:
        匹配的MAC地址列表
    """
    query = db.query(MACAddress).filter(MACAddress.mac_address.like(f"%{search_mac}%"))
    mac_addresses = query.order_by(MACAddress.last_seen.desc()).all()
    return mac_addresses


@router.get("/{device_id}/mac-addresses", response_model=List[MACAddressSchema])
def get_device_mac_addresses(
    device_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取指定设备的MAC地址表
    
    Args:
        device_id: 设备ID
        skip: 跳过记录数
        limit: 限制记录数
        db: 数据库会话
        
    Returns:
        MAC地址列表
    """
    # 检查设备是否存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with id {device_id} not found"
        )
    
    mac_addresses = db.query(MACAddress).filter(
        MACAddress.device_id == device_id
    ).order_by(MACAddress.last_seen.desc()).offset(skip).limit(limit).all()
    
    return mac_addresses
