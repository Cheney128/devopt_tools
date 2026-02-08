"""
备份任务模型定义
定义批量备份任务相关的数据模型
"""
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.models import Base


class BackupTaskStatus(str, Enum):
    """备份任务状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class BackupPriority(str, Enum):
    """备份任务优先级枚举"""
    LOW = "low"       # 低优先级
    NORMAL = "normal" # 正常优先级
    HIGH = "high"     # 高优先级


class BackupTask(Base):
    """
    批量备份任务表
    用于管理和跟踪批量配置备份任务的执行状态
    """
    __tablename__ = "backup_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True, nullable=False)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(SQLEnum(BackupTaskStatus), default=BackupTaskStatus.PENDING)
    priority = Column(SQLEnum(BackupPriority), default=BackupPriority.NORMAL)
    total = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    filters = Column(JSON, default=dict)
    max_concurrent = Column(Integer, default=3)
    timeout = Column(Integer, default=300)
    retry_count = Column(Integer, default=2)
    notify_on_complete = Column(Integer, default=0)
    created_by = Column(String(100), nullable=True)
    error_details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<BackupTask(task_id='{self.task_id}', status='{self.status}')>"
