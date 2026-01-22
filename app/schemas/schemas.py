"""
数据验证模式
定义API请求和响应的数据结构
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict, Json
from typing import Optional, List, Dict, Any
from datetime import datetime


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# 设备相关模型
class DeviceBase(BaseModel):
    """设备基础模型"""
    hostname: str = Field(..., description="设备主机名")
    ip_address: str = Field(..., description="设备IP地址")
    vendor: str = Field(..., description="设备厂商")
    model: str = Field(..., description="设备型号")
    os_version: Optional[str] = Field(None, description="操作系统版本")
    location: Optional[str] = Field(None, description="设备位置")
    contact: Optional[str] = Field(None, description="联系人")
    status: str = Field("active", description="设备状态")
    login_method: str = Field("ssh", description="登录方式")
    login_port: int = Field(22, description="登录端口")
    username: Optional[str] = Field(None, description="登录用户名")
    password: Optional[str] = Field(None, description="登录密码")
    sn: Optional[str] = Field(None, description="设备序列号")

    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v):
        """验证IP地址格式"""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')

    @field_validator('login_method')
    @classmethod
    def validate_login_method(cls, v):
        """验证登录方式"""
        if v not in ['ssh', 'telnet']:
            raise ValueError('Login method must be either ssh or telnet')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证设备状态"""
        if v not in ['active', 'inactive', 'maintenance', 'offline']:
            raise ValueError('Status must be active, inactive, maintenance, or offline')
        return v


class DeviceCreate(DeviceBase):
    """创建设备模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""
    hostname: Optional[str] = Field(None, description="设备主机名")
    ip_address: Optional[str] = Field(None, description="设备IP地址")
    vendor: Optional[str] = Field(None, description="设备厂商")
    model: Optional[str] = Field(None, description="设备型号")
    os_version: Optional[str] = Field(None, description="操作系统版本")
    location: Optional[str] = Field(None, description="设备位置")
    contact: Optional[str] = Field(None, description="联系人")
    status: Optional[str] = Field(None, description="设备状态")
    login_method: Optional[str] = Field(None, description="登录方式")
    login_port: Optional[int] = Field(None, description="登录端口")
    username: Optional[str] = Field(None, description="登录用户名")
    password: Optional[str] = Field(None, description="登录密码")
    sn: Optional[str] = Field(None, description="设备序列号")


class Device(DeviceBase):
    """设备模型"""
    id: int = Field(..., description="设备ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# 端口相关模型
class PortBase(BaseModel):
    """端口基础模型"""
    port_name: str = Field(..., description="端口名称")
    status: str = Field("up", description="端口状态")
    speed: Optional[str] = Field(None, description="端口速率")
    description: Optional[str] = Field(None, description="端口描述")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证端口状态"""
        if v not in ['up', 'down', 'disabled']:
            raise ValueError('Port status must be up, down, or disabled')
        return v


class PortCreate(PortBase):
    """创建端口模型"""
    device_id: int = Field(..., description="设备ID")


class PortUpdate(BaseModel):
    """更新端口模型"""
    port_name: Optional[str] = Field(None, description="端口名称")
    status: Optional[str] = Field(None, description="端口状态")
    speed: Optional[str] = Field(None, description="端口速率")
    description: Optional[str] = Field(None, description="端口描述")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")


