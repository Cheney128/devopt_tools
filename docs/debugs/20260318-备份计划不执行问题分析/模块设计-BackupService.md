
# BackupService 模块详细设计

**设计日期**：2026-03-18  
**所属文档**：[设计细化文档.md](./设计细化文档.md)

---

## 1. 模块概述

BackupService 是一个独立的服务类，封装所有备份相关的核心业务逻辑，将备份逻辑从 API 端点中解耦出来，提高代码的可复用性、可测试性和可维护性。

---

## 2. 职责划分

| 组件 | 职责 |
|------|------|
| BackupService | 备份核心业务逻辑（采集配置、对比、保存、Git提交） |
| API Endpoints | HTTP 请求/响应处理、参数校验、调用 BackupService |
| BackupScheduler | 定时任务调度、调用 BackupService |
| BackupExecutor | 批量备份执行、并发控制、调用 BackupService |

---

## 3. 类设计

### 3.1 类图

```
┌─────────────────────────────────────────┐
│          BackupService                  │
├─────────────────────────────────────────┤
│ - netmiko_service: NetmikoService      │
│ - git_service: GitService               │
├─────────────────────────────────────────┤
│ + __init__()                            │
│ + collect_config(device_id, db)         │
│ + execute_scheduled_backup(...)         │
└─────────────────────────────────────────┘
           │
           │ 使用
           ▼
┌──────────────────┐  ┌──────────────────┐
│  NetmikoService  │  │   GitService     │
└──────────────────┘  └──────────────────┘
```

### 3.2 依赖注入

BackupService 在初始化时创建 NetmikoService 和 GitService 实例，不使用依赖注入，以简化从同步上下文中的调用。

---

## 4. 方法详细设计

### 4.1 `__init__()`

**签名**：
```python
def __init__(self)
```

**功能**：
- 初始化 `netmiko_service` 实例
- 初始化 `git_service` 实例

---

### 4.2 `collect_config(device_id: int, db: Session) -&gt; Dict[str, Any]`

**签名**：
```python
async def collect_config(
    self, 
    device_id: int, 
    db: Session
) -&gt; Dict[str, Any]
```

**功能**：
从设备采集配置，对比最新配置，保存到数据库，提交到 Git（如果配置了 Git）。

**参数**：
- `device_id` - 设备 ID
- `db` - 数据库会话

**返回值**：
```python
{
    "success": bool,              # 是否成功
    "message": str,               # 结果消息
    "config_id": Optional[int],   # 配置记录 ID（如果有新配置）
    "config_changed": bool,       # 配置是否变化
    "config_size": int,           # 配置内容大小（字节）
    "git_commit_id": Optional[str],  # Git 提交 ID（如果有）
    "version": Optional[str]      # 配置版本号（如果有新配置）
}
```

**处理流程**：

```
1. 查询设备信息
   ↓
2. 检查设备是否存在
   ↓ 不存在 → 返回 {success: False, message: "Device not found"}
   ↓ 存在
3. 调用 netmiko_service.collect_running_config() 采集配置
   ↓
4. 检查配置是否为空
   ↓ 为空 → 返回 {success: False, message: "Failed to get config from device"}
   ↓ 不为空
5. 查询设备最新配置
   ↓
6. 对比配置内容
   ↓ 无变化 → 返回 {success: True, config_changed: False, ...}
   ↓ 有变化
7. 生成新版本号
   ↓
8. 创建新 Configuration 记录
   ↓
9. 检查是否有活跃的 Git 配置
   ↓ 有
10. 初始化 Git 仓库
    ↓
11. 提交配置到 Git
    ↓
12. 推送到远程仓库
    ↓
13. 更新 Configuration.git_commit_id
    ↓
14. 保存到数据库
    ↓
15. 返回成功结果
```

**日志记录**：
- `[BackupService] Querying device {device_id}...`
- `[BackupService] Collecting config from device {hostname}...`
- `[BackupService] Config unchanged for device {hostname}`
- `[BackupService] Config changed for device {hostname}, creating new version {version}`
- `[BackupService] Git commit successful: {commit_id}`
- `[BackupService] Config saved successfully, config_id: {config_id}`

---

### 4.3 `execute_scheduled_backup(device_id: int, db: Session, task_id: str) -&gt; Dict[str, Any]`

