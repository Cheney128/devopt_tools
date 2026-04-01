---
ontology:
  id: DOC-auto-generated
  type: document
  problem: ARP/MAC 调度器修复
  problem_id: P001
  status: active
  created: 2026-03-30
  updated: 2026-03-30
  author: Claude
  tags:
    - documentation
---
# ARP/MAC 自动采集不运行根因分析报告

**分析日期**: 2026-03-30  
**分析人**: 乐乐 (DevOps Agent)  
**项目**: switch_manage  
**数据库**: 10.21.65.20:3307 (测试环境)

---

## 一、问题现象

### 1.1 数据停滞
- `arp_current` 表：记录数为 **0**，无最新采集数据
- `mac_current` 表：记录数为 **0**，无最新采集数据
- `ip_location_current` 表：有 2207 条记录，但 `last_seen` 最晚为 **2026-03-26 15:22:35**
- `ip_location_current.calculated_at` 最新为 **2026-03-30 10:13:37**（说明 IP 定位计算手动触发过）

### 1.2 设备 ID 不一致（已知背景）
- `devices` 表当前 ID 范围：211-276
- 历史采集数据中存在旧 ID（89、116 等）
- 原因：缺少外键约束和级联删除机制（已确认）

---

## 二、调度机制分析

### 2.1 现有调度器架构

项目中存在 **三个独立的调度器**：

| 调度器 | 文件 | 功能 | 启动方式 | 状态 |
|--------|------|------|----------|------|
| `backup_scheduler` | `app/services/backup_scheduler.py` | 设备配置备份 | `main.py` startup 事件 | ✅ 正常加载 |
| `ip_location_scheduler` | `app/services/ip_location_scheduler.py` | IP 定位预计算 | `main.py` startup 事件 | ✅ 正常启动 |
| `arp_mac_scheduler` | `app/services/arp_mac_scheduler.py` | ARP/MAC 数据采集 | **未在任何地方调用** | ❌ **未启动** |

### 2.2 调度器启动流程（app/main.py）

```python
@app.on_event("startup")
async def startup_event():
    # 1. 加载备份任务
    backup_scheduler.load_schedules(db)
    
    # 2. 启动 IP 定位预计算调度器
    ip_location_scheduler.start()
    
    # ❌ 缺少：ARP/MAC 采集调度器启动代码
```

### 2.3 ip_location_scheduler 功能分析

**职责**：仅负责 IP 定位预计算（调用 `IPLocationCalculator.calculate_batch()`）

**触发机制**：
- 定时任务：每 10 分钟执行一次（`IntervalTrigger(minutes=10)`）
- 手动触发：通过 API `/api/ip-location/collection/trigger`（需手动调用）

**关键发现**：
```python
# ip_location_scheduler.py 第 52-67 行
def _run_calculation(self):
    """执行预计算（定时任务回调）"""
    logger.info("开始执行 IP 定位预计算...")
    
    try:
        db = SessionLocal()
        calculator = IPLocationCalculator(db)
        stats = calculator.calculate_batch()  # 仅计算，不采集
        ...
```

**结论**：`ip_location_scheduler` **只负责计算，不负责采集**。它依赖于 `arp_current` 和 `mac_current` 表中已有数据。

### 2.4 arp_mac_scheduler 功能分析

**职责**：负责 ARP 和 MAC 数据的实际采集

**关键方法**：
```python
# arp_mac_scheduler.py
def collect_all_devices(self) -> dict:
    """采集所有活跃设备的 ARP 和 MAC 表"""
    devices = self.db.query(Device).filter(Device.status == 'active').all()
    # 逐个设备采集 ARP 和 MAC，保存到 arp_current 和 mac_current 表

def collect_and_calculate(self) -> dict:
    """采集 ARP+MAC 并触发 IP 定位计算"""
    collection_stats = self.collect_all_devices()  # 先采集
    calculation_stats = calculator.calculate_batch()  # 后计算
```

**关键发现**：
1. `arp_mac_scheduler.py` 文件存在且功能完整
2. 但该文件 **从未在 `main.py` 中被导入或启动**
3. 没有任何定时任务或 API 调用该调度器

---

## 三、根因定位

### 3.1 根本原因

**ARP/MAC 自动采集功能从未被集成到应用启动流程中。**

具体表现：
1. `arp_mac_scheduler.py` 文件存在但未被使用
2. `main.py` 中缺少 `arp_mac_scheduler` 的导入和启动代码
3. 没有任何定时任务触发 ARP/MAC 采集
4. `ip_location_scheduler` 仅负责计算，无法触发采集

### 3.2 证据链

#### 证据 1：main.py 中无 arp_mac_scheduler 相关代码
```bash
$ grep -r "arp_mac_scheduler" /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage/app/main.py
# (无输出)
```

