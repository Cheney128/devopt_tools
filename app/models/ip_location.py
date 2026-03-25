# -*- coding: utf-8 -*-
"""
IP 定位模型定义

包含：
- IPLocationCurrent: IP 定位当前状态表
- IPLocationHistory: IP 定位历史记录表
- IPLocationSettings: IP 定位配置表
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, Index, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.models.models import Base


class IPLocationCurrent(Base):
    """
    IP 定位当前状态表

    存储最新的 IP 定位结果，包含冗余设备信息以避免 N+1 查询。
    """
    __tablename__ = "ip_location_current"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(50), nullable=False, index=True, comment='IP地址')
    mac_address = Column(String(17), nullable=False, comment='MAC地址')

    # ARP 来源设备信息
    arp_source_device_id = Column(Integer, nullable=False, comment='ARP来源设备ID')
    arp_device_hostname = Column(String(255), nullable=True, comment='ARP来源设备主机名（冗余）')
    arp_device_ip = Column(String(50), nullable=True, comment='ARP来源设备IP（冗余）')
    arp_device_location = Column(String(255), nullable=True, comment='ARP来源设备位置（冗余）')

    # MAC 命中设备信息
    mac_hit_device_id = Column(Integer, nullable=True, comment='MAC命中设备ID')
    mac_device_hostname = Column(String(255), nullable=True, comment='MAC命中设备主机名（冗余）')
    mac_device_ip = Column(String(50), nullable=True, comment='MAC命中设备IP（冗余）')
    mac_device_location = Column(String(255), nullable=True, comment='MAC命中设备位置（冗余）')

    # 接入信息
    access_interface = Column(String(100), nullable=True, comment='接入接口')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')

    # 定位置信度
    confidence = Column(DECIMAL(5, 2), nullable=False, default=0.00, index=True, comment='置信度')
    is_uplink = Column(Boolean, nullable=False, default=False, comment='是否上行链路')
    is_core_switch = Column(Boolean, nullable=False, default=False, comment='是否核心交换机')
    match_type = Column(String(20), nullable=False, comment='匹配类型')

    # 时间信息
    last_seen = Column(DateTime, nullable=False, index=True, comment='最后发现时间')
    calculated_at = Column(DateTime, nullable=False, default=func.now(), comment='计算时间')

    # 批次信息
    calculate_batch_id = Column(String(64), nullable=False, index=True, comment='计算批次ID')
    batch_status = Column(String(20), nullable=False, default='calculating', index=True, comment='批次状态')

    # 复合索引
    __table_args__ = (
        Index('idx_ip_mac', 'ip_address', 'mac_address'),
        Index('idx_arp_device', 'arp_source_device_id'),
        Index('idx_mac_device', 'mac_hit_device_id'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'arp_source_device_id': self.arp_source_device_id,
            'arp_device_hostname': self.arp_device_hostname,
            'arp_device_ip': self.arp_device_ip,
            'arp_device_location': self.arp_device_location,
            'mac_hit_device_id': self.mac_hit_device_id,
            'mac_device_hostname': self.mac_device_hostname,
            'mac_device_ip': self.mac_device_ip,
            'mac_device_location': self.mac_device_location,
            'access_interface': self.access_interface,
            'vlan_id': self.vlan_id,
            'confidence': float(self.confidence) if self.confidence else 0.0,
            'is_uplink': self.is_uplink,
            'is_core_switch': self.is_core_switch,
            'match_type': self.match_type,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
        }


class IPLocationHistory(Base):
    """
    IP 定位历史记录表

    存储已下线 IP 的历史定位记录，保留 30 天。
    """
    __tablename__ = "ip_location_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(50), nullable=False, index=True, comment='IP地址')
    mac_address = Column(String(17), nullable=False, comment='MAC地址')

    # ARP 来源设备信息
    arp_source_device_id = Column(Integer, nullable=True, comment='ARP来源设备ID')
    arp_device_hostname = Column(String(255), nullable=True, comment='ARP来源设备主机名')
    arp_device_ip = Column(String(50), nullable=True, comment='ARP来源设备IP')
    arp_device_location = Column(String(255), nullable=True, comment='ARP来源设备位置')

    # MAC 命中设备信息
    mac_hit_device_id = Column(Integer, nullable=True, comment='MAC命中设备ID')
    mac_device_hostname = Column(String(255), nullable=True, comment='MAC命中设备主机名')
    mac_device_ip = Column(String(50), nullable=True, comment='MAC命中设备IP')
    mac_device_location = Column(String(255), nullable=True, comment='MAC命中设备位置')

    # 接入信息
    access_interface = Column(String(100), nullable=True, comment='接入接口')
    vlan_id = Column(Integer, nullable=True, comment='VLAN ID')

    # 定位置信度
    confidence = Column(DECIMAL(5, 2), nullable=False, default=0.00, comment='置信度')
    is_uplink = Column(Boolean, nullable=False, default=False, comment='是否上行链路')
    is_core_switch = Column(Boolean, nullable=False, default=False, comment='是否核心交换机')
    match_type = Column(String(20), nullable=False, comment='匹配类型')

    # 时间信息
    first_seen = Column(DateTime, nullable=False, comment='首次发现时间')
    last_seen = Column(DateTime, nullable=False, comment='最后发现时间')
    archived_at = Column(DateTime, nullable=False, default=func.now(), index=True, comment='归档时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'arp_source_device_id': self.arp_source_device_id,
            'arp_device_hostname': self.arp_device_hostname,
            'arp_device_ip': self.arp_device_ip,
            'arp_device_location': self.arp_device_location,
            'mac_hit_device_id': self.mac_hit_device_id,
            'mac_device_hostname': self.mac_device_hostname,
            'mac_device_ip': self.mac_device_ip,
            'mac_device_location': self.mac_device_location,
            'access_interface': self.access_interface,
            'vlan_id': self.vlan_id,
            'confidence': float(self.confidence) if self.confidence else 0.0,
            'is_uplink': self.is_uplink,
            'is_core_switch': self.is_core_switch,
            'match_type': self.match_type,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
        }


class IPLocationSettings(Base):
    """
    IP 定位配置表

    存储系统配置参数，如下线检测阈值、历史保留天数等。
    """
    __tablename__ = "ip_location_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment='配置键')
    value = Column(Text, nullable=True, comment='配置值')
    description = Column(Text, nullable=True, comment='配置说明')
    created_at = Column(DateTime, nullable=False, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')

    # 默认配置
    DEFAULT_SETTINGS = {
        'offline_threshold_minutes': '30',  # 下线检测阈值（分钟）
        'history_retention_days': '30',     # 历史保留天数
        'calculation_interval_minutes': '10', # 预计算间隔（分钟）
        'confidence_threshold': '0.5',       # 置信度阈值
    }

    @classmethod
    def get_default(cls, key: str) -> str:
        """获取默认配置值"""
        return cls.DEFAULT_SETTINGS.get(key, '')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }