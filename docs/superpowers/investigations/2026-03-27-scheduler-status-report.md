# IP 定位 Ver3 定时采集任务运行状态调查报告

**调查日期**: 2026-03-27
**调查人员**: Claude
**问题背景**: arp_current 和 mac_current 表中所有记录的 last_seen 都是昨天 15:22，怀疑定时采集任务没有运行。

---

## 调查结论

**根本原因**: ARP+MAC 定时采集任务从未启动，因为调度器代码存在但未被集成到应用启动流程中。

---

## 详细调查结果

### 1. 定时任务代码调查

#### 1.1 现有调度器文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `app/services/ip_location_scheduler.py` | 已集成 | IP 定位计算调度器（每10分钟执行计算） |
| `app/services/arp_mac_scheduler.py` | **未集成** | ARP+MAC 采集调度器（未被导入或启动） |
| `app/services/backup_scheduler.py` | 已集成 | 备份调度器 |

#### 1.2 `ip_location_scheduler.py` 分析

```python
# app/services/ip_location_scheduler.py
class IPLocationScheduler:
    def __init__(self, interval_minutes: int = 10):
        self.scheduler = BackgroundScheduler()

    def _run_calculation(self):
        """执行预计算（定时任务回调）"""
        # 从 arp_current 和 mac_current 表读取数据进行计算
        # 不负责采集数据
```

**关键发现**: `IPLocationScheduler` 只是 **计算器**，不负责采集 ARP/MAC 数据。它从现有的 `arp_current` 和 `mac_current` 表读取数据进行 IP 定位匹配。

#### 1.3 `arp_mac_scheduler.py` 分析

```python
# app/services/arp_mac_scheduler.py
class ARPMACScheduler:
    """ARP+MAC 批量采集调度器"""

    def collect_all_devices(self) -> dict:
        """采集所有活跃设备的 ARP 和 MAC 表"""
        # ... 采集逻辑
```

**关键发现**: `ARPMACScheduler` 类存在，但：
- 未在 `main.py` 中导入
- 未在启动事件中实例化或启动
- 没有定时任务注册

**代码缺陷**: 第 135 行使用了 `uuid.uuid4()` 但未导入 `uuid` 模块，会导致运行时错误。

---

### 2. 应用启动配置调查

#### 2.1 `main.py` 启动事件

```python
# app/main.py
from app.services.backup_scheduler import backup_scheduler
from app.services.ip_location_scheduler import ip_location_scheduler
# 注意：没有导入 arp_mac_scheduler

@app.on_event("startup")
async def startup_event():
    # 加载备份任务
    backup_scheduler.load_schedules(db)

    # 启动 IP 定位预计算调度器
    ip_location_scheduler.start()
    print("[Startup] IP Location scheduler started (interval: 10 minutes)")

    # 注意：没有启动 ARP+MAC 采集调度器
```

**结论**: 应用启动时只启动了：
1. `backup_scheduler` - 备份调度器
2. `ip_location_scheduler` - IP 定位计算调度器

**ARP+MAC 采集调度器从未被启动。**

---

### 3. 数据流分析

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   ARP 采集      │     │   MAC 采集      │     │  IP 定位计算    │
│  (手动/API)     │     │  (手动/API)     │     │  (定时10分钟)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  arp_current    │     │  mac_current    │────▶│ ip_location_    │
│     表          │────▶│     表          │     │    current      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                       ▲
        │                       │
   ┌────┴────┐            ┌────┴────┐
   │ 手动触发 │            │ 手动触发 │
   │  API    │            │  API    │
   └─────────┘            └─────────┘
```

**问题**: 数据流中缺少定时采集环节，`arp_current` 和 `mac_current` 表的数据只能通过手动 API 触发更新。

---

### 4. 可用的手动采集 API

#### 4.1 ARP 采集 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/arp-collection/{device_id}/collect` | POST | 采集单个设备 ARP 表 |
| `/api/arp-collection/batch/collect` | POST | 批量采集 ARP 表 |

#### 4.2 MAC 采集 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/device-collection/{device_id}/collect-mac` | POST | 采集单个设备 MAC 表 |

#### 4.3 代码问题

**`arp_collection.py` 第 57 行和 68 行**:
```python
# 错误：使用了不存在的字段名
db.query(ARPEntry).filter(ARPEntry.device_id == device_id).delete()
#                                        ^^^^^^^^^^
# 应该是: ARPEntry.arp_device_id
```

**`arp_mac_scheduler.py` 第 135 行**:
```python
# 错误：未导入 uuid 模块
collection_batch_id=f"batch_{...}_{uuid.uuid4().hex[:8]}"
#                              ^^^^ NameError
```

---

### 5. 日志证据

**`netmiko_session.log`**: 只包含设备连接日志，无定时采集相关日志。

**应用日志**: 未找到 IP 定位调度器的执行日志（可能未配置日志输出到文件）。

---

### 6. 数据状态推断

根据 `arp_current` 和 `mac_current` 表中 `last_seen` 时间（昨天 15:22）：
- 数据是通过手动 API 触发采集的
- 之后没有新的采集任务运行
- `ip_location_scheduler` 虽然在运行，但由于源数据没有更新，计算结果也没有变化

---

## 问题总结

| 问题 | 严重程度 | 状态 |
|------|----------|------|
| ARP+MAC 采集调度器未集成 | **严重** | 未修复 |
| `arp_mac_scheduler.py` 缺少 uuid 导入 | 高 | 未修复 |
| `arp_collection.py` 字段名错误 | 高 | 未修复 |
| 缺少定时采集任务日志记录 | 中 | 未配置 |

---

## 建议修复方案

1. **集成 ARP+MAC 采集调度器**
   - 在 `main.py` 中导入并启动 `ARPMACScheduler`
   - 配置合理的采集间隔（如每 5 分钟）

2. **修复代码缺陷**
   - 在 `arp_mac_scheduler.py` 中添加 `import uuid`
   - 修复 `arp_collection.py` 中的字段名错误

3. **完善日志配置**
   - 配置调度器日志输出到文件
   - 添加采集开始/结束日志

---

## 附录：相关文件路径

- `app/services/ip_location_scheduler.py` - IP 定位计算调度器
- `app/services/arp_mac_scheduler.py` - ARP+MAC 采集调度器（未集成）
- `app/services/ip_location_calculator.py` - IP 定位计算核心逻辑
- `app/api/endpoints/arp_collection.py` - ARP 采集 API
- `app/api/endpoints/device_collection.py` - MAC 采集 API
- `app/models/ip_location_current.py` - ARP/MAC 数据模型
- `app/main.py` - 应用入口