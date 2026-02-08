"""
监控统计Schema定义
定义备份计划监控面板相关的数据模型
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class BackupStatistics(BaseModel):
    """备份统计信息"""
    total_devices: int = 0
    total_schedules: int = 0
    active_schedules: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None


class DeviceBackupStatistics(BaseModel):
    """设备备份统计"""
    device_id: int
    device_name: str
    total_backups: int = 0
    successful_backups: int = 0
    failed_backups: int = 0
    success_rate: float = 0.0
    last_backup_time: Optional[datetime] = None
    average_execution_time: float = 0.0


class ScheduleStatistics(BaseModel):
    """备份计划统计"""
    schedule_id: int
    device_id: int
    device_name: str
    schedule_type: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    last_execution_time: Optional[datetime] = None
    average_execution_time: float = 0.0
    is_active: bool = True


class ExecutionLogResponse(BaseModel):
    """执行日志响应"""
    id: int
    task_id: str
    device_id: int
    device_name: Optional[str] = None
    schedule_id: Optional[int] = None
    status: str
    execution_time: Optional[float] = None
    trigger_type: str
    config_id: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class DashboardSummary(BaseModel):
    """仪表盘摘要"""
    statistics: BackupStatistics
    recent_executions: list[ExecutionLogResponse]
    failed_today: int = 0
    scheduled_today: int = 0
    devices_backup_today: int = 0


class TrendData(BaseModel):
    """趋势数据"""
    date: str
    total: int
    success: int
    failed: int
    success_rate: float


class ExecutionStatusDistribution(BaseModel):
    """执行状态分布"""
    status: str
    count: int
    percentage: float