#### 证据 2：arp_current 和 mac_current 表为空
```sql
mysql> SELECT MAX(last_seen), COUNT(*) FROM arp_current;
+----------------+----------+
| MAX(last_seen) | COUNT(*) |
+----------------+----------+
| NULL           | 0        |
+----------------+----------+

mysql> SELECT MAX(last_seen), COUNT(*) FROM mac_current;
+----------------+----------+
| MAX(last_seen) | COUNT(*) |
+----------------+----------+
| NULL           | 0        |
+----------------+----------+
```

#### 证据 3：ip_location_current 数据停滞在 3 月 26 日
```sql
mysql> SELECT MAX(calculated_at), MAX(last_seen), COUNT(*) FROM ip_location_current;
+---------------------+---------------------+----------+
| MAX(calculated_at)  | MAX(last_seen)      | COUNT(*) |
+---------------------+---------------------+----------+
| 2026-03-30 10:13:37 | 2026-03-26 15:22:35 | 2207     |
+---------------------+---------------------+----------+
```

- `calculated_at` 最新（今天手动触发过计算）
- `last_seen` 停滞在 3 月 26 日（原始采集数据未更新）
- 说明：计算任务在运行，但采集任务从未运行

#### 证据 4：arp_mac_scheduler.py 代码中存在 import 缺失
```python
# arp_mac_scheduler.py 第 112 行使用 uuid，但未导入
collection_batch_id=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

# 文件头部无 import uuid
```

---

## 四、日志分析

### 4.1 日志配置

项目使用 `logging.basicConfig(level=logging.INFO)` 配置日志，输出到标准输出。

### 4.2 应用启动日志

当前应用通过 uvicorn 运行：
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**预期启动日志**（来自 `main.py`）：
```
[Startup] DATABASE_URL: mysql+pymysql://***:***@10.21.65.20:3307/switch_manage
[Startup] DEPLOY_MODE: 未设置
[Startup] IP Location scheduler started (interval: 10 minutes)
```

**缺失的日志**：
```
# 应该有以下日志但实际没有
[Startup] ARP/MAC scheduler started (interval: XX minutes)
```

### 4.3 采集日志

**预期采集日志**（来自 `arp_mac_scheduler.py`）：
```
开始批量采集 ARP 和 MAC 表，时间：2026-03-30 10:00:00
共有 XX 台设备需要采集
设备 XXX ARP 采集成功：XX 条
设备 XXX MAC 采集成功：XX 条
批量采集完成：{...}
```

**实际日志**：无相关输出

---

## 五、配置分析

### 5.1 采集间隔配置

| 配置项 | 位置 | 值 | 说明 |
|--------|------|-----|------|
| `interval_minutes` | `ip_location_scheduler.py` | 10 | IP 定位预计算间隔 |
| `calculation_interval_minutes` | `ip_location.py` DEFAULT_SETTINGS | 10 | 数据库配置默认值 |
| ARP/MAC 采集间隔 | **无配置** | N/A | 调度器未启动 |

### 5.2 依赖服务

| 依赖 | 状态 | 说明 |
|------|------|------|
| APScheduler | ✅ 已安装 (3.10.4) | 定时任务框架 |
| Redis | ❌ 未使用 | 项目未配置 Redis |
| 数据库连接 | ✅ 正常 | 10.21.65.20:3307 |

---

## 六、代码逻辑分析

### 6.1 采集函数调用链

```
用户手动触发
    ↓
/api/arp-collection/{device_id}/collect (API)
    ↓
netmiko_service.collect_arp_table(device)
    ↓
arp_current 表（单设备）

或

定时任务（缺失）
    ↓
arp_mac_scheduler.collect_all_devices()
    ↓
netmiko_service.batch_collect_arp_table(devices)
    ↓
arp_current 表（批量）
```

### 6.2 条件判断分析

`ip_location_scheduler._run_calculation()` 中无条件跳过逻辑，但：
- 如果 `arp_current` 和 `mac_current` 表为空
- `IPLocationCalculator.calculate_batch()` 会加载 0 条记录
- 计算结果 `matched=0`，但不会报错

### 6.3 异常处理分析

`arp_mac_scheduler.py` 中有异常处理：
```python
try:
    # 采集逻辑
    self.db.commit()
except Exception as e:
    logger.error(f"设备 {device.hostname} 采集失败：{str(e)}")
    self.db.rollback()
```

但由于调度器从未启动，异常处理代码也从未执行。

---

## 七、修复方案

### 7.1 短期修复（推荐）

在 `app/main.py` 中添加 ARP/MAC 采集调度器启动代码：

