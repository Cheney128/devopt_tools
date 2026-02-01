"""
数据模型定义
定义数据库表结构
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime


# 创建基础类
Base = declarative_base()


class Device(Base):
    """
    设备信息表
    """
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(50), unique=True, nullable=False, index=True)
    vendor = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    os_version = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    login_method = Column(String(20), nullable=False, default="ssh")
    login_port = Column(Integer, nullable=False, default=22)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    sn = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    ports = relationship("Port", back_populates="device", cascade="all, delete-orphan")
    vlans = relationship("VLAN", back_populates="device", cascade="all, delete-orphan")
    inspections = relationship("Inspection", back_populates="device", cascade="all, delete-orphan")
    configurations = relationship("Configuration", back_populates="device", cascade="all, delete-orphan")
    mac_addresses = relationship("MACAddress", back_populates="device", cascade="all, delete-orphan")
    device_versions = relationship("DeviceVersion", back_populates="device", cascade="all, delete-orphan")
    backup_schedules = relationship("BackupSchedule", back_populates="device", cascade="all, delete-orphan")


class Port(Base):
    """
    端口信息表
    """
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    port_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="up")
    speed = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    vlan_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="ports")


class VLAN(Base):
    """
    VLAN信息表
    """
    __tablename__ = "vlans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    vlan_name = Column(String(100), nullable=False)
    vlan_description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="vlans")


class Inspection(Base):
    """
    巡检结果表
    """
    __tablename__ = "inspections"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    inspection_time = Column(DateTime, nullable=False, default=func.now())
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    interface_status = Column(JSON, nullable=True)
    error_logs = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="inspections")


class Configuration(Base):
    """
    配置信息表
    """
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    config_content = Column(Text, nullable=True)
    config_time = Column(DateTime, nullable=False, default=func.now())
    version = Column(String(50), nullable=False, default="1.0")
    change_description = Column(Text, nullable=True)
    git_commit_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="configurations")


class GitConfig(Base):
    """
    Git配置信息表
    """
    __tablename__ = "git_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repo_url = Column(String(255), nullable=False, unique=True)
    username = Column(String(100), nullable=True)
    password = Column(String(255), nullable=True)
    branch = Column(String(50), nullable=False, default="main")
    ssh_key_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class BackupSchedule(Base):
    """
    备份任务计划表
    """
    __tablename__ = "backup_schedules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    schedule_type = Column(String(20), nullable=False, default="daily")  # hourly, daily, monthly
    time = Column(String(10), nullable=True)  # 时间点，格式 HH:MM
    day = Column(Integer, nullable=True)  # 每月的日期，1-31
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="backup_schedules")


class MACAddress(Base):
    """
    MAC地址表
    """
    __tablename__ = "mac_addresses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    mac_address = Column(String(17), nullable=False, index=True)
    vlan_id = Column(Integer, nullable=True)
    interface = Column(String(100), nullable=False)
    address_type = Column(String(20), nullable=False, default="dynamic")
    last_seen = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="mac_addresses")


class DeviceVersion(Base):
    """
    设备版本信息表
    """
    __tablename__ = "device_versions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    software_version = Column(String(100), nullable=True)
    hardware_version = Column(String(100), nullable=True)
    boot_version = Column(String(100), nullable=True)
    system_image = Column(String(255), nullable=True)
    uptime = Column(String(100), nullable=True)
    collected_at = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 关联关系
    device = relationship("Device", back_populates="device_versions")


class CommandTemplate(Base):
    """
    命令模板表
    """
    __tablename__ = "command_templates"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    command = Column(Text, nullable=False)
    vendor = Column(String(50), nullable=True, index=True)  # 适用厂商
    device_type = Column(String(50), nullable=True, index=True)  # 适用设备类型
    variables = Column(JSON, nullable=True)  # 模板变量定义
    tags = Column(JSON, nullable=True)  # 标签列表
    is_public = Column(Boolean, nullable=False, default=True)  # 是否公开
    created_by = Column(String(100), nullable=True)  # 创建者
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class CommandHistory(Base):
    """
    命令执行历史表
    """
    __tablename__ = "command_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    command = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    executed_by = Column(String(100), nullable=True)  # 执行用户
    execution_time = Column(DateTime, nullable=False, default=func.now())
    duration = Column(Float, nullable=True)  # 执行时长（秒）
    
    # 关联关系
    device = relationship("Device", back_populates="command_history")


# 为Device类添加command_history关联
Device.command_history = relationship("CommandHistory", back_populates="device", cascade="all, delete-orphan")