**签名**：
```python
async def execute_scheduled_backup(
    self, 
    device_id: int, 
    db: Session,
    task_id: str
) -&gt; Dict[str, Any]
```

**功能**：
执行定时备份，调用 `collect_config()`，创建 `BackupExecutionLog`，更新 `BackupSchedule.last_run_time`。

**参数**：
- `device_id` - 设备 ID
- `db` - 数据库会话
- `task_id` - 任务 ID（用于日志记录）

**返回值**：
```python
{
    "success": bool,              # 是否成功
    "message": str,               # 结果消息
    "config_id": Optional[int],   # 配置记录 ID
    "execution_time": float       # 执行时间（秒）
}
```

**处理流程**：

```
1. 记录开始时间
   ↓
2. 调用 collect_config(device_id, db)
   ↓
3. 计算执行时间
   ↓
4. 查询设备的活跃备份计划
   ↓
5. 判断配置是否变化
   ↓
6. 构建错误消息（如果配置无变化）
   ↓
7. 创建 BackupExecutionLog 记录
   ↓
8. 如果备份成功，更新 BackupSchedule.last_run_time
   ↓
9. 提交数据库事务
   ↓
10. 返回结果
```

**日志记录**：
- `[BackupService] Executing scheduled backup, task_id={task_id}`
- `[BackupService] Calling collect_config()...`
- `[BackupService] Config changed: {config_changed}`
- `[BackupService] Creating execution log...`
- `[BackupService] Updating schedule last_run_time...`
- `[BackupService] Scheduled backup completed, success={success}`

---

## 5. 错误处理

| 错误场景 | 处理方式 | 返回值 |
|---------|---------|--------|
| 设备不存在 | 捕获异常，记录日志 | `{success: False, message: "Device not found"}` |
| 配置采集失败 | 捕获异常，记录日志 | `{success: False, message: "Failed to get config from device"}` |
| Git 操作失败 | 捕获异常，记录日志，不影响配置保存 | `{success: True, config_id: xxx}` |
| 数据库操作失败 | 捕获异常，记录日志，回滚事务 | `{success: False, message: "..."}` |

---

## 6. 代码实现模板

