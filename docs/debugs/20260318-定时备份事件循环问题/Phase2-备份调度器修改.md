
# Phase2 - 备份调度器修改

## 概述
修改 `_execute_backup()` 方法，使用 `asyncio.run_coroutine_threadsafe()` 将异步备份任务提交到主事件循环执行。

## 变更文件
- `app/services/backup_scheduler.py`

## 设计详情

### 1. 导入主事件循环获取函数
在文件顶部添加导入：
```python
from app.main import get_main_event_loop
```

### 2. 修改 `_execute_backup()` 方法
将 `asyncio.run()` 替换为 `asyncio.run_coroutine_threadsafe()`：

**修改前：**
```python
result = asyncio.run(
    backup_service.execute_scheduled_backup(device_id, db, task_id)
)
```

**修改后：**
```python
try:
    main_loop = get_main_event_loop()
    logger.info(f"[ScheduledBackup] Submitting coroutine to main loop: {main_loop}")
    
    future = asyncio.run_coroutine_threadsafe(
        backup_service.execute_scheduled_backup(device_id, db, task_id),
        main_loop
    )
    
    result = future.result(timeout=300)
    logger.info(f"[ScheduledBackup] Coroutine completed with result: {result}")
    
except RuntimeError as e:
    logger.error(f"[ScheduledBackup] Failed to get main event loop: {e}")
    raise
except concurrent.futures.TimeoutError:
    logger.error(f"[ScheduledBackup] Coroutine execution timed out after 300 seconds")
    future.cancel()
    raise
except Exception as e:
    logger.error(f"[ScheduledBackup] Coroutine execution failed: {e}")
    raise
```

### 3. 添加 concurrent.futures 导入
在文件顶部添加：
```python
import concurrent.futures
```

## 执行流程说明

```
APScheduler 后台线程
    ↓
_execute_backup(device_id)
    ↓
获取 main_loop (get_main_event_loop())
    ↓
asyncio.run_coroutine_threadsafe(coro, main_loop)
    ↓
[主事件循环中执行] execute_scheduled_backup()
    ↓
future.result() 等待结果
    ↓
返回 result
```

## 验证要点
- 定时备份不再报 "Future attached to a different loop" 错误
- 日志显示 "Submitting coroutine to main loop"
- 备份任务正常执行，成功率提升到 95%+

