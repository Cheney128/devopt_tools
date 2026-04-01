---
ontology:
  id: DOC-auto-generated
  type: document
  problem: 中间版本归档
  problem_id: ARCH
  status: archived
  created: 2026-03
  updated: 2026-03
  author: Claude
  tags:
    - documentation
---
# ARP/MAC 采集调度器修复方案

**文档版本**: 1.1  
**创建日期**: 2026-03-30  
**更新日期**: 2026-03-30 11:30  
**负责人**: 运维开发团队  
**优先级**: 🔴 高（数据采集停滞）

---

## ✅ 实施状态

**短期修复**: ✅ **已完成** (2026-03-30 11:30)

- [x] 任务 1：修复 uuid 导入
- [x] 任务 2：集成到启动流程
- [x] 任务 3：配置采集间隔

**Git Commit**: `fix/regression-2026-03-26`  
**验证状态**: ⏳ 待验证（需重启应用并观察 30 分钟）

---

---

## 📋 目录

- [问题背景和根因](#-问题背景和根因)
- [短期修复方案（1 天内）](#-短期修复方案 1-天内)
- [中期修复方案（1 周内）](#-中期修复方案 1-周内)
- [实施计划](#-实施计划)
- [验证方案](#-验证方案)
- [回滚方案](#-回滚方案)

---

## 📌 问题背景和根因

### 问题现象

ARP/MAC 自动采集数据停滞在 **2026-03-26**，此后无新增采集记录。

### 根因分析

经过代码审查，发现以下问题：

1. **代码缺陷**：`app/services/arp_mac_scheduler.py` 中使用了 `uuid` 模块但未导入
   - 位置：第 119 行 `uuid.uuid4().hex[:8]`
   - 影响：调度器运行时会产生 `NameError: name 'uuid' is not defined`

2. **集成缺失**：ARP/MAC 调度器从未被集成到应用启动流程
   - 对比参考：`ip_location_scheduler` 和 `backup_scheduler` 均在 `app/main.py` 的 `startup_event()` 中启动
   - 现状：`arp_mac_scheduler` 无任何启动代码，应用重启后调度器不会运行

### 影响范围

- **受影响模块**：ARP 表采集、MAC 表采集、IP 定位预计算
- **业务影响**：IP 定位数据无法更新，影响网络拓扑分析和故障定位
- **数据影响**：2026-03-26 至今的 ARP/MAC 数据缺失

---

## 🔧 短期修复方案（1 天内）

### 任务 1：修复 uuid 导入

**文件**: `app/services/arp_mac_scheduler.py`

**问题**: 使用了 `uuid` 但未导入

**修复方案**:

```python
# 在文件头部导入部分添加（第 12 行附近）
import uuid
```

**修改后的导入部分**:

```python
import logging
import uuid  # ← 新增
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.models import Device
from app.models.ip_location_current import ARPEntry, MACAddressCurrent
from app.services.netmiko_service import get_netmiko_service
from app.services.ip_location_calculator import get_ip_location_calculator
```

**风险评估**: 🟢 低风险（仅添加导入语句）

---

### 任务 2：集成到启动流程

**文件**: `app/main.py`

**参考实现**:

对比 `ip_location_scheduler` 和 `backup_scheduler` 的集成方式：

```python
# app/main.py 现有代码（参考）
from app.services.backup_scheduler import backup_scheduler
from app.services.ip_location_scheduler import ip_location_scheduler

@app.on_event("startup")
async def startup_event():
    # ... 其他代码 ...
    
    # 启动 IP 定位预计算调度器
    try:
        ip_location_scheduler.start()
        print("[Startup] IP Location scheduler started (interval: 10 minutes)")
    except Exception as e:
        print(f"Warning: Could not start IP location scheduler: {e}")
```

**修复方案**:

1. **添加导入**（第 10 行附近）:

```python
from app.services.backup_scheduler import backup_scheduler
from app.services.ip_location_scheduler import ip_location_scheduler
from app.services.arp_mac_scheduler import arp_mac_scheduler  # ← 新增
```

2. **在 startup_event() 中添加启动代码**（第 57 行附近，IP 定位调度器启动之后）:

```python
    # 启动 IP 定位预计算调度器
    try:
        ip_location_scheduler.start()
        print("[Startup] IP Location scheduler started (interval: 10 minutes)")
    except Exception as e:
        print(f"Warning: Could not start IP location scheduler: {e}")
    
    # 启动 ARP/MAC 采集调度器 ← 新增
    try:
        db = next(get_db())
        arp_mac_scheduler.start(db)
        print("[Startup] ARP/MAC scheduler started (interval: 30 minutes)")
    except Exception as e:
        print(f"Warning: Could not start ARP/MAC scheduler: {e}")
```

**风险评估**: 🟡 中风险（需确保调度器启动不影响其他服务）

---

### 任务 3：配置采集间隔

**文件**: `app/services/arp_mac_scheduler.py` 和 `.env`

**建议采集间隔**: 30 分钟

**修复方案**:

1. **修改调度器类支持间隔配置**:

```python
# app/services/arp_mac_scheduler.py 类定义修改

class ARPMACScheduler:
    """
    ARP+MAC 批量采集调度器
    """

    def __init__(self, db: Session, interval_minutes: int = 30):
        """
        初始化调度器

        Args:
            db: 数据库会话
            interval_minutes: 采集间隔（分钟），默认 30 分钟
        """
        self.db = db
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self._is_running = False
        self.netmiko = get_netmiko_service(db)
    
    def start(self, db: Session = None):
        """
        启动调度器
        
        Args:
            db: 数据库会话（可选，如果初始化时已提供则不需要）
        """
        if self._is_running:
            logger.warning("ARP/MAC 调度器已在运行中")
            return
        
        # 如果提供了新的 db，更新它
        if db:
            self.db = db
        
        # 添加定时任务
        self.scheduler.add_job(
            func=self.collect_and_calculate,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='arp_mac_collection',
            name='ARP/MAC 采集',
            replace_existing=True,
            misfire_grace_time=600  # 允许 10 分钟的错过执行宽限期
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info(f"ARP/MAC 调度器已启动，间隔：{self.interval_minutes} 分钟")
    
    def shutdown(self):
        """
        关闭调度器
        """
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("ARP/MAC 调度器已关闭")
    
    def get_status(self) -> dict:
        """
        获取调度器状态
        
        Returns:
            状态信息字典
        """
        jobs = self.scheduler.get_jobs() if self._is_running else []
        arp_job = next((j for j in jobs if j.id == 'arp_mac_collection'), None)
        
        return {
            'is_running': self._is_running,
            'interval_minutes': self.interval_minutes,
            'last_run': None,  # 待实现
            'next_run': arp_job.next_run_time.isoformat() if arp_job and arp_job.next_run_time else None,
        }
```

2. **添加必要导入**:

```python
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler  # ← 新增
from apscheduler.triggers.interval import IntervalTrigger  # ← 新增

# ... 其他导入保持不变 ...
```

3. **创建全局实例**（文件末尾）:

```python
# 创建全局调度器实例
arp_mac_scheduler = ARPMACScheduler(db=None)  # db 将在 start() 时传入


def get_arp_mac_scheduler(db: Session) -> ARPMACScheduler:
    """
    获取 ARP+MAC 调度器实例

    Args:
        db: 数据库会话

    Returns:
        调度器实例
    """
    return ARPMACScheduler(db)
```

4. **添加环境变量配置**（`.env` 文件）:

```bash
# ARP/MAC 采集间隔（分钟）
ARP_MAC_COLLECTION_INTERVAL=30
```

5. **在 config.py 中添加配置项**:

```python
class Settings:
    def __init__(self):
        # ... 现有配置 ...
        
        # ARP/MAC 采集配置
        self.ARP_MAC_COLLECTION_INTERVAL = int(
            os.getenv('ARP_MAC_COLLECTION_INTERVAL', '30')
        )
```

**风险评估**: 🟡 中风险（需验证 APScheduler 依赖已安装）

---

## 📈 中期修复方案（1 周内）

### 任务 1：添加调度器健康检查

#### 设计思路

参考 `ip_location_scheduler.get_status()` 方法，为 ARP/MAC 调度器实现健康状态监控。

#### 接口定义

**API 端点**: `GET /api/v1/scheduler/arp-mac/status`

**响应示例**:

```json
{
  "scheduler": "arp_mac",
  "is_running": true,
  "interval_minutes": 30,
  "last_run": "2026-03-30T10:30:00+08:00",
  "last_stats": {
    "arp_success": 15,
    "arp_failed": 1,
    "mac_success": 15,
    "mac_failed": 1,
    "total_arp_entries": 1250,
    "total_mac_entries": 3400,
    "duration_seconds": 180.5
  },
  "next_run": "2026-03-30T11:00:00+08:00",
  "health_status": "healthy"
}
```

**健康状态定义**:

| 状态 | 条件 |
|------|------|
| `healthy` | 调度器运行中，最近一次采集成功率 > 80% |
| `degraded` | 调度器运行中，最近一次采集成功率 50%-80% |
| `unhealthy` | 调度器未运行，或最近一次采集成功率 < 50% |

#### 实现步骤

1. **在 `ARPMACScheduler` 类中增强状态跟踪**:

```python
class ARPMACScheduler:
    def __init__(self, db: Session, interval_minutes: int = 30):
        # ... 现有代码 ...
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None
        self._consecutive_failures: int = 0
    
    def _run_calculation(self):
        """定时任务回调（内部使用）"""
        try:
            stats = self.collect_and_calculate()
            self._last_run = datetime.now()
            self._last_stats = stats
            
            # 更新失败计数
            if stats.get('collection', {}).get('arp_success', 0) == 0:
                self._consecutive_failures += 1
            else:
                self._consecutive_failures = 0
                
        except Exception as e:
            logger.error(f"ARP/MAC 采集失败：{e}", exc_info=True)
            self._consecutive_failures += 1
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        jobs = self.scheduler.get_jobs() if self._is_running else []
        arp_job = next((j for j in jobs if j.id == 'arp_mac_collection'), None)
        
        # 计算健康状态
        health_status = "healthy"
        if not self._is_running:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 3:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 1:
            health_status = "degraded"
        
        return {
            'scheduler': 'arp_mac',
            'is_running': self._is_running,
            'interval_minutes': self.interval_minutes,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'last_stats': self._last_stats,
            'next_run': arp_job.next_run_time.isoformat() if arp_job and arp_job.next_run_time else None,
            'consecutive_failures': self._consecutive_failures,
            'health_status': health_status,
        }
```

2. **添加 API 端点** (`app/api/endpoints/scheduler.py`):

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models import get_db
from app.services.arp_mac_scheduler import get_arp_mac_scheduler, ARPMACScheduler

router = APIRouter()

@router.get("/scheduler/arp-mac/status")
def get_arp_mac_scheduler_status(
    scheduler: ARPMACScheduler = Depends(get_arp_mac_scheduler)
):
    """
    获取 ARP/MAC 调度器状态
    """
    return scheduler.get_status()
```

3. **前端展示**（建议）:
   - 在系统监控页面添加调度器状态卡片
   - 显示运行状态、上次运行时间、下次运行时间、健康状态
   - 提供手动触发按钮

---

### 任务 2：添加采集失败告警

#### 设计思路

实现分级告警机制，根据失败次数触发不同级别的告警。

#### 告警规则

| 失败次数 | 告警级别 | 告警方式 | 告警内容 |
|----------|----------|----------|----------|
| 1-2 次 | 警告 | 日志记录 | 记录错误日志 |
| 3-5 次 | 严重 | 飞书消息 | 发送告警到运维群 |
| 6+ 次 | 紧急 | 飞书消息 + 邮件 | 发送告警到运维群 + 邮件通知负责人 |

#### 实现方案

1. **在 `ARPMACScheduler` 中添加告警逻辑**:

```python
class ARPMACScheduler:
    def __init__(self, db: Session, interval_minutes: int = 30):
        # ... 现有代码 ...
        self._consecutive_failures: int = 0
        self._failure_threshold_warning = 3    # 警告阈值
        self._failure_threshold_critical = 6   # 紧急阈值
    
    def _run_calculation(self):
        """定时任务回调"""
        try:
            stats = self.collect_and_calculate()
            self._last_run = datetime.now()
            self._last_stats = stats
            
            # 检查采集成功率
            collection = stats.get('collection', {})
            arp_success = collection.get('arp_success', 0)
            arp_failed = collection.get('arp_failed', 0)
            
            if arp_success == 0 and arp_failed > 0:
                # 采集完全失败
                self._consecutive_failures += 1
                self._handle_failure(arp_success, arp_failed)
            else:
                # 采集成功或部分成功
                if self._consecutive_failures > 0:
                    logger.info(f"ARP/MAC 采集恢复，之前连续失败 {self._consecutive_failures} 次")
                self._consecutive_failures = 0
        
        except Exception as e:
            logger.error(f"ARP/MAC 采集异常：{e}", exc_info=True)
            self._consecutive_failures += 1
            self._handle_failure(0, 0, str(e))
    
    def _handle_failure(self, arp_success: int, arp_failed: int, error: str = None):
        """
        处理采集失败
        
        Args:
            arp_success: ARP 采集成功设备数
            arp_failed: ARP 采集失败设备数
            error: 错误信息
        """
        # 记录错误日志
        if error:
            logger.error(f"ARP/MAC 采集异常：{error}")
        else:
            logger.error(f"ARP/MAC 采集失败：成功 {arp_success} 台，失败 {arp_failed} 台")
        
        # 判断告警级别
        if self._consecutive_failures >= self._failure_threshold_critical:
            self._send_alert("critical", arp_success, arp_failed, error)
        elif self._consecutive_failures >= self._failure_threshold_warning:
            self._send_alert("warning", arp_success, arp_failed, error)
    
    def _send_alert(self, level: str, arp_success: int, arp_failed: int, error: str = None):
        """
        发送告警
        
        Args:
            level: 告警级别 (warning/critical)
            arp_success: ARP 采集成功设备数
            arp_failed: ARP 采集失败设备数
            error: 错误信息
        """
        from app.services.feishu_service import send_feishu_alert  # 假设存在飞书服务
        
        title = "🔴 ARP/MAC 采集紧急告警" if level == "critical" else "🟡 ARP/MAC 采集警告"
        
        content = f"""
**告警级别**: {level}
**失败次数**: 连续 {self._consecutive_failures} 次
**采集结果**: 成功 {arp_success} 台，失败 {arp_failed} 台
**错误信息**: {error or '采集异常'}
**发生时间**: {datetime.now().isoformat()}
**建议操作**: 检查设备连通性、网络状态、采集服务日志
"""
        
        # 发送飞书消息
        try:
            send_feishu_alert(
                title=title,
                content=content,
                level=level
            )
            logger.info(f"已发送 {level} 级别飞书告警")
        except Exception as e:
            logger.error(f"发送飞书告警失败：{e}")
        
        # 如果是紧急级别，发送邮件
        if level == "critical":
            self._send_email_alert(title, content)
    
    def _send_email_alert(self, title: str, content: str):
        """发送紧急邮件告警"""
        # TODO: 实现邮件发送逻辑
        logger.warning("邮件告警功能待实现")
```

2. **配置告警接收人**（`.env` 文件）:

```bash
# 告警配置
ARP_MAC_ALERT_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
ARP_MAC_ALERT_EMAIL=ops@example.com
```

---

## 📅 实施计划

### 优先级排序

| 优先级 | 任务 | 工时评估 | 依赖 |
|--------|------|----------|------|
| P0 | 修复 uuid 导入 | 0.1 小时 | 无 |
| P0 | 集成到启动流程 | 0.5 小时 | uuid 导入修复 |
| P0 | 配置采集间隔 | 1 小时 | 集成到启动流程 |
| P1 | 添加调度器健康检查 API | 2 小时 | 采集间隔配置 |
| P1 | 前端展示调度器状态 | 2 小时 | 健康检查 API |
| P2 | 添加采集失败告警 | 3 小时 | 健康检查 |

### 时间安排

**Day 1（短期修复）**:
- 上午：完成 P0 任务（uuid 导入 + 启动集成 + 采集间隔配置）
- 下午：验证修复效果，观察 1-2 个采集周期

**Day 2-3（中期修复 - 健康检查）**:
- 实现调度器状态 API
- 前端展示开发

**Day 4-5（中期修复 - 告警）**:
- 实现失败检测和告警逻辑
- 配置告警接收人
- 测试告警流程

---

## ✅ 验证方案

### 验证步骤

1. **代码验证**:
   ```bash
   # 语法检查
   python -m py_compile app/services/arp_mac_scheduler.py
   python -m py_compile app/main.py
   
   # 导入测试
   python -c "from app.services.arp_mac_scheduler import arp_mac_scheduler; print('OK')"
   ```

2. **启动验证**:
   ```bash
   # 启动应用
   python -m uvicorn app.main:app --reload
   
   # 检查日志输出
   # 应看到：[Startup] ARP/MAC scheduler started (interval: 30 minutes)
   ```

3. **功能验证**:
   ```bash
   # 查询调度器状态
   curl http://localhost:8000/api/v1/scheduler/arp-mac/status
   
   # 预期响应
   # {"is_running": true, "interval_minutes": 30, ...}
   ```

4. **采集验证**:
   ```sql
   -- 等待 30 分钟后，查询数据库
   SELECT COUNT(*), MAX(last_seen) FROM arp_entries;
   SELECT COUNT(*), MAX(last_seen) FROM mac_addresses_current;
   
   -- last_seen 应该是最近 30 分钟内
   ```

5. **告警验证**（中期）:
   - 模拟设备不可达场景
   - 观察日志中的错误记录
   - 验证飞书告警消息接收

### 验收标准

- [ ] 应用启动日志显示 ARP/MAC 调度器已启动
- [ ] 调度器状态 API 返回 `is_running: true`
- [ ] 30 分钟后数据库中有新的 ARP/MAC 记录
- [ ] 采集成功率 > 90%（活跃设备）
- [ ] 告警功能正常触发（中期）

---

## 🔄 回滚方案

### 回滚场景

| 场景 | 回滚操作 | 影响 |
|------|----------|------|
| 调度器启动失败 | 注释掉 `main.py` 中的启动代码 | 无影响（恢复原状） |
| 采集性能问题 | 调整采集间隔或暂停调度器 | 数据采集暂停 |
| 数据库压力过大 | 增加采集间隔至 60 分钟 | 数据更新延迟 |

### 回滚步骤

1. **快速回滚**（注释启动代码）:

```python
# app/main.py 修改
# 注释掉新增的启动代码
# try:
#     db = next(get_db())
#     arp_mac_scheduler.start(db)
#     print("[Startup] ARP/MAC scheduler started (interval: 30 minutes)")
# except Exception as e:
#     print(f"Warning: Could not start ARP/MAC scheduler: {e}")
```

2. **重启应用**:

```bash
# Docker 环境
docker-compose restart backend

# 或直接重启进程
pkill -f "uvicorn app.main:app"
python -m uvicorn app.main:app --reload
```

3. **验证回滚**:

```bash
# 确认调度器未启动
curl http://localhost:8000/api/v1/scheduler/arp-mac/status
# 预期：{"is_running": false, ...}
```

### 回滚检查清单

- [ ] 应用正常启动，无报错
- [ ] 其他调度器（备份、IP 定位）正常运行
- [ ] 前端功能不受影响
- [ ] 数据库无异常锁或事务

---

## 📝 附录

### 参考文件

- 调度器源码：`app/services/arp_mac_scheduler.py`
- 启动逻辑：`app/main.py`
- 参考实现：`app/services/ip_location_scheduler.py`
- 参考实现：`app/services/backup_scheduler.py`
- 配置文件：`app/config.py`, `.env`

### 相关文件修改清单

| 文件 | 修改类型 | 内容 |
|------|----------|------|
| `app/services/arp_mac_scheduler.py` | 修改 | 添加 uuid 导入、APScheduler 集成、状态跟踪 |
| `app/main.py` | 修改 | 添加调度器启动代码 |
| `app/config.py` | 修改 | 添加采集间隔配置项 |
| `.env` | 修改 | 添加环境变量 `ARP_MAC_COLLECTION_INTERVAL` |
| `app/api/endpoints/scheduler.py` | 新增（中期） | 添加调度器状态 API |

### 联系信息

- 负责人：运维开发团队
- 问题反馈：飞书运维群
- 紧急联系：ops@example.com

---

**文档结束**
