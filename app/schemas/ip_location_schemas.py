"""
IP 定位功能 Pydantic Schemas
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class ARPEntryBase(BaseModel):
    ip_address: str
    mac_address: str
    vlan_id: Optional[int] = None
    interface: Optional[str] = None
    arp_type: Optional[str] = None
    age_minutes: Optional[int] = None


class ARPEntryCreate(ARPEntryBase):
    device_id: int
    last_seen: Optional[datetime] = None


class ARPEntrySchema(ARPEntryBase):
    id: int
    device_id: int
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MACAddressSchema(BaseModel):
    id: int
    device_id: int
    mac_address: str
    vlan_id: Optional[int] = None
    interface: str
    address_type: str
    is_trunk: Optional[bool] = None
    learned_from: Optional[str] = None
    last_seen: datetime

    class Config:
        from_attributes = True


class IPLocationResult(BaseModel):
    """IP 定位结果"""
    ip_address: str
    mac_address: str
    device_id: int
    device_hostname: str
    device_ip: str
    interface: str
    vlan_id: Optional[int] = None
    last_seen: datetime
    confidence: float = 1.0  # 匹配置信度


class IPLocationQueryResponse(BaseModel):
    """IP 查询响应"""
    success: bool
    ip_address: str
    locations: List[IPLocationResult]
    message: Optional[str] = None


class IPListEntry(BaseModel):
    """IP 列表项"""
    ip_address: str
    mac_address: str
    device_id: int
    device_hostname: str
    interface: str
    vlan_id: Optional[int] = None
    last_seen: datetime


class IPListResponse(BaseModel):
    """IP 列表响应"""
    total: int
    items: List[IPListEntry]
    page: int
    page_size: int


class CollectionStatus(BaseModel):
    """收集状态"""
    is_running: bool
    last_run_at: Optional[datetime] = None
    last_run_success: bool = True
    last_run_message: Optional[str] = None
    devices_total: int = 0
    devices_completed: int = 0
    devices_failed: int = 0
    arp_entries_collected: int = 0
    mac_entries_collected: int = 0


class CollectionTriggerResponse(BaseModel):
    """触发收集响应"""
    success: bool
    message: str
    status: Optional[CollectionStatus] = None
