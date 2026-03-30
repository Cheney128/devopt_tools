# -*- coding: utf-8 -*-
"""
IP 定位当前数据表模型

包含：
- ARPEntry: ARP 当前数据表
- MACAddressCurrent: MAC 当前数据表
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.models import Base


class ARPEntry(Base):
    """
    ARP 当前数据表

    存储设备最新的 ARP 表项，用于 IP 定位预计算。
    """
    __tablename__ = "arp_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(50), nullable=False, index=True, comment='IP 地址')
    mac_address = Column(String(17), nullable=False, comment='MAC 地址')
    arp_device_id = Column(Integer, nullable=False, comment='ARP 来源设备 ID')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')
    arp_interface = Column(String(100), nullable=True, comment='ARP 接口')
    source_type = Column(String(20), nullable=True, comment='来源类型')
    last_seen = Column(DateTime, nullable=False, default=func.now(), index=True, comment='最后发现时间')
    collection_batch_id = Column(String(64), nullable=False, index=True, comment='采集批次 ID')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 复合索引
    __table_args__ = (
        Index('idx_ip_mac', 'ip_address', 'mac_address'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'arp_device_id': self.arp_device_id,
            'vlan_id': self.vlan_id,
            'arp_interface': self.arp_interface,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }


class MACAddressCurrent(Base):
    """
    MAC 当前数据表

    存储设备最新的 MAC 地址表，用于 IP 定位预计算。
    """
    __tablename__ = "mac_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mac_address = Column(String(17), nullable=False, index=True, comment='MAC 地址')
    mac_device_id = Column(Integer, nullable=False, index=True, comment='MAC 来源设备 ID')
    mac_interface = Column(String(100), nullable=False, comment='MAC 接口')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')
    is_trunk = Column(Boolean, nullable=True, default=False, comment='是否 Trunk 接口')
    interface_description = Column(String(255), nullable=True, comment='接口描述')
    source_type = Column(String(20), nullable=True, comment='来源类型')
    last_seen = Column(DateTime, nullable=False, default=func.now(), index=True, comment='最后发现时间')
    collection_batch_id = Column(String(64), nullable=True, comment='采集批次 ID')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'mac_address': self.mac_address,
            'mac_device_id': self.mac_device_id,
            'vlan_id': self.vlan_id,
            'mac_interface': self.mac_interface,
            'is_trunk': self.is_trunk,
            'interface_description': self.interface_description,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }
