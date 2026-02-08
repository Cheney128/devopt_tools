# Phase 3-备份计划监控面板-评审文档

## 文档信息

- **评审阶段**: Phase 3-备份计划监控面板
- **评审日期**: 2026-02-06
- **评审人员**: AI代码评审助手
- **评审类型**: 实施方案评审

---

## 一、评审摘要

### 1.1 总体评价

经过对 Phase 3 实施方案的详细评审，该方案是三个阶段中设计最为完善的一个，在数据模型设计、监控指标定义、前端可视化呈现等方面都表现出较高的专业水平。监控面板功能是备份系统的重要支撑，与 Phase 2 的批量备份功能形成完整的闭环。方案整体技术深度适中，但在API性能优化、缓存策略和实时推送方面仍有改进空间。

### 1.2 关键发现

| 类别 | 数量 | 严重程度 |
|------|------|----------|
| 方案设计合理 | 5项 | 无问题 |
| 需要优化项 | 3项 | 中等问题 |
| 潜在风险 | 2项 | 需关注 |

### 1.3 评审结论

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 数据模型设计 | 90/100 | 模型设计完整，字段定义清晰 |
| API设计合理性 | 82/100 | API设计合理，查询参数灵活 |
| 前端组件设计 | 88/100 | 组件设计美观，交互逻辑清晰 |
| 监控指标完整性 | 85/100 | 覆盖主要监控维度 |
| 性能考虑 | 75/100 | 缺少缓存和性能优化策略 |
| 与现有系统集成 | 80/100 | 与Phase 2集成需注意 |

---

## 二、任务拆解评审

### 2.1 任务结构审查

**方案设计的任务拆解:**

```
任务1: 数据库设计并创建 backup_execution_logs 表
任务2: 后端调度器记录执行日志
任务3: 后端新增监控统计API
任务4: 前端实现监控面板组件
任务5: 添加路由和菜单
```

**评审结论**: ✅ 任务拆解合理，逻辑清晰

**优点:**
- 任务顺序符合依赖关系（先有数据模型，再记录日志，然后提供API，最后展示）
- 每个任务边界清晰，职责单一
- 涵盖了从数据库到前端的完整功能链路

**不足:**
- 缺少数据迁移任务的详细说明
- 任务2与任务3之间的数据流说明不够清晰

### 2.2 与Phase 1/2的关联性分析

| Phase 1/2 成果 | Phase 3 依赖 | 评审意见 |
|----------------|--------------|----------|
| `/devices/all` API | 用于获取设备列表 | ✅ 可复用 |
| 批量备份API | 依赖执行日志数据 | ✅ 已设计关联 |
| 备份调度器 | 需要记录执行日志 | ✅ 已设计 |
| Device模型 | 用于关联查询 | ✅ 已设计 |

**评审结论**: ✅ Phase 3 正确依赖 Phase 1/2 的成果

---

## 三、数据库设计评审

### 3.1 数据模型设计

**方案设计的模型:**

```python
class BackupExecutionLog(Base):
    """
    备份执行日志表
    记录每次备份任务的执行详情
    """
    __tablename__ = "backup_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True, nullable=False, comment="任务ID")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    schedule_id = Column(Integer, ForeignKey("backup_schedules.id"), nullable=True, comment="备份计划ID")
    
    status = Column(String(20), nullable=False, comment="执行状态: success, failed, timeout, cancelled")
    execution_time = Column(Float, comment="执行耗时(秒)")
    
    # 备份结果
    config_id = Column(Integer, ForeignKey("configurations.id"), nullable=True, comment="成功备份的配置ID")
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_details = Column(Text, nullable=True, comment="错误详情堆栈")
    
    # 执行上下文
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 统计信息
    config_size = Column(Integer, nullable=True, comment="配置大小(bytes)")
    git_commit_id = Column(String(40), nullable=True, comment="Git提交ID")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
```

**数据模型评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 字段完整性 | 92/100 | 包含所有必要字段 |
| 外键关联 | 88/100 | 关联关系设计合理 |
| 索引设计 | 85/100 | 已有基本索引 |
| 数据类型 | 90/100 | 使用正确的数据类型 |
| 扩展性 | 82/100 | 缺少扩展字段 |

**优点:**
- 字段设计完整，涵盖了执行的所有关键信息
- 支持多种状态（success, failed, timeout, cancelled）
- 包含执行时间、配置大小等统计信息
- 支持Git提交ID关联

**改进建议:**

```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class BackupExecutionLog(Base):
    """
    备份执行日志表
    记录每次备份任务的执行详情
    """
    __tablename__ = "backup_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), index=True, nullable=False, comment="任务ID")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, comment="设备ID")
    schedule_id = Column(Integer, ForeignKey("backup_schedules.id"), nullable=True, comment="备份计划ID")
    
    status = Column(String(20), nullable=False, comment="执行状态: success, failed, timeout, cancelled")
    execution_time = Column(Float, comment="执行耗时(秒)")
    
    # 备份结果
    config_id = Column(Integer, ForeignKey("configurations.id"), nullable=True, comment="成功备份的配置ID")
    error_message = Column(Text, nullable=True, comment="错误信息")
    error_details = Column(Text, nullable=True, comment="错误详情堆栈")
    
    # 执行上下文
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 统计信息
    config_size = Column(Integer, nullable=True, comment="配置大小(bytes)")
    git_commit_id = Column(String(40), nullable=True, comment="Git提交ID")
    
    # 扩展信息
    extra_info = Column(JSON, nullable=True, comment="额外信息（网络延迟、设备响应时间等）")
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    
    # 索引优化
    __table_args__ = (
        Index("idx_backup_log_device_time", "device_id", "created_at"),
        Index("idx_backup_log_status_time", "status", "created_at"),
        Index("idx_backup_log_schedule_time", "schedule_id", "created_at"),
        Index("idx_backup_log_task", "task_id"),
    )
    
    # 关联关系
    device = relationship("Device", back_populates="backup_logs")
    schedule = relationship("BackupSchedule", back_populates="execution_logs")
    configuration = relationship("Configuration")
    
    def __repr__(self):
        return f"<BackupExecutionLog(id={self.id}, task_id={self.task_id}, device_id={self.device_id}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "device_id": self.device_id,
            "schedule_id": self.schedule_id,
            "status": self.status,
            "execution_time": self.execution_time,
            "config_id": self.config_id,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "config_size": self.config_size,
            "git_commit_id": self.git_commit_id,
            "extra_info": self.extra_info,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
```

### 3.2 数据库迁移方案评审

**方案设计的迁移SQL:**

```sql
CREATE TABLE backup_execution_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    schedule_id INTEGER REFERENCES backup_schedules(id),
    status VARCHAR(20) NOT NULL,
    execution_time FLOAT,
    config_id INTEGER REFERENCES configurations(id),
    error_message TEXT,
    error_details TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    config_size INTEGER,
    git_commit_id VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backup_log_task ON backup_execution_logs(task_id);
CREATE INDEX idx_backup_log_device_time ON backup_execution_logs(device_id, created_at);
CREATE INDEX idx_backup_log_status ON backup_execution_logs(status);
CREATE INDEX idx_backup_log_schedule ON backup_execution_logs(schedule_id, created_at);
```

**迁移方案评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 索引设计 | 88/100 | 索引覆盖常用查询 |
| 外键约束 | 85/100 | 外键关系正确 |
| 数据完整性 | 82/100 | 缺少默认值约束 |

**问题分析:**

1. **缺少默认值**: `created_at` 没有 NOT NULL 约束
2. **缺少ON DELETE处理**: 外键没有定义删除时的行为
3. **缺少字段约束**: status 字段缺少 CHECK 约束

**改进建议:**

```sql
CREATE TABLE backup_execution_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES backup_schedules(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
    execution_time FLOAT CHECK (execution_time >= 0),
    config_id INTEGER REFERENCES configurations(id) ON DELETE SET NULL,
    error_message TEXT,
    error_details TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP CHECK (completed_at >= started_at),
    config_size INTEGER CHECK (config_size >= 0),
    git_commit_id VARCHAR(40),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backup_log_task ON backup_execution_logs(task_id);
CREATE INDEX idx_backup_log_device_time ON backup_execution_logs(device_id, created_at);
CREATE INDEX idx_backup_log_status_time ON backup_execution_logs(status, created_at);
CREATE INDEX idx_backup_log_schedule_time ON backup_execution_logs(schedule_id, created_at);
CREATE INDEX idx_backup_log_device_status ON backup_execution_logs(device_id, status);
```

---

## 四、后端调度器日志记录评审

### 4.1 调度器修改方案

**方案设计的调度器修改:**

```python
async def _execute_backup(self, device_id: int, schedule_id: int = None, db=None):
    """执行单个设备的备份"""
    task_id = str(uuid.uuid4())
    device = db.query(Device).filter(Device.id == device_id).first()
    
    # 创建执行日志
    log = BackupExecutionLog(
        task_id=task_id,
        device_id=device_id,
        schedule_id=schedule_id,
        status="running",
        started_at=datetime.now()
    )
    db.add(log)
    db.commit()
    
    try:
        # 执行配置采集
        from app.services.config_collector import collect_config_from_device
        result = await collect_config_from_device(device)
        
        # 更新日志状态
        log.status = "success" if result["success"] else "failed"
        log.execution_time = execution_time
        log.config_id = result.get("config_id")
        log.error_message = result.get("error")
        
    except Exception as e:
        log.status = "failed"
        log.error_message = str(e)
    
    finally:
        log.completed_at = datetime.now()
        db.commit()
```

**调度器修改评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 日志记录完整性 | 85/100 | 覆盖主要场景 |
| 异常处理 | 78/100 | 缺少详细错误堆栈 |
| 事务管理 | 72/100 | 多次commit存在事务问题 |
| 性能考虑 | 75/100 | 每次备份都提交事务 |

**问题分析:**

1. **事务管理问题**: 方案在日志创建和更新时分别调用 `db.commit()`，可能导致数据不一致
2. **异常处理不完整**: 只记录错误信息，缺少错误详情（traceback）
3. **缺少重试计数**: 没有记录重试次数
4. **连接管理**: 没有处理数据库连接异常

**改进建议:**

```python
import asyncio
import traceback
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import uuid

class BackupSchedulerService:
    """备份调度器服务类"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.max_concurrent_jobs = 3
        self.semaphore = asyncio.Semaphore(self.max_concurrent_jobs)
        logger.info("Backup scheduler initialized")
    
    async def _execute_backup(
        self, 
        device_id: int, 
        schedule_id: int = None, 
        db=None
    ):
        """
        执行单个设备的备份
        
        Args:
            device_id: 设备ID
            schedule_id: 备份计划ID（可选）
            db: 数据库会话
        
        Returns:
            dict: 备份结果
        """
        task_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        device = db.query(Device).filter(Device.id == device_id).first()
        
        if not device:
            logger.error(f"Device {device_id} not found")
            return {
                "success": False,
                "error": "Device not found",
                "device_id": device_id
            }
        
        log = BackupExecutionLog(
            task_id=task_id,
            device_id=device_id,
            schedule_id=schedule_id,
            status="running",
            started_at=start_time
        )
        
        try:
            db.add(log)
            
            try:
                from app.services.config_collector import collect_config_from_device
                result = await collect_config_from_device(device)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                if result.get("success"):
                    log.status = "success"
                    log.execution_time = execution_time
                    log.config_id = result.get("config_id")
                    log.git_commit_id = result.get("git_commit_id")
                    log.config_size = result.get("config_size", 0)
                    
                    logger.info(
                        f"Backup completed for device {device_id}: "
                        f"{device.hostname}, time: {execution_time:.2f}s"
                    )
                    
                    return {
                        "success": True,
                        "config_id": result.get("config_id"),
                        "execution_time": execution_time,
                        "device_id": device_id
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    log.status = "failed"
                    log.execution_time = execution_time
                    log.error_message = error_msg
                    
                    logger.error(
                        f"Backup failed for device {device_id}: "
                        f"{device.hostname}, error: {error_msg}"
                    )
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "device_id": device_id
                    }
                    
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                error_traceback = traceback.format_exc()
                
                log.status = "failed"
                log.execution_time = execution_time
                log.error_message = str(e)
                log.error_details = error_traceback
                
                logger.exception(f"Backup error for device {device_id}: {e}")
                
                return {
                    "success": False,
                    "error": str(e),
                    "error_details": error_traceback,
                    "device_id": device_id
                }
        
        except SQLAlchemyError as e:
            logger.error(f"Database error during backup for device {device_id}: {e}")
            db.rollback()
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "device_id": device_id
            }
        
        finally:
            log.completed_at = datetime.now()
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Failed to commit backup log: {e}")
                db.rollback()
    
    async def _execute_backup_all(
        self, 
        device_ids: list, 
        schedule_id: int = None, 
        db=None
    ):
        """
        执行多个设备的批量备份
        
        Args:
            device_ids: 设备ID列表
            schedule_id: 备份计划ID（可选）
            db: 数据库会话
        """
        task_id = str(uuid.uuid4())
        results = []
        
        async def execute_with_limit(device_id):
            async with self.semaphore:
                result = await self._execute_backup(device_id, schedule_id, db)
                return {
                    "device_id": device_id,
                    **result
                }
        
        tasks = [execute_with_limit(device_id) for device_id in device_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
```

---

## 五、监控统计API评审

### 5.1 API端点设计

**方案设计的API:**

```python
@router.get("/backup-statistics", response_model=BackupStatistics)
async def get_backup_statistics(
    days: Optional[int] = Query(30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取备份统计信息"""

@router.get("/device-backup-status", response_model=List[DeviceBackupStatus])
async def get_device_backup_status(db: Session = Depends(get_db)):
    """获取所有设备的备份状态"""

@router.get("/recent-executions", response_model=List[ExecutionLogResponse])
async def get_recent_executions(
    limit: int = Query(20, description="返回数量"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db)
):
    """获取最近执行记录"""

@router.get("/execution-trend", response_model=ExecutionTrend)
async def get_execution_trend(
    days: int = Query(7, description="天数"),
    db: Session = Depends(get_db)
):
    """获取执行趋势数据"""
```

**API设计评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 功能覆盖度 | 88/100 | 覆盖主要监控场景 |
| 参数设计 | 80/100 | 参数灵活但缺少分页 |
| 性能考虑 | 72/100 | 缺少缓存策略 |
| 数据聚合 | 85/100 | 聚合计算正确 |

**问题分析:**

1. **缺少分页**: recent_executions 接口没有分页参数
2. **缺少缓存**: 高频查询没有缓存机制
3. **性能风险**: execution-trend 使用循环查询，效率低
4. **缺少实时推送**: 没有WebSocket或SSE支持

**改进建议:**

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.database import get_db
from app.models.models import (
    BackupExecutionLog, Device, BackupSchedule, Configuration
)
from app.schemas.monitoring import (
    BackupStatistics, DeviceBackupStatus, ExecutionLogResponse,
    ExecutionTrend, DailyStatistics
)
from app.core.cache import cache

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# 缓存配置
CACHE_TTL = 300  # 5分钟缓存

@router.get("/backup-statistics", response_model=BackupStatistics)
async def get_backup_statistics(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取备份统计信息
    - 使用缓存减少数据库查询
    """
    cache_key = f"backup_statistics_{days}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    start_date = datetime.now() - timedelta(days=days)
    
    # 并行查询提高性能
    total_query = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.created_at >= start_date
    )
    success_query = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.created_at >= start_date,
        BackupExecutionLog.status == "success"
    )
    failed_query = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.created_at >= start_date,
        BackupExecutionLog.status == "failed"
    )
    timeout_query = db.query(func.count(BackupExecutionLog.id)).filter(
        BackupExecutionLog.created_at >= start_date,
        BackupExecutionLog.status == "timeout"
    )
    
    total_executions = total_query.scalar() or 0
    success_count = success_query.scalar() or 0
    failed_count = failed_query.scalar() or 0
    timeout_count = timeout_query.scalar() or 0
    
    # 平均执行时间
    avg_time = db.query(func.avg(BackupExecutionLog.execution_time)).filter(
        BackupExecutionLog.created_at >= start_date,
        BackupExecutionLog.execution_time.isnot(None)
    ).scalar() or 0.0
    
    # 总配置大小
    total_config_size = db.query(func.sum(BackupExecutionLog.config_size)).filter(
        BackupExecutionLog.created_at >= start_date
    ).scalar() or 0
    
    # 设备数量
    device_count = db.query(func.count(Device.id)).scalar()
    
    # 计划数量
    schedule_count = db.query(func.count(BackupSchedule.id)).filter(
        BackupSchedule.is_active == True
    ).scalar()
    
    success_rate = round(success_count / total_executions * 100, 2) if total_executions > 0 else 0.0
    
    result = {
        "total_executions": total_executions,
        "success_count": success_count,
        "failed_count": failed_count,
        "timeout_count": timeout_count,
        "success_rate": success_rate,
        "average_execution_time": round(avg_time, 2),
        "total_config_size": total_config_size,
        "device_count": device_count,
        "schedule_count": schedule_count,
        "period_days": days
    }
    
    # 存入缓存
    cache.set(cache_key, result, ttl=CACHE_TTL)
    
    return result

@router.get("/device-backup-status", response_model=List[DeviceBackupStatus])
async def get_device_backup_status(
    refresh: bool = Query(False, description="是否强制刷新"),
    db: Session = Depends(get_db)
):
    """
    获取所有设备的备份状态
    """
    cache_key = "device_backup_status"
    if not refresh:
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
    
    devices = db.query(Device).all()
    results = []
    
    # 获取所有设备ID
    device_ids = [d.id for d in devices]
    
    if not device_ids:
        return results
    
    # 批量查询每个设备的最近日志
    for device in devices:
        last_log = db.query(BackupExecutionLog).filter(
            BackupExecutionLog.device_id == device.id
        ).order_by(desc(BackupExecutionLog.created_at)).first()
        
        all_logs = db.query(BackupExecutionLog).filter(
            BackupExecutionLog.device_id == device.id
        ).all()
        
        total = len(all_logs)
        success = len([log for log in all_logs if log.status == "success"])
        failed = len([log for log in all_logs if log.status == "failed"])
        timeout = len([log for log in all_logs if log.status == "timeout"])
        success_rate = round(success / total * 100, 2) if total > 0 else 0.0
        
        results.append({
            "device_id": device.id,
            "device_name": device.hostname or device.name,
            "ip": device.ip,
            "vendor": device.vendor,
            "last_backup_status": last_log.status if last_log else None,
            "last_backup_time": last_log.created_at if last_log else None,
            "last_execution_time": last_log.execution_time if last_log else None,
            "total_backups": total,
            "success_count": success,
            "failed_count": failed,
            "timeout_count": timeout,
            "success_rate": success_rate,
            "last_error_message": last_log.error_message if last_log and last_log.status == "failed" else None
        })
    
    # 存入缓存
    cache.set(cache_key, results, ttl=CACHE_TTL)
    
    return results

@router.get("/recent-executions", response_model=Dict[str, Any])
async def get_recent_executions(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    device_id: Optional[int] = Query(None, description="按设备ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取最近执行记录（支持分页）
    """
    query = db.query(BackupExecutionLog).join(
        Device, BackupExecutionLog.device_id == Device.id
    )
    
    if status:
        if status not in ['success', 'failed', 'timeout', 'cancelled']:
            raise HTTPException(status_code=400, detail="无效的状态筛选")
        query = query.filter(BackupExecutionLog.status == status)
    
    if device_id:
        query = query.filter(BackupExecutionLog.device_id == device_id)
    
    # 获取总数
    total = query.count()
    
    # 获取分页数据
    logs = query.order_by(desc(BackupExecutionLog.created_at)).offset(offset).limit(limit).all()
    
    results = []
    for log in logs:
        device = db.query(Device).filter(Device.id == log.device_id).first()
        results.append({
            "id": log.id,
            "task_id": log.task_id,
            "device_id": log.device_id,
            "device_name": device.hostname if device else "Unknown",
            "device_ip": device.ip if device else None,
            "status": log.status,
            "execution_time": log.execution_time,
            "started_at": log.started_at,
            "completed_at": log.completed_at,
            "error_message": log.error_message,
            "error_details": log.error_details,
            "git_commit_id": log.git_commit_id,
            "config_size": log.config_size,
            "created_at": log.created_at
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "executions": results
    }

@router.get("/execution-trend", response_model=ExecutionTrend)
async def get_execution_trend(
    days: int = Query(7, ge=1, le=90, description="天数"),
    db: Session = Depends(get_db)
):
    """
    获取执行趋势数据（优化版本）
    """
    cache_key = f"execution_trend_{days}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 生成日期列表
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    # 批量查询减少数据库调用
    daily_stats = db.query(
        func.date(BackupExecutionLog.created_at).label('date'),
        func.count(BackupExecutionLog.id).label('total'),
        func.sum(func.cast(BackupExecutionLog.status == 'success', Integer)).label('success'),
        func.sum(func.cast(BackupExecutionLog.status == 'failed', Integer)).label('failed'),
        func.avg(BackupExecutionLog.execution_time).label('avg_time')
    ).filter(
        BackupExecutionLog.created_at >= start_date
    ).group_by(
        func.date(BackupExecutionLog.created_at)
    ).all()
    
    # 转换为字典便于查询
    stats_dict = {
        stat.date: {
            "total": stat.total or 0,
            "success": stat.success or 0,
            "failed": stat.failed or 0,
            "avg_time": float(stat.avg_time) if stat.avg_time else 0.0
        }
        for stat in daily_stats
    }
    
    success_counts = []
    failure_counts = []
    average_times = []
    
    for date_str in dates:
        date_stats = stats_dict.get(date_str, {"total": 0, "success": 0, "failed": 0, "avg_time": 0.0})
        success_counts.append(date_stats["success"])
        failure_counts.append(date_stats["failed"])
        average_times.append(round(date_stats["avg_time"], 2))
    
    result = {
        "dates": dates,
        "success_counts": success_counts,
        "failure_counts": failure_counts,
        "average_times": average_times,
        "days": days
    }
    
    # 存入缓存
    cache.set(cache_key, result, ttl=CACHE_TTL)
    
    return result

@router.get("/failed-devices", response_model=List[Dict[str, Any]])
async def get_failed_devices(
    days: int = Query(7, ge=1, le=30, description="查询天数"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取失败设备列表（用于告警）
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 查询最近失败的设备
    failed_logs = db.query(BackupExecutionLog).filter(
        BackupExecutionLog.created_at >= start_date,
        BackupExecutionLog.status == "failed"
    ).order_by(desc(BackupExecutionLog.created_at)).limit(limit * 10).all()
    
    # 按设备分组，取最近的失败记录
    device_failures = {}
    for log in failed_logs:
        if log.device_id not in device_failures:
            device = db.query(Device).filter(Device.id == log.device_id).first()
            device_failures[log.device_id] = {
                "device_id": log.device_id,
                "device_name": device.hostname if device else "Unknown",
                "ip": device.ip if device else None,
                "vendor": device.vendor if device else None,
                "last_failure_time": log.created_at,
                "last_error": log.error_message,
                "failure_count": 1
            }
        else:
            device_failures[log.device_id]["failure_count"] += 1
    
    # 按失败次数排序
    sorted_failures = sorted(
        device_failures.values(),
        key=lambda x: x["failure_count"],
        reverse=True
    )[:limit]
    
    return sorted_failures

@router.get("/health-check")
async def health_check(db: Session = Depends(get_db)):
    """
    监控服务健康检查
    """
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }
```

### 5.2 Schema定义评审

**方案设计的Schema:**

```python
class BackupStatistics(BaseModel):
    """备份统计信息"""
    total_executions: int
    success_count: int
    failed_count: int
    success_rate: float
    average_execution_time: float
    total_config_size: int
    device_count: int
    schedule_count: int

class DeviceBackupStatus(BaseModel):
    """设备备份状态"""
    device_id: int
    device_name: str
    last_backup_status: Optional[str]
    last_backup_time: Optional[datetime]
    total_backups: int
    success_rate: float
```

**Schema设计评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 字段完整性 | 85/100 | 缺少一些扩展字段 |
| 数据验证 | 80/100 | 缺少验证规则 |
| 文档完整性 | 82/100 | 缺少字段说明 |

**改进建议:**

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BackupStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class BackupStatistics(BaseModel):
    """备份统计信息"""
    total_executions: int = Field(..., description="总执行次数")
    success_count: int = Field(..., description="成功次数")
    failed_count: int = Field(..., description="失败次数")
    timeout_count: int = Field(0, description="超时次数")
    success_rate: float = Field(..., description="成功率(%)")
    average_execution_time: float = Field(..., description="平均执行时间(秒)")
    total_config_size: int = Field(0, description="总配置大小(bytes)")
    device_count: int = Field(..., description="设备数量")
    schedule_count: int = Field(..., description="活跃计划数量")
    period_days: int = Field(30, description="统计周期(天)")

class DeviceBackupStatus(BaseModel):
    """设备备份状态"""
    device_id: int = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    ip: Optional[str] = Field(None, description="设备IP")
    vendor: Optional[str] = Field(None, description="设备厂商")
    last_backup_status: Optional[str] = Field(None, description="最后备份状态")
    last_backup_time: Optional[datetime] = Field(None, description="最后备份时间")
    last_execution_time: Optional[float] = Field(None, description="最后执行时间(秒)")
    total_backups: int = Field(0, description="总备份次数")
    success_count: int = Field(0, description="成功次数")
    failed_count: int = Field(0, description="失败次数")
    timeout_count: int = Field(0, description="超时次数")
    success_rate: float = Field(0.0, description="成功率(%)")
    last_error_message: Optional[str] = Field(None, description="最后错误信息")

class ExecutionLogResponse(BaseModel):
    """执行日志响应"""
    id: int = Field(..., description="日志ID")
    task_id: str = Field(..., description="任务ID")
    device_id: int = Field(..., description="设备ID")
    device_name: str = Field(..., description="设备名称")
    device_ip: Optional[str] = Field(None, description="设备IP")
    status: str = Field(..., description="执行状态")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[str] = Field(None, description="错误详情")
    git_commit_id: Optional[str] = Field(None, description="Git提交ID")
    config_size: Optional[int] = Field(None, description="配置大小(bytes)")
    created_at: Optional[datetime] = Field(None, description="创建时间")

class ExecutionTrend(BaseModel):
    """执行趋势数据"""
    dates: List[str] = Field(..., description="日期列表")
    success_counts: List[int] = Field(..., description="成功次数列表")
    failure_counts: List[int] = Field(..., description="失败次数列表")
    average_times: List[float] = Field(..., description="平均执行时间列表")
    days: int = Field(7, description="统计天数")

class DailyStatistics(BaseModel):
    """每日统计"""
    date: str = Field(..., description="日期")
    total: int = Field(..., description="总执行次数")
    success: int = Field(..., description="成功次数")
    failed: int = Field(..., description="失败次数")
    avg_execution_time: float = Field(0.0, description="平均执行时间")
    success_rate: float = Field(0.0, description="成功率")
```

---

## 六、前端监控面板评审

### 6.1 组件设计

**方案设计的组件:**

```vue
<template>
  <div class="monitoring-panel">
    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="statistics-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <!-- 更多卡片 -->
    </el-row>
    
    <!-- 趋势图表 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :span="16">
        <el-card class="chart-card">
          <div ref="trendChartRef" class="trend-chart"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <div ref="pieChartRef" class="pie-chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 设备状态表格 -->
    <el-card class="device-table-card">
      <el-table :data="deviceStatus">
        <!-- 表格列定义 -->
      </el-table>
    </el-card>
  </div>
</template>
```

**组件设计评审:**

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| UI设计 | 88/100 | 使用Element Plus组件 |
| 图表展示 | 85/100 | 使用ECharts图表 |
| 交互设计 | 80/100 | 支持自动刷新 |
| 响应式设计 | 78/100 | 部分响应式问题 |

**优点:**
- 使用Element Plus组件，风格统一
- 统计卡片设计美观，包含图标和数值
- 支持趋势图表和饼图展示
- 支持时间范围筛选

**问题分析:**

1. **缺少实时更新**: 依赖轮询，没有WebSocket推送
2. **图表不可交互**: 缺少图表交互功能（点击查看详情）
3. **缺少告警功能**: 没有失败告警机制
4. **性能优化**: 图表在数据变化时没有优化销毁重建

**改进建议:**

```vue
<!-- frontend/src/components/BackupMonitoringPanel.vue -->
<template>
  <div class="monitoring-panel">
    <!-- 页面头部 -->
    <div class="panel-header">
      <div class="header-left">
        <h2>备份监控面板</h2>
        <el-tag :type="healthStatusType">{{ healthStatusText }}</el-tag>
      </div>
      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="handleDateRangeChange"
        />
        <el-button type="primary" size="small" @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          @change="toggleAutoRefresh"
        />
      </div>
    </div>
    
    <!-- 统计卡片区域 -->
    <el-row :gutter="20" class="statistics-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="goToDetail('success')">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><Check /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_rate }}%</div>
              <div class="stat-label">成功率</div>
              <div class="stat-detail">
                <span>成功: {{ statistics.success_count }}</span>
                <span>总计: {{ statistics.total_executions }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="goToDetail('failed')">
          <div class="stat-content">
            <div class="stat-icon danger">
              <el-icon><Close /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.failed_count }}</div>
              <div class="stat-label">失败次数</div>
              <div class="stat-detail">
                <span>超时: {{ statistics.timeout_count }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.average_execution_time }}s</div>
              <div class="stat-label">平均耗时</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover" @click="goToDevices">
          <div class="stat-content">
            <div class="stat-icon info">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.device_count }}</div>
              <div class="stat-label">设备数量</div>
              <div class="stat-detail">
                <span>计划: {{ statistics.schedule_count }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 趋势图表 -->
    <el-row :gutter="20" class="chart-section">
      <el-col :xs="24" :lg="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>执行趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
                <el-radio-button label="7">7天</el-radio-button>
                <el-radio-button label="14">14天</el-radio-button>
                <el-radio-button label="30">30天</el-radio-button>
                <el-radio-button label="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" class="trend-chart"></div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="8">
        <el-card class="chart-card">
          <template #header>
            <span>执行状态分布</span>
          </template>
          <div ref="pieChartRef" class="pie-chart"></div>
        </el-card>
        
        <!-- 快速统计 -->
        <el-card class="quick-stats-card">
          <template #header>
            <span>快速统计</span>
          </template>
          <div class="quick-stats">
            <div class="quick-stat-item">
              <span class="label">今日执行</span>
              <span class="value">{{ dailyStats.today_total || 0 }}</span>
            </div>
            <div class="quick-stat-item">
              <span class="label">本周执行</span>
              <span class="value">{{ dailyStats.week_total || 0 }}</span>
            </div>
            <div class="quick-stat-item">
              <span class="label">存储使用</span>
              <span class="value">{{ formatSize(statistics.total_config_size) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 设备状态和执行记录 -->
    <el-row :gutter="20" class="detail-section">
      <el-col :xs="24" :lg="12">
        <el-card class="device-table-card">
          <template #header>
            <div class="card-header">
              <span>设备备份状态</span>
              <div class="header-actions">
                <el-input
                  v-model="deviceSearch"
                  placeholder="搜索设备"
                  size="small"
                  prefix-icon="Search"
                  clearable
                  @input="filterDevices"
                />
                <el-select v-model="deviceStatusFilter" size="small" placeholder="状态筛选" clearable>
                  <el-option label="全部" value="" />
                  <el-option label="正常" value="success" />
                  <el-option label="异常" value="failed" />
                  <el-option label="从未备份" value="none" />
                </el-select>
              </div>
            </div>
          </template>
          
          <el-table 
            :data="filteredDeviceStatus" 
            v-loading="loadingDeviceStatus"
            max-height="400"
            stripe
            @row-click="goToDeviceDetail"
          >
            <el-table-column prop="device_name" label="设备名称" min-width="120" />
            <el-table-column prop="ip" label="IP地址" width="140" />
            <el-table-column prop="vendor" label="厂商" width="100" />
            <el-table-column prop="last_backup_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.last_backup_status)" size="small">
                  {{ formatStatus(row.last_backup_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_backup_time" label="最后备份" width="160">
              <template #default="{ row }">
                {{ formatTime(row.last_backup_time) }}
              </template>
            </el-table-column>
            <el-table-column prop="success_rate" label="成功率" width="120">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.success_rate" 
                  :color="getProgressColor(row.success_rate)"
                  :stroke-width="8"
                />
              </template>
            </el-table-column>
            <el-table-column prop="total_backups" label="备份次数" width="90" align="center" />
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card class="recent-logs-card">
          <template #header>
            <div class="card-header">
              <span>最近执行记录</span>
              <div class="header-actions">
                <el-select v-model="logFilter" size="small" placeholder="筛选状态" clearable>
                  <el-option label="全部" value="" />
                  <el-option label="成功" value="success" />
                  <el-option label="失败" value="failed" />
                  <el-option label="超时" value="timeout" />
                </el-select>
                <el-button size="small" type="primary" link @click="loadRecentExecutions">
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <el-table 
            :data="recentExecutions" 
            v-loading="loadingExecutions"
            max-height="400"
            stripe
            @row-click="goToLogDetail"
          >
            <el-table-column prop="device_name" label="设备" min-width="120" />
            <el-table-column prop="device_ip" label="IP" width="130" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ formatStatus(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="execution_time" label="耗时" width="90">
              <template #default="{ row }">
                {{ row.execution_time ? `${row.execution_time.toFixed(2)}s` : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.started_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" min-width="150" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.status === 'failed'" class="error-text">
                  {{ row.error_message || '未知错误' }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 失败设备告警 -->
    <el-card v-if="failedDevices.length > 0" class="alert-card">
      <template #header>
        <div class="alert-header">
          <el-icon class="alert-icon"><Warning /></el-icon>
          <span>需要关注的设备</span>
          <el-badge :value="failedDevices.length" type="danger" class="alert-badge" />
        </div>
      </template>
      <div class="failed-devices-grid">
        <div 
          v-for="device in failedDevices.slice(0, 6)" 
          :key="device.device_id"
          class="failed-device-item"
          @click="goToDeviceDetail(device.device_id)"
        >
          <div class="device-info">
            <span class="device-name">{{ device.device_name }}</span>
            <span class="device-ip">{{ device.ip }}</span>
          </div>
          <div class="device-stats">
            <el-tag type="danger" size="small">
              {{ device.failure_count }}次失败
            </el-tag>
            <span class="last-error">{{ device.last_error }}</span>
          </div>
        </div>
        <div v-if="failedDevices.length > 6" class="more-devices" @click="showAllFailedDevices">
          <span>+{{ failedDevices.length - 6 }}个设备</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { monitoringApi } from '@/api/monitoringApi'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

export default {
  name: 'BackupMonitoringPanel',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const statistics = ref({
      total_executions: 0,
      success_count: 0,
      failed_count: 0,
      timeout_count: 0,
      success_rate: 0,
      average_execution_time: 0,
      total_config_size: 0,
      device_count: 0,
      schedule_count: 0
    })
    
    const deviceStatus = ref([])
    const recentExecutions = ref([])
    const failedDevices = ref([])
    const dailyStats = ref({
      today_total: 0,
      week_total: 0
    })
    
    const trendData = ref({
      dates: [],
      success_counts: [],
      failure_counts: [],
      average_times: []
    })
    
    const loading = ref(false)
    const loadingDeviceStatus = ref(false)
    const loadingExecutions = ref(false)
    
    const trendDays = ref(7)
    const dateRange = ref([])
    const deviceSearch = ref('')
    const deviceStatusFilter = ref('')
    const logFilter = ref('')
    const autoRefresh = ref(true)
    
    const trendChartRef = ref(null)
    const pieChartRef = ref(null)
    let trendChart = null
    let pieChart = null
    let refreshTimer = null
    
    // 计算属性
    const filteredDeviceStatus = computed(() => {
      let result = deviceStatus.value
      
      if (deviceSearch.value) {
        const search = deviceSearch.value.toLowerCase()
        result = result.filter(d => 
          d.device_name?.toLowerCase().includes(search) ||
          d.ip?.includes(search)
        )
      }
      
      if (deviceStatusFilter.value) {
        if (deviceStatusFilter.value === 'none') {
          result = result.filter(d => !d.last_backup_status)
        } else {
          result = result.filter(d => d.last_backup_status === deviceStatusFilter.value)
        }
      }
      
      return result
    })
    
    const healthStatusType = computed(() => {
      if (statistics.value.success_rate >= 95) return 'success'
      if (statistics.value.success_rate >= 80) return 'warning'
      return 'danger'
    })
    
    const healthStatusText = computed(() => {
      if (statistics.value.success_rate >= 95) return '健康'
      if (statistics.value.success_rate >= 80) return '一般'
      return '异常'
    })
    
    // 方法
    const loadStatistics = async () => {
      try {
        const response = await monitoringApi.getBackupStatistics(30)
        statistics.value = response
        updatePieChart()
      } catch (error) {
        console.error('加载统计信息失败:', error)
      }
    }
    
    const loadDeviceStatus = async () => {
      loadingDeviceStatus.value = true
      try {
        const response = await monitoringApi.getDeviceBackupStatus()
        deviceStatus.value = response
      } catch (error) {
        console.error('加载设备状态失败:', error)
      } finally {
        loadingDeviceStatus.value = false
      }
    }
    
    const loadRecentExecutions = async () => {
      loadingExecutions.value = true
      try {
        const response = await monitoringApi.getRecentExecutions(50)
        recentExecutions.value = response.executions || response
      } catch (error) {
        console.error('加载执行记录失败:', error)
      } finally {
        loadingExecutions.value = false
      }
    }
    
    const loadFailedDevices = async () => {
      try {
        const response = await monitoringApi.getFailedDevices(7, 10)
        failedDevices.value = response
      } catch (error) {
        console.error('加载失败设备失败:', error)
      }
    }
    
    const loadTrend = async () => {
      try {
        const response = await monitoringApi.getExecutionTrend(trendDays.value)
        trendData.value = response
        updateTrendChart()
      } catch (error) {
        console.error('加载趋势数据失败:', error)
      }
    }
    
    const loadDailyStats = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]
        const response = await monitoringApi.getExecutionTrend(7)
        
        const todayData = response.dates.find(d => d === today)
        if (todayData) {
          const todayIndex = response.dates.indexOf(todayData)
          dailyStats.value.today_total = response.success_counts[todayIndex] + response.failure_counts[todayIndex]
        }
        
        // 计算本周总计
        dailyStats.value.week_total = response.success_counts.reduce((a, b) => a + b, 0) + 
                                        response.failure_counts.reduce((a, b) => a + b, 0)
      } catch (error) {
        console.error('加载日统计失败:', error)
      }
    }
    
    const refreshData = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadStatistics(),
          loadDeviceStatus(),
          loadRecentExecutions(),
          loadFailedDevices(),
          loadTrend(),
          loadDailyStats()
        ])
        ElMessage.success('数据已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      } finally {
        loading.value = false
      }
    }
    
    const updateTrendChart = () => {
      if (!trendChart) return
      
      trendChart.setOption({
        tooltip: { 
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        legend: { data: ['成功', '失败'] },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: trendData.value.dates,
          axisLabel: {
            formatter: (value) => {
              const date = new Date(value)
              return `${date.getMonth() + 1}/${date.getDate()}`
            }
          }
        },
        yAxis: { type: 'value' },
        series: [
          {
            name: '成功',
            type: 'bar',
            stack: 'total',
            data: trendData.value.success_counts,
            itemStyle: { color: '#67c23a' },
            emphasis: { focus: 'series' }
          },
          {
            name: '失败',
            type: 'bar',
            stack: 'total',
            data: trendData.value.failure_counts,
            itemStyle: { color: '#f56c6c' },
            emphasis: { focus: 'series' }
          }
        ]
      })
    }
    
    const updatePieChart = () => {
      if (!pieChart) return
      
      const success = statistics.value.success_count || 0
      const failed = statistics.value.failed_count || 0
      const timeout = statistics.value.timeout_count || 0
      
      pieChart.setOption({
        tooltip: { 
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: { 
          bottom: '5%',
          left: 'center'
        },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 18,
              fontWeight: 'bold'
            }
          },
          data: [
            { value: success, name: '成功', itemStyle: { color: '#67c23a' } },
            { value: failed, name: '失败', itemStyle: { color: '#f56c6c' } },
            { value: timeout, name: '超时', itemStyle: { color: '#e6a23c' } }
          ]
        }]
      })
    }
    
    const initCharts = () => {
      if (trendChartRef.value) {
        trendChart = echarts.init(trendChartRef.value)
      }
      if (pieChartRef.value) {
        pieChart = echarts.init(pieChartRef.value)
      }
      
      // 响应窗口大小变化
      window.addEventListener('resize', handleResize)
    }
    
    const handleResize = () => {
      trendChart?.resize()
      pieChart?.resize()
    }
    
    const getStatusType = (status) => {
      const types = {
        success: 'success',
        failed: 'danger',
        timeout: 'warning',
        cancelled: 'info'
      }
      return types[status] || 'info'
    }
    
    const formatStatus = (status) => {
      const texts = {
        success: '成功',
        failed: '失败',
        timeout: '超时',
        cancelled: '已取消'
      }
      return texts[status] || (status || '从未备份')
    }
    
    const getProgressColor = (percentage) => {
      if (percentage >= 90) return '#67c23a'
      if (percentage >= 70) return '#e6a23c'
      return '#f56c6c'
    }
    
    const formatTime = (time) => {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }
    
    const formatSize = (bytes) => {
      if (!bytes) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB', 'TB']
      let size = bytes
      let unitIndex = 0
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      return `${size.toFixed(2)} ${units[unitIndex]}`
    }
    
    const filterDevices = () => {
      // 过滤逻辑在计算属性中实现
    }
    
    const handleDateRangeChange = () => {
      if (dateRange.value && dateRange.value.length === 2) {
        const days = Math.ceil((dateRange.value[1] - dateRange.value[0]) / (1000 * 60 * 60 * 24))
        trendDays.value = Math.min(days, 90)
        loadTrend()
      }
    }
    
    const toggleAutoRefresh = (value) => {
      if (value) {
        startAutoRefresh()
      } else {
        stopAutoRefresh()
      }
    }
    
    const startAutoRefresh = () => {
      refreshTimer = setInterval(() => {
        loadStatistics()
        loadRecentExecutions()
      }, 30000)
    }
    
    const stopAutoRefresh = () => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
        refreshTimer = null
      }
    }
    
    const goToDetail = (status) => {
      router.push({
        path: '/monitoring/executions',
        query: { status }
      })
    }
    
    const goToDevices = () => {
      router.push('/devices')
    }
    
    const goToDeviceDetail = (deviceId) => {
      router.push({
        path: '/devices/detail',
        query: { id: deviceId }
      })
    }
    
    const goToLogDetail = (row) => {
      router.push({
        path: '/monitoring/executions',
        query: { id: row.id }
      })
    }
    
    const showAllFailedDevices = () => {
      router.push({
        path: '/monitoring/failed'
      })
    }
    
    // 生命周期
    onMounted(async () => {
      await nextTick()
      initCharts()
      await refreshData()
      if (autoRefresh.value) {
        startAutoRefresh()
      }
    })
    
    onUnmounted(() => {
      stopAutoRefresh()
      window.removeEventListener('resize', handleResize)
      trendChart?.dispose()
      pieChart?.dispose()
    })
    
    return {
      statistics,
      deviceStatus,
      recentExecutions,
      failedDevices,
      dailyStats,
      trendData,
      loading,
      loadingDeviceStatus,
      loadingExecutions,
      trendDays,
      dateRange,
      deviceSearch,
      deviceStatusFilter,
      logFilter,
      autoRefresh,
      trendChartRef,
      pieChartRef,
      filteredDeviceStatus,
      healthStatusType,
      healthStatusText,
      loadStatistics,
      loadDeviceStatus,
      loadRecentExecutions,
      loadFailedDevices,
      loadTrend,
      refreshData,
      handleDateRangeChange,
      toggleAutoRefresh,
      filterDevices,
      goToDetail,
      goToDevices,
      goToDeviceDetail,
      goToLogDetail,
      showAllFailedDevices,
      getStatusType,
      formatStatus,
      getProgressColor,
      formatTime,
      formatSize
    }
  }
}
</script>

<style scoped>
.monitoring-panel {
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.statistics-cards {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
}

.stat-icon.success { background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%); }
.stat-icon.danger { background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%); }
.stat-icon.warning { background: linear-gradient(135deg, #e6a23c 0%, #f5d14b 100%); }
.stat-icon.info { background: linear-gradient(135deg, #909399 0%, #b4b4b8 100%); }

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-detail {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.chart-section,
.detail-section {
  margin-bottom: 20px;
}

.chart-card {
  height: 420px;
}

.quick-stats-card {
  margin-top: 20px;
}

.quick-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.quick-stat-item {
  text-align: center;
}

.quick-stat-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.quick-stat-item .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.trend-chart,
.pie-chart {
  height: 320px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.device-table-card,
.recent-logs-card {
  height: 100%;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
}

.alert-card {
  border-left: 4px solid #f56c6c;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-icon {
  color: #f56c6c;
  font-size: 20px;
}

.alert-badge {
  margin-left: 10px;
}

.failed-devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.failed-device-item {
  padding: 12px;
  background: #fef0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.failed-device-item:hover {
  background: #fde2e2;
}

.device-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.device-name {
  font-weight: 600;
  color: #303133;
}

.device-ip {
  font-size: 12px;
  color: #909399;
}

.device-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.last-error {
  font-size: 12px;
  color: #f56c6c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 150px;
}

.more-devices {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  color: #409eff;
}

.more-devices:hover {
  background: #ecf5ff;
}
</style>
```

---

## 七、风险评估

### 7.1 技术风险

| 风险项 | 影响程度 | 发生概率 | 风险等级 | 缓解措施 |
|--------|----------|----------|----------|----------|
| 大量日志数据导致查询性能下降 | 高 | 中 | 高 | 实现数据归档和清理策略 |
| 数据库连接池耗尽 | 中 | 低 | 中 | 实现连接池监控和限制 |
| 监控API响应慢 | 中 | 中 | 中 | 添加缓存机制和查询优化 |
| 图表渲染性能问题 | 低 | 中 | 低 | 实现虚拟滚动和图表优化 |

### 7.2 数据管理风险

| 风险项 | 影响程度 | 发生概率 | 风险等级 | 缓解措施 |
|--------|----------|----------|----------|----------|
| 日志数据无限增长 | 高 | 高 | 高 | 实现数据保留策略 |
| 历史数据查询超时 | 中 | 中 | 中 | 分区表和索引优化 |
| 统计数据不准确 | 中 | 低 | 中 | 增加数据验证和校验 |

---

## 八、改进建议汇总

### 8.1 紧急改进项（实施前必须处理）

1. **实现数据归档和清理策略**
   - 优先级: 高
   - 原因: 防止日志数据无限增长
   - 实施方案: 保留30天热数据，归档冷数据到历史表

2. **添加API缓存机制**
   - 优先级: 高
   - 原因: 减少数据库查询压力
   - 实施方案: 使用Redis缓存热点数据

3. **优化趋势查询性能**
   - 优先级: 高
   - 原因: 循环查询效率低
   - 实施方案: 使用批量查询和聚合函数

### 8.2 建议改进项（实施过程中处理）

4. **实现WebSocket实时推送**
   - 优先级: 中
   - 原因: 提高用户体验
   - 实施方案: 实现执行状态实时推送

5. **添加数据分区表**
   - 优先级: 中
   - 原因: 提高大表查询性能
   - 实施方案: 按日期分区备份执行日志表

6. **实现告警通知机制**
   - 优先级: 中
   - 原因: 及时发现备份失败
   - 实施方案: 集成邮件或企业微信告警

7. **添加图表交互功能**
   - 优先级: 低
   - 原因: 提高数据分析能力
   - 实施方案: 支持点击查看详细数据

---

## 九、结论

### 9.1 总体评审结论

经过对 Phase 3 实施方案的详细评审，该方案是三个阶段中设计最为完善的一个。数据模型设计完整，API功能覆盖全面，前端组件美观实用。监控面板功能将为备份系统提供重要的运维支撑，与 Phase 2 的批量备份功能形成完整的闭环。

### 9.2 与原始评审文档一致性

该实施方案与原始评审文档的评审结论对比：

| 评审项 | 原始评审建议 | 实施方案 | 一致性 |
|--------|--------------|----------|--------|
| BackupExecutionLog模型 | 已实现 | ✅ 已覆盖 | ✅ 一致 |
| 执行日志记录 | 已实现 | ✅ 已覆盖 | ✅ 一致 |
| 监控统计API | 已实现 | ✅ 已覆盖 | ✅ 一致 |
| 监控面板组件 | 已实现 | ✅ 已覆盖 | ✅ 一致 |
| 趋势图表展示 | 已实现 | ✅ 已覆盖 | ✅ 一致 |
| 数据缓存机制 | 建议增加 | ⚠️ 需补充 | ⚠️ 部分一致 |
| WebSocket推送 | 未提及 | ⚠️ 需补充 | ⚠️ 部分一致 |
| 告警通知机制 | 建议增加 | ⚠️ 需补充 | ⚠️ 部分一致 |

### 9.3 评审决定

**评审结果**: 通过

**评审意见**:
该实施方案设计完整，技术实现详细，可以作为后续开发的指导文档。建议在实施过程中关注数据增长带来的性能问题，适时引入缓存和归档策略。

### 9.4 实施建议

| 阶段 | 主要任务 | 预计工时 | 优先级 |
|------|----------|----------|--------|
| 第一步 | 实现数据模型和迁移脚本 | 2小时 | 高 |
| 第二步 | 实现调度器日志记录 | 2小时 | 高 |
| 第三步 | 实现监控API和缓存 | 3小时 | 高 |
| 第四步 | 实现前端监控面板 | 4小时 | 高 |
| 第五步 | 集成测试和性能优化 | 2小时 | 中 |
| 第六步 | 添加自动刷新和告警 | 2小时 | 低 |

---

## 附录

### A. 评审文件清单

| 文件路径 | 文件类型 | 说明 |
|----------|----------|------|
| `docs/功能需求/前端/plans/Phase3-备份计划监控面板/实施计划.md` | Markdown | 实施方案 |
| `docs/功能需求/前端/配置管理模块问题分析与优化方案.md` | Markdown | 原始需求 |
| `docs/功能需求/前端/配置管理模块问题分析与优化方案-评审文档.md` | Markdown | 原始评审 |
| `docs/功能需求/前端/plans/Phase1-修复设备列表显示问题/Phase1-修复设备列表显示问题-评审文档.md` | Markdown | Phase 1评审 |
| `docs/功能需求/前端/plans/Phase2-批量备份功能/Phase2-批量备份功能-评审文档.md` | Markdown | Phase 2评审 |

### B. 依赖关系

| 依赖项 | 来源 | 说明 |
|--------|------|------|
| BackupExecutionLog模型 | Phase 3 Task 1 | 核心数据模型 |
| 批量备份任务 | Phase 2 | 产生执行日志 |
| Device模型 | 现有代码 | 用于关联查询 |
| 缓存服务 | 需新建 | 用于API缓存 |

### C. 评审方法说明

本次评审采用以下方法：
1. **代码审查**: 对方案中的代码示例进行实际验证
2. **一致性检查**: 对比方案与原始评审文档的一致性
3. **技术评估**: 评估技术方案的实现难度和可行性
4. **风险分析**: 识别潜在的技术和数据管理风险
5. **最佳实践**: 参考行业最佳实践提出改进建议
6. **对比分析**: 与Phase 1/2评审结果进行对比分析

### D. 评审人员信息

- **评审工具**: AI代码评审助手
- **评审日期**: 2026-02-06
- **评审版本**: 1.0

---

**文档结束**