```python
# app/main.py
from app.services.arp_mac_scheduler import ARPMACScheduler  # 新增导入
from app.services.ip_location_scheduler import ip_location_scheduler
from app.services.backup_scheduler import backup_scheduler

# 创建全局 ARP/MAC 采集调度器实例
arp_mac_scheduler = None  # 需要在 startup 中初始化

@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    
    # 1. 加载备份任务
    backup_scheduler.load_schedules(db)
    
    # 2. 启动 IP 定位预计算调度器
    ip_location_scheduler.start()
    
    # 3. 启动 ARP/MAC 采集调度器（新增）
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        
        # 创建后台调度器
        arp_scheduler = BackgroundScheduler()
        
        # 添加定时任务（每 30 分钟采集一次）
        arp_scheduler.add_job(
            func=lambda: ARPMACScheduler(db).collect_and_calculate(),
            trigger=IntervalTrigger(minutes=30),
            id='arp_mac_collection',
            name='ARP/MAC 自动采集',
            replace_existing=True,
            misfire_grace_time=600  # 允许 10 分钟的错过执行宽限期
        )
        
        arp_scheduler.start()
        print("[Startup] ARP/MAC collection scheduler started (interval: 30 minutes)")
        
    except Exception as e:
        print(f"Warning: Could not start ARP/MAC collection scheduler: {e}")
```

### 7.2 中期修复

创建独立的 `ARPMACSchedulerService` 类（参考 `backup_scheduler.py`）：

```python
# app/services/arp_mac_scheduler_service.py
class ARPMACSchedulerService:
    def __init__(self, interval_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self._is_running = False
    
    def start(self):
        if self._is_running:
            return
        
        self.scheduler.add_job(
            func=self._run_collection,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='arp_mac_collection',
            name='ARP/MAC 自动采集',
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info(f"ARP/MAC 采集调度器已启动，间隔：{self.interval_minutes} 分钟")
    
    def _run_collection(self):
        db = SessionLocal()
        try:
            scheduler = ARPMACScheduler(db)
            stats = scheduler.collect_and_calculate()
            logger.info(f"ARP/MAC 采集完成：{stats}")
        finally:
            db.close()

# 创建全局实例
arp_mac_scheduler = ARPMACSchedulerService(interval_minutes=30)
```

### 7.3 长期修复

1. **统一调度器管理**：创建 `SchedulerManager` 统一管理所有定时任务
2. **配置化**：将采集间隔移到配置文件或数据库配置表
3. **监控告警**：添加采集失败告警机制
4. **健康检查**：添加 `/health/scheduler` 端点检查调度器状态

### 7.4 代码修复

修复 `arp_mac_scheduler.py` 中的 import 缺失：

```python
# 在文件头部添加
import uuid
```

---

## 八、验证方案

### 8.1 启动验证

修复后重启应用，检查启动日志：
```bash
# 预期输出
[Startup] IP Location scheduler started (interval: 10 minutes)
[Startup] ARP/MAC collection scheduler started (interval: 30 minutes)
```

### 8.2 数据采集验证

等待第一个采集周期后检查数据库：
```sql
-- 检查 ARP 数据
SELECT COUNT(*), MAX(last_seen) FROM arp_current;
-- 预期：COUNT(*) > 0, MAX(last_seen) 为当前时间

-- 检查 MAC 数据
SELECT COUNT(*), MAX(last_seen) FROM mac_current;
-- 预期：COUNT(*) > 0, MAX(last_seen) 为当前时间

-- 检查 IP 定位计算
SELECT COUNT(*), MAX(calculated_at) FROM ip_location_current;
-- 预期：自动更新
```

### 8.3 调度器状态验证

添加 API 端点检查调度器状态：
```python
@router.get("/scheduler/status")
async def get_scheduler_status():
    return {
        'ip_location': ip_location_scheduler.get_status(),
        'arp_mac': arp_mac_scheduler.get_status(),
    }
```

---

## 九、总结

### 9.1 根因

**ARP/MAC 自动采集调度器 (`arp_mac_scheduler.py`) 从未被集成到应用启动流程中**，导致：
1. 采集任务从未自动执行
2. `arp_current` 和 `mac_current` 表为空
3. IP 定位计算无新数据可处理
4. 数据停滞在 3 月 26 日

### 9.2 影响范围

- **受影响功能**：ARP/MAC 自动采集、IP 定位自动更新
- **不受影响功能**：手动采集 API、IP 定位手动计算、历史数据查询
- **数据风险**：无数据丢失风险，仅数据不更新

### 9.3 修复优先级

🔴 **高优先级**：采集功能是 IP 定位功能的数据来源，需尽快修复

### 9.4 后续建议

1. 添加调度器健康检查端点
2. 添加采集失败告警机制
3. 完善日志记录（采集开始/结束/失败）
4. 考虑添加手动触发采集的 API（已存在但需验证）

---

**报告完成时间**: 2026-03-30 10:35  
**分析工具**: Superpowers systematic-debugging
