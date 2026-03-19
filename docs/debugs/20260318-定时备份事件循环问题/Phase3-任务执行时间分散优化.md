
# Phase3 - 任务执行时间分散优化

## 概述
将 hourly 类型的备份任务按设备 ID 分散到不同分钟执行，避免所有任务同时触发造成资源压力。

## 变更文件
- `app/services/backup_scheduler.py`

## 设计详情

### 修改 `_create_trigger()` 方法

**修改前：**
```python
if schedule.schedule_type == "hourly":
    return CronTrigger(minute="0")
```

**修改后：**
```python
if schedule.schedule_type == "hourly":
    minute = schedule.device_id % 60
    logger.info(f"[Scheduler] Hourly schedule for device {schedule.device_id} set to minute={minute}")
    return CronTrigger(minute=str(minute))
```

## 分散策略说明

| 设备 ID | 执行分钟 |
|---------|----------|
| 1 | 1 |
| 2 | 2 |
| ... | ... |
| 59 | 59 |
| 60 | 0 |
| 61 | 1 |
| 62 | 2 |
| ... | ... |

## 优点

1. **确定性**：同一设备总是在同一分钟执行，便于调试
2. **分布均匀**：65台设备分散在60分钟内，每分钟约1-2个任务
3. **实现简单**：只需修改一行代码
4. **兼容现有**：不影响 daily 和 monthly 类型的任务

## 验证要点

- 加载备份计划时，日志显示每个 hourly 任务的 minute 设置
- 设备1在第1分钟执行，设备2在第2分钟执行，以此类推
- 没有两个 hourly 任务在同一分钟执行（除非设备数超过60）