```python
"""
备份服务模块
封装所有备份相关的核心逻辑
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Device, Configuration, GitConfig, BackupSchedule, BackupExecutionLog
from app.services.netmiko_service import NetmikoService
from app.services.git_service import GitService

logger = logging.getLogger(__name__)


class BackupService:
    """
    备份服务类，封装所有备份相关的核心逻辑
    """
    
    def __init__(self):
        self.netmiko_service = NetmikoService()
        self.git_service = GitService()
    
    async def collect_config(
        self, 
        device_id: int, 
        db: Session
    ) -&gt; Dict[str, Any]:
        """
        从设备采集配置（核心业务逻辑）
        """
        logger.info(f"[BackupService] Querying device {device_id}...")
        
        # 查询设备信息
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            logger.warning(f"[BackupService] Device {device_id} not found")
            return {"success": False, "message": "Device not found"}
        
        logger.info(f"[BackupService] Collecting config from device {device.hostname}...")
        
        # 从设备获取配置
        config_content = await self.netmiko_service.collect_running_config(device)
        if not config_content:
            logger.warning(f"[BackupService] Failed to get config from device {device.hostname}")
            return {"success": False, "message": "Failed to get config from device"}
        
        # 获取设备最新配置
        latest_config = db.query(Configuration).filter(
            Configuration.device_id == device_id
        ).order_by(Configuration.config_time.desc()).first()
        
        # 检查配置是否有变化
        if latest_config and latest_config.config_content == config_content:
            logger.info(f"[BackupService] Config unchanged for device {device.hostname}")
            return {
                "success": True,
                "message": "配置无变化，已成功登录并验证",
                "config_id": latest_config.id,
                "config_changed": False,
                "config_size": len(config_content) if config_content else 0
            }
        
        logger.info(f"[BackupService] Config changed for device {device.hostname}")
        
        # 生成版本号
        new_version = "1.0"
        if latest_config:
            current_version = latest_config.version
            try:
                major, minor = map(int, current_version.split("."))
                new_version = f"{major}.{minor + 1}"
            except:
                new_version = "1.0"
        
        logger.info(f"[BackupService] Creating new version {new_version} for device {device.hostname}")
        
        # 创建新的配置记录
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content,
            version=new_version,
            change_description="Auto-collected from device"
        )
        
        # 检查是否有Git配置，如果有则提交到Git
        git_commit_id = None
        try:
            git_config = db.query(GitConfig).filter(GitConfig.is_active == True).first()
            if git_config:
                logger.info(f"[BackupService] Git config found, committing to Git...")
                from app.services.git_service import GitService
                device_git_service = GitService()
                if device_git_service.init_repo(git_config):
                    commit_id = device_git_service.commit_config(
                        device.hostname,
                        config_content,
                        f"Auto-update config for {device.hostname} at {datetime.now()}"
                    )
                    if commit_id:
                        device_git_service.push_to_remote()
                        git_commit_id = commit_id
                        new_config.git_commit_id = commit_id
                        logger.info(f"[BackupService] Git commit successful: {commit_id}")
                    device_git_service.close()
        except Exception as git_error:
            logger.error(f"[BackupService] Git operation error: {str(git_error)}")
        
        # 保存到数据库
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        logger.info(f"[BackupService] Config saved successfully, config_id: {new_config.id}")
        
        return {
            "success": True,
            "message": "Config collected from device and saved",
            "config_id": new_config.id,
            "config_changed": True,
            "config_size": len(config_content) if config_content else 0,
            "git_commit_id": git_commit_id,
            "version": new_version
        }
    
    async def execute_scheduled_backup(
        self, 
        device_id: int, 
        db: Session,
        task_id: str
    ) -&gt; Dict[str, Any]:
        """
        执行定时备份（包含日志记录）
        """
        logger.info(f"[BackupService] Executing scheduled backup, task_id={task_id}")
        
        started_at = datetime.now()
        execution_log = None
        
        try:
            logger.info(f"[BackupService] Calling collect_config()...")
            result = await self.collect_config(device_id, db)
            
            execution_time = (datetime.now() - started_at).total_seconds()
            
            logger.info(f"[BackupService] Querying backup schedule for device {device_id}...")
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()
            
            config_changed = result.get("config_changed", True)
            logger.info(f"[BackupService] Config changed: {config_changed}")
            
            error_message = None
            if not config_changed:
                error_message = "配置无变化，已成功登录并验证设备配置"
            
            logger.info(f"[BackupService] Creating execution log...")
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="success" if result.get("success") else "failed",
                execution_time=execution_time,
                trigger_type="scheduled",
                config_id=result.get("config_id"),
                config_size=result.get("config_size", 0),
                git_commit_id=result.get("git_commit_id"),
                error_message=error_message if not result.get("success") else None,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)
            
            if schedule and result.get("success"):
                logger.info(f"[BackupService] Updating schedule last_run_time...")
                schedule.last_run_time = datetime.now()
            
            db.commit()
            
            logger.info(f"[BackupService] Scheduled backup completed, success={result.get('success')}")
            
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "config_id": result.get("config_id"),
                "execution_time": execution_time
            }
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"[BackupService] Scheduled backup failed: {error_message}")
            
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()
            
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="failed",
                execution_time=(datetime.now() - started_at).total_seconds(),
                trigger_type="scheduled",
                error_message=error_message,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)
            db.commit()
            
            return {
                "success": False,
                "message": error_message,
                "config_id": None,
                "execution_time": (datetime.now() - started_at).total_seconds()
            }
```

---

## 7. 使用示例

### 7.1 在 API 端点中使用

```python
from app.services.backup_service import BackupService

@router.post("/device/{device_id}/collect")
async def collect_config_from_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    backup_service = BackupService()
    result = await backup_service.collect_config(device_id, db)
    return result
```

### 7.2 在 BackupScheduler 中使用

```python
def _execute_backup(self, device_id: int):
    import asyncio
    from app.models import SessionLocal
    from app.services.backup_service import BackupService
    
    db = SessionLocal()
    try:
        backup_service = BackupService()
        result = asyncio.run(
            backup_service.execute_scheduled_backup(device_id, db, "task_123")
        )
    finally:
        db.close()
```

---

## 8. 测试要点

| 测试场景 | 验证内容 |
|---------|---------|
| 设备不存在 | 返回正确的错误 |
| 配置采集成功 | 返回 success=True |
| 配置无变化 | 返回 config_changed=False |
| 配置有变化 | 创建新配置记录 |
| Git 配置存在 | 提交到 Git |
| Git 操作失败 | 不影响配置保存 |
| 定时备份执行 | 创建执行日志 |

