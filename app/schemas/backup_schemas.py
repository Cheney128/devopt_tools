"""
备份相关Schema定义
定义批量备份请求和响应的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class BackupPriority(str, Enum):
    """备份优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class BackupTaskStatus(str, Enum):
    """备份任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupFilter(BaseModel):
    """备份筛选条件"""
    filter_status: Optional[str] = Field(None, description="按设备状态筛选 (online/offline/maintenance)")
    filter_vendor: Optional[str] = Field(None, description="按厂商筛选")
    async_execute: bool = Field(True, description="是否异步执行")
    notify_on_complete: bool = Field(False, description="完成后是否通知")
    priority: BackupPriority = Field(BackupPriority.NORMAL, description="任务优先级")
    max_concurrent: int = Field(3, ge=1, le=10, description="最大并发数")
    timeout: int = Field(300, ge=60, le=3600, description="单设备超时时间（秒）")
    retry_count: int = Field(2, ge=0, le=5, description="失败重试次数")


class BackupTaskResponse(BaseModel):
    """备份任务响应"""
    task_id: str
    status: BackupTaskStatus
    total: int
    completed: int = 0
    success_count: int = 0
    failed_count: int = 0
    message: str
    progress_percentage: float = 0.0


class BackupTaskDetailResponse(BackupTaskResponse):
    """备份任务详情响应"""
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = []
    results: Optional[List[Dict[str, Any]]] = None


class BackupTaskListResponse(BaseModel):
    """备份任务列表响应"""
    tasks: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class CancelTaskResponse(BaseModel):
    """取消任务响应"""
    message: str
    task_id: str


class BackupResultItem(BaseModel):
    """单个设备备份结果"""
    device_id: int
    device_name: str
    success: bool
    config_id: Optional[int] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: Optional[float] = None
    config_size: Optional[int] = None
    git_commit_id: Optional[str] = None