class Port(PortBase):
    """端口模型"""
    id: int = Field(..., description="端口ID")
    device_id: int = Field(..., description="设备ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# VLAN相关模型
class VLANBase(BaseModel):
    """VLAN基础模型"""
    vlan_name: str = Field(..., description="VLAN名称")
    vlan_description: Optional[str] = Field(None, description="VLAN描述")


class VLANCreate(VLANBase):
    """创建VLAN模型"""
    device_id: int = Field(..., description="设备ID")


class VLANUpdate(BaseModel):
    """更新VLAN模型"""
    vlan_name: Optional[str] = Field(None, description="VLAN名称")
    vlan_description: Optional[str] = Field(None, description="VLAN描述")


class VLAN(VLANBase):
    """VLAN模型"""
    id: int = Field(..., description="VLAN ID")
    device_id: int = Field(..., description="设备ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# 巡检相关模型
class InspectionBase(BaseModel):
    """巡检基础模型"""
    device_id: int = Field(..., description="设备ID")
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用率")
    interface_status: Optional[Dict[str, Any]] = Field(None, description="接口状态")
    error_logs: Optional[str] = Field(None, description="错误日志")
    status: str = Field("completed", description="巡检状态")


class InspectionCreate(InspectionBase):
    """创建巡检记录模型"""
    pass


class Inspection(InspectionBase):
    """巡检模型"""
    id: int = Field(..., description="巡检ID")
    inspection_time: Optional[datetime] = Field(None, description="巡检时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


# 配置相关模型
class ConfigurationBase(BaseModel):
    """配置基础模型"""
    device_id: int = Field(..., description="设备ID")
    config_content: Optional[str] = Field(None, description="配置内容")
    config_time: Optional[datetime] = Field(None, description="配置时间")
    version: Optional[str] = Field("1.0", description="配置版本")
    change_description: Optional[str] = Field(None, description="配置变更描述")
    git_commit_id: Optional[str] = Field(None, description="Git提交ID")


class ConfigurationCreate(ConfigurationBase):
    """创建配置记录模型"""
    pass


class Configuration(ConfigurationBase):
    """配置模型"""
    id: int = Field(..., description="配置ID")
    device_name: Optional[str] = Field(None, description="设备名称")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


# Git配置相关模型
class GitConfigBase(BaseModel):
    """Git配置基础模型"""
    repo_url: str = Field(..., description="Git仓库URL")
    username: Optional[str] = Field(None, description="Git用户名")
    password: Optional[str] = Field(None, description="Git密码或Token")
    branch: Optional[str] = Field("main", description="Git分支")
    ssh_key_path: Optional[str] = Field(None, description="SSH密钥路径")
    is_active: Optional[bool] = Field(True, description="是否激活")


class GitConfigCreate(GitConfigBase):
    """创建Git配置模型"""
    pass


class GitConfigUpdate(BaseModel):
    """更新Git配置模型"""
    repo_url: Optional[str] = Field(None, description="Git仓库URL")
    username: Optional[str] = Field(None, description="Git用户名")
    password: Optional[str] = Field(None, description="Git密码或Token")
    branch: Optional[str] = Field(None, description="Git分支")
    ssh_key_path: Optional[str] = Field(None, description="SSH密钥路径")
    is_active: Optional[bool] = Field(None, description="是否激活")


class GitConfig(GitConfigBase):
    """Git配置模型"""
    id: int = Field(..., description="Git配置ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# MAC地址相关模型
class MACAddressBase(BaseModel):
    """MAC地址基础模型"""
    mac_address: str = Field(..., description="MAC地址")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    interface: str = Field(..., description="学习接口")
    address_type: str = Field("dynamic", description="地址类型")
    last_seen: Optional[datetime] = Field(None, description="最后发现时间")

    @field_validator('mac_address')
    @classmethod
    def validate_mac_address(cls, v):
        """验证MAC地址格式"""
        import re
        # 支持多种MAC地址格式：00:11:22:33:44:55 或 0011.2233.4455
        mac_pattern_colon = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        mac_pattern_dot = re.compile(r'^([0-9A-Fa-f]{4})([.-])([0-9A-Fa-f]{4})([.-])([0-9A-Fa-f]{4})([.-])([0-9A-Fa-f]{2})$')
        if not (mac_pattern_colon.match(v) or mac_pattern_dot.match(v)):
            raise ValueError('Invalid MAC address format')
        return v

    @field_validator('address_type')
    @classmethod
    def validate_address_type(cls, v):
        """验证地址类型"""
        if v not in ['static', 'dynamic']:
            raise ValueError('Address type must be either static or dynamic')
        return v


class MACAddressCreate(MACAddressBase):
    """创建MAC地址模型"""
    device_id: int = Field(..., description="设备ID")


class MACAddress(MACAddressBase):
    """MAC地址模型"""
    id: int = Field(..., description="MAC地址ID")
    device_id: int = Field(..., description="设备ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    model_config = ConfigDict(from_attributes=True)


# 设备版本信息相关模型
class DeviceVersionBase(BaseModel):
    """设备版本信息基础模型"""
    software_version: Optional[str] = Field(None, description="软件版本")
    hardware_version: Optional[str] = Field(None, description="硬件版本")
    boot_version: Optional[str] = Field(None, description="启动版本")
    system_image: Optional[str] = Field(None, description="系统镜像")
    uptime: Optional[str] = Field(None, description="运行时间")
    collected_at: Optional[datetime] = Field(None, description="采集时间")


class DeviceVersionCreate(DeviceVersionBase):
    """创建设备版本信息模型"""
    device_id: int = Field(..., description="设备ID")


class DeviceVersion(DeviceVersionBase):
    """设备版本信息模型"""
    id: int = Field(..., description="版本信息ID")
    device_id: int = Field(..., description="设备ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")

    model_config = ConfigDict(from_attributes=True)


# 批量操作相关模型
class BatchDeleteRequest(BaseModel):
    """批量删除请求模型"""
    ids: List[int] = Field(..., description="要删除的ID列表")


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求模型"""
    ids: List[int] = Field(..., description="要更新的ID列表")
    status: str = Field(..., description="新状态")


class BatchOperationResult(BaseModel):
    """批量操作结果模型"""
    success: bool = Field(..., description="操作是否全部成功")
    message: str = Field(..., description="操作结果消息")
    total: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_devices: Optional[List[str]] = Field(None, description="失败的设备列表")


# 设备采集相关模型
class DeviceCollectionRequest(BaseModel):
    """设备信息采集请求模型"""
    device_ids: List[int] = Field(..., description="设备ID列表")
    collect_types: List[str] = Field(
        ...,
        description="采集类型列表",
        json_schema_extra={"example": ["version", "serial", "interfaces", "mac_table", "running_config"]}
    )

    @field_validator('collect_types')
    @classmethod
    def validate_collect_types(cls, v):
        """验证采集类型"""
        valid_types = ['version', 'serial', 'interfaces', 'mac_table', 'running_config']
        for collect_type in v:
            if collect_type not in valid_types:
                raise ValueError(f'Invalid collect type: {collect_type}. Must be one of {valid_types}')
        return v


class DeviceCollectionResult(BaseModel):
    """设备信息采集结果模型"""
    success: bool = Field(..., description="采集是否成功")
    message: str = Field(..., description="采集结果消息")
    data: Optional[Any] = Field(None, description="采集数据")


# Oxidized集成相关模型
class OxidizedStatus(BaseModel):
    """Oxidized状态模型"""
    status: str = Field(..., description="Oxidized服务状态")
    message: str = Field(..., description="状态消息")


class OxidizedSyncResult(BaseModel):
    """Oxidized同步结果模型"""
    success: bool = Field(..., description="同步是否成功")
    message: str = Field(..., description="同步结果消息")
    synced_count: int = Field(..., description="同步的设备数量")


# 通用响应模型
class InspectionResult(BaseModel):
    """巡检结果模型"""
    success: bool = Field(..., description="巡检是否成功")
    message: str = Field(..., description="巡检结果消息")
    data: Optional[Dict[str, Any]] = Field(None, description="巡检数据")


# 分页相关模型
class PaginatedResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    items: List[Any] = Field(..., description="当前页数据")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


# 错误响应模型
class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


# 设备详情模型（放在文件末尾，确保引用的类型已定义）
class DeviceWithDetails(Device):
    """设备详情模型（包含关联数据）"""
    ports: Optional[List[Port]] = Field(default_factory=list, description="端口列表")
    vlans: Optional[List[VLAN]] = Field(default_factory=list, description="VLAN列表")
    inspections: Optional[List[Inspection]] = Field(default_factory=list, description="巡检记录列表")
    configurations: Optional[List[Configuration]] = Field(default_factory=list, description="配置记录列表")
    mac_addresses: Optional[List[MACAddress]] = Field(default_factory=list, description="MAC地址列表")
    versions: Optional[List[DeviceVersion]] = Field(default_factory=list, description="版本信息列表")
