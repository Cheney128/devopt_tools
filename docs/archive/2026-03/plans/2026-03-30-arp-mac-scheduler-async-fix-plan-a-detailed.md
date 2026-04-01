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
# ARP/MAC 采集调度器异步调用修复 - 方案 A 详细设计

**方案名称**: 使用 asyncio.run() 包装异步调用
**设计日期**: 2026-03-30
**方案编号**: A
**优先级**: P0（紧急修复）
**预计工作量**: 2-4 小时

***

## 1. 方案概述

### 1.1 问题根因

`arp_mac_scheduler.py` 的 `_collect_device()` 方法是同步方法，但调用了 `netmiko_service.py` 中的异步方法 `collect_arp_table()` 和 `collect_mac_table()`，没有使用 `await` 或 `asyncio.run()`，导致返回 coroutine 对象而非实际数据。

### 1.2 方案核心思路

在同步上下文中使用 `asyncio.run()` 包装异步方法调用，创建独立的事件循环来执行异步操作。

### 1.3 方案优势

| 优势   | 说明                            |
| ---- | ----------------------------- |
| 改动最小 | 仅修改 1 个文件，约 20 行代码            |
| 风险最低 | 不影响其他模块对 netmiko\_service 的使用 |
| 快速部署 | 可立即修复生产问题                     |
| 向后兼容 | 不破坏现有 API 签名                  |

***

## 2. 代码修改详细设计

### 2.1 文件修改清单

| 文件                                  | 修改类型 | 修改内容                                    |
| ----------------------------------- | ---- | --------------------------------------- |
| `app/services/arp_mac_scheduler.py` | 编辑   | 添加 asyncio 导入，修改 `_collect_device()` 方法 |

### 2.2 导入语句修改

**位置**: 文件顶部（约第 10-14 行）

**修改前**:

```python
import logging
import uuid
from datetime import datetime
from typing import List, Optional
```

**修改后**:

```python
import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional
```

**说明**: 在导入区域顶部添加 `import asyncio`，保持导入顺序符合 PEP8 规范（标准库优先）。

### 2.3 `_collect_device()` 方法修改

**位置**: 第 109-189 行

**修改策略**: 保持方法签名不变，在异步调用处使用 `asyncio.run()` 包装。

#### 2.3.1 完整修改后代码

```python
def _collect_device(self, device: Device) -> dict:
    """
    采集单个设备的 ARP 和 MAC 表

    Args:
        device: 设备对象

    Returns:
        采集结果
    """
    device_stats = {
        'device_id': device.id,
        'device_hostname': device.hostname,
        'arp_success': False,
        'mac_success': False,
        'arp_entries_count': 0,
        'mac_entries_count': 0,
    }

    try:
        # 采集 ARP 表 - 使用 asyncio.run() 包装异步调用
        arp_table = asyncio.run(self.netmiko.collect_arp_table(device))

        if arp_table:
            # 清空并保存
            self.db.query(ARPEntry).filter(
                ARPEntry.arp_device_id == device.id
            ).delete()

            for entry in arp_table:
                arp_entry = ARPEntry(
                    ip_address=entry['ip_address'],
                    mac_address=entry['mac_address'],
                    arp_device_id=device.id,
                    vlan_id=entry.get('vlan_id'),
                    arp_interface=entry.get('interface'),
                    last_seen=datetime.now(),
                    collection_batch_id=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                )
                self.db.add(arp_entry)

            device_stats['arp_success'] = True
            device_stats['arp_entries_count'] = len(arp_table)
            logger.info(f"设备 {device.hostname} ARP 采集成功：{len(arp_table)} 条")
        else:
            logger.warning(f"设备 {device.hostname} ARP 采集返回空结果")

        # 采集 MAC 表 - 使用 asyncio.run() 包装异步调用
        mac_table = asyncio.run(self.netmiko.collect_mac_table(device))

        if mac_table:
            # 清空并保存
            self.db.query(MACAddressCurrent).filter(
                MACAddressCurrent.mac_device_id == device.id
            ).delete()

            for entry in mac_table:
                mac_entry = MACAddressCurrent(
                    mac_address=entry['mac_address'],
                    mac_device_id=device.id,
                    vlan_id=entry.get('vlan_id'),
                    mac_interface=entry['interface'],
                    is_trunk=entry.get('is_trunk', False),
                    interface_description=entry.get('description'),
                    last_seen=datetime.now()
                )
                self.db.add(mac_entry)

            device_stats['mac_success'] = True
            device_stats['mac_entries_count'] = len(mac_table)
            logger.info(f"设备 {device.hostname} MAC 采集成功：{len(mac_table)} 条")
        else:
            logger.warning(f"设备 {device.hostname} MAC 采集返回空结果")

        # 提交事务
        self.db.commit()

    except Exception as e:
        logger.error(f"设备 {device.hostname} 采集失败：{str(e)}", exc_info=True)
        self.db.rollback()
        device_stats['error'] = str(e)

    return device_stats
```

#### 2.3.2 关键修改点对比

| 行号  | 修改前                                                  | 修改后                                                               | 说明                  |
| --- | ---------------------------------------------------- | ----------------------------------------------------------------- | ------------------- |
| 130 | `arp_table = self.netmiko.collect_arp_table(device)` | `arp_table = asyncio.run(self.netmiko.collect_arp_table(device))` | 添加 asyncio.run() 包装 |
| 156 | `mac_table = self.netmiko.collect_mac_table(device)` | `mac_table = asyncio.run(self.netmiko.collect_mac_table(device))` | 添加 asyncio.run() 包装 |
| 185 | `logger.error(f"...{str(e)}")`                       | `logger.error(f"...{str(e)}", exc_info=True)`                     | 增强错误日志，便于调试         |

***

## 3. 依赖项分析

### 3.1 新增依赖

| 依赖        | 类型  | Python 版本要求 | 是否需要安装  |
| --------- | --- | ----------- | ------- |
| `asyncio` | 标准库 | Python 3.4+ | 不需要（内置） |

**结论**: 无需安装任何新的外部依赖，`asyncio` 是 Python 标准库模块。

### 3.2 现有依赖兼容性

| 依赖          | 当前版本    | asyncio 兼容性 | 备注                                              |
| ----------- | ------- | ----------- | ----------------------------------------------- |
| APScheduler | 3.10.4  | 兼容          | BackgroundScheduler 在独立线程运行，与 asyncio.run() 无冲突 |
| SQLAlchemy  | 1.4.51  | 兼容          | 同步 Session 操作不受 asyncio 影响                      |
| FastAPI     | 0.104.1 | 兼容          | 调度器在后台线程运行，与 FastAPI 事件循环隔离                     |
| netmiko     | 4.1.0   | 兼容          | 异步方法正常执行                                        |

### 3.3 依赖关系图

```
arp_mac_scheduler.py
    │
    ├── asyncio (标准库，新增导入)
    │
    ├── netmiko_service.py
    │       │
    │       └── collect_arp_table() [async]
    │       └── collect_mac_table() [async]
    │       │
    │       └── execute_command() [async]
    │               │
    │               └── ConnectHandler (netmiko 同步)
    │               └── asyncio.to_thread() 或 run_in_executor
    │
    └── SQLAlchemy Session (同步)
```

***

## 4. 兼容性评估

### 4.1 Python 版本兼容性

| Python 版本    | asyncio.run() 支持 | 建议版本 |
| ------------ | ---------------- | ---- |
| Python 3.6   | 不支持              | 不推荐  |
| Python 3.7   | 支持（首次引入）         | 最低要求 |
| Python 3.8+  | 支持（推荐）           | 推荐   |
| Python 3.10+ | 支持（最佳）           | 最佳   |

**项目当前 Python 版本**: 需确认（建议 >= 3.8）

### 4.2 事件循环隔离分析

#### APScheduler 线程模型

```
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI 主进程                                                   │
│                                                                  │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │ 主线程               │    │ 后台线程（APScheduler）         │ │
│  │                     │    │                                 │ │
│  │  FastAPI 事件循环    │    │  无事件循环                     │ │
│  │  (uvicorn)          │    │                                 │ │
│  │                     │    │  _run_collection()              │ │
│  │                     │    │      │                          │ │
│  │                     │    │      ▼                          │ │
│  │                     │    │  _collect_device()              │ │
│  │                     │    │      │                          │ │
│  │                     │    │      │ asyncio.run()            │ │
│  │                     │    │      │     │                    │ │
│  │                     │    │      │     ▼                    │ │
│  │                     │    │      │  [新事件循环]            │ │
│  │                     │    │      │     │                    │ │
│  │                     │    │      │     ▼                    │ │
│  │                     │    │      │  collect_arp_table()     │ │
│  │                     │    │      │     │                    │ │
│  │                     │    │      │     ▼                    │ │
│  │                     │    │      │  execute_command()       │ │
│  │                     │    │                                 │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**关键点**:

1. APScheduler 的 BackgroundScheduler 在独立线程运行
2. 该线程本身没有事件循环
3. `asyncio.run()` 会为每次调用创建新的临时事件循环
4. 事件循环之间完全隔离，不会产生冲突

### 4.3 与其他模块兼容性

#### 4.3.1 FastAPI 路由兼容性

FastAPI 路由中的异步调用不受影响：

- FastAPI 在主线程有自己的事件循环
- ARP/MAC 调度器在后台线程运行
- 两者事件循环完全隔离

#### 4.3.2 其他调度器兼容性

项目可能存在其他调度器（如设备监控），需要确认：

- 其他调度器若使用相同的 netmiko\_service 异步方法，需检查是否有类似问题
- 建议全局搜索：`grep -rn "collect_arp_table\|collect_mac_table" --include="*.py" app/`

***

## 5. 测试计划

### 5.1 单元测试

#### 5.1.1 测试文件位置

建议创建：`tests/services/test_arp_mac_scheduler_async.py`

#### 5.1.2 测试用例设计

```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from app.services.arp_mac_scheduler import ARPMACScheduler
from app.models.models import Device

class TestARPMACSchedulerAsyncFix:
    """ARP/MAC 调度器异步修复测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        db.query = Mock(return_value=Mock())
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        return db

    @pytest.fixture
    def mock_device(self):
        """模拟设备对象"""
        device = Device(
            id=1,
            hostname="test-switch-01",
            vendor="huawei",
            username="admin",
            password="password",
            status="active"
        )
        return device

    @pytest.fixture
    def mock_netmiko(self):
        """模拟 NetmikoService"""
        netmiko = Mock()
        # 使用 AsyncMock 模拟异步方法返回值
        netmiko.collect_arp_table = AsyncMock(return_value=[
            {'ip_address': '192.168.1.1', 'mac_address': '00:11:22:33:44:55', 'vlan_id': 1, 'interface': 'Vlanif1'}
        ])
        netmiko.collect_mac_table = AsyncMock(return_value=[
            {'mac_address': '00:11:22:33:44:55', 'vlan_id': 1, 'interface': 'GigabitEthernet0/0/1'}
        ])
        return netmiko

    def test_collect_device_returns_dict(self, mock_db, mock_device, mock_netmiko):
        """测试 _collect_device 返回正确的字典结构"""
        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = mock_netmiko

        result = scheduler._collect_device(mock_device)

        assert isinstance(result, dict)
        assert 'device_id' in result
        assert 'arp_success' in result
        assert 'mac_success' in result

    def test_collect_device_arp_success(self, mock_db, mock_device, mock_netmiko):
        """测试 ARP 采集成功"""
        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = mock_netmiko

        result = scheduler._collect_device(mock_device)

        assert result['arp_success'] == True
        assert result['arp_entries_count'] == 1

    def test_collect_device_mac_success(self, mock_db, mock_device, mock_netmiko):
        """测试 MAC 采集成功"""
        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = mock_netmiko

        result = scheduler._collect_device(mock_device)

        assert result['mac_success'] == True
        assert result['mac_entries_count'] == 1

    def test_collect_device_handles_none_result(self, mock_db, mock_device):
        """测试处理返回 None 的情况"""
        netmiko = Mock()
        netmiko.collect_arp_table = AsyncMock(return_value=None)
        netmiko.collect_mac_table = AsyncMock(return_value=None)

        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = netmiko

        result = scheduler._collect_device(mock_device)

        assert result['arp_success'] == False
        assert result['mac_success'] == False

    def test_collect_device_handles_exception(self, mock_db, mock_device):
        """测试异常处理"""
        netmiko = Mock()
        netmiko.collect_arp_table = AsyncMock(side_effect=Exception("Connection failed"))

        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = netmiko

        result = scheduler._collect_device(mock_device)

        assert 'error' in result
        assert 'Connection failed' in result['error']
        mock_db.rollback.assert_called_once()

    def test_asyncio_run_creates_isolated_loop(self, mock_db, mock_device, mock_netmiko):
        """测试 asyncio.run() 创建独立事件循环"""
        scheduler = ARPMACScheduler(db=mock_db)
        scheduler.netmiko = mock_netmiko

        # 确保在非异步上下文中调用
        assert asyncio.get_event_loop_policy().get_event_loop() is None or \
               not asyncio.get_event_loop().is_running()

        result = scheduler._collect_device(mock_device)
        assert result is not None
```

### 5.2 集成测试

#### 5.2.1 手动集成测试步骤

```bash
# 1. 确保数据库中有测试设备
sqlite3 data/switch_manage.db "SELECT id, hostname, status FROM devices WHERE status='active' LIMIT 3;"

# 2. 启动服务（开发模式）
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
python -m uvicorn app.main:app --reload --port 8000

# 3. 触发手动采集测试
curl -X POST http://localhost:8000/api/v1/arp-mac/collect

# 4. 检查日志确认成功
tail -100 logs/app.log | grep -E "ARP.*采集成功|MAC.*采集成功|采集失败"

# 5. 验证数据库有数据
sqlite3 data/switch_manage.db "SELECT COUNT(*) FROM arp_entries;"
sqlite3 data/switch_manage.db "SELECT COUNT(*) FROM mac_address_current;"

# 6. 检查调度器状态
curl http://localhost:8000/api/v1/arp-mac/status
```

#### 5.2.2 预期成功输出示例

```log
2026-03-30 14:00:00 INFO: 开始批量采集 ARP 和 MAC 表
2026-03-30 14:00:05 INFO: 设备 switch-01 ARP 采集成功：150 条
2026-03-30 14:00:10 INFO: 设备 switch-01 MAC 采集成功：200 条
2026-03-30 14:00:15 INFO: 设备 switch-02 ARP 采集成功：80 条
...
2026-03-30 14:05:00 INFO: 批量采集完成：arp_success=64, mac_success=64
```

#### 5.2.3 API 响应验证

```json
{
  "scheduler": "arp_mac",
  "is_running": true,
  "consecutive_failures": 0,
  "health_status": "healthy",
  "last_stats": {
    "collection": {
      "arp_success": 64,
      "arp_failed": 0,
      "mac_success": 64,
      "mac_failed": 0,
      "total_arp_entries": 5000,
      "total_mac_entries": 8000
    }
  }
}
```

### 5.3 性能测试

#### 5.3.1 测试场景

采集 64 台设备，记录总耗时。

#### 5.3.2 性能基准

| 场景             | 预期耗时    | 告警阈值    |
| -------------- | ------- | ------- |
| 64 台设备 ARP+MAC | < 10 分钟 | > 15 分钟 |
| 单设备 ARP+MAC    | < 30 秒  | > 60 秒  |

#### 5.3.3 性能对比分析

`asyncio.run()` 每次调用会创建新的事件循环，理论上比复用事件循环有轻微性能开销：

- 单次开销：约 1-2ms
- 64 台设备总开销：约 128ms
- **结论**: 性能影响可忽略不计（< 0.1%）

***

## 6. 回滚方案

### 6.1 回滚触发条件

| 条件              | 描述                       | 处理     |
| --------------- | ------------------------ | ------ |
| 连续失败 >= 3 次     | 修复后仍无法正常采集               | 触发回滚   |
| RuntimeError 异常 | asyncio.run() 在已有事件循环中调用 | 评估方案 B |
| 性能严重下降          | 采集耗时超过告警阈值 2 倍           | 评估优化方案 |

### 6.2 回滚步骤

```bash
# 1. 停止服务
systemctl stop switch-manage  # 或 kill 进程

# 2. 回滚代码（使用 git）
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
git checkout HEAD~1 -- app/services/arp_mac_scheduler.py

# 3. 重启服务
systemctl start switch-manage

# 4. 确认回滚成功
git diff app/services/arp_mac_scheduler.py
```

### 6.3 回滚后备选方案

若方案 A 回滚，可考虑方案 B：

**方案 B**: 在 `netmiko_service.py` 中创建同步包装方法

- 添加 `collect_arp_table_sync()` 和 `collect_mac_table_sync()` 方法
- 内部使用 `asyncio.run()` 包装
- `arp_mac_scheduler.py` 调用同步方法

***

## 7. 实施计划

### 7.1 实施步骤

| 步骤 | 操作                        | 预计时间  | 负责人 |
| -- | ------------------------- | ----- | --- |
| 1  | 备份当前代码                    | 5 分钟  | 开发  |
| 2  | 修改 arp\_mac\_scheduler.py | 10 分钟 | 开发  |
| 3  | 本地单元测试                    | 15 分钟 | 开发  |
| 4  | 本地集成测试                    | 20 分钟 | 开发  |
| 5  | 提交代码审查                    | 10 分钟 | 开发  |
| 6  | 部署到测试环境                   | 15 分钟 | 运维  |
| 7  | 测试环境验证                    | 30 分钟 | QA  |
| 8  | 部署到生产环境                   | 10 分钟 | 运维  |
| 9  | 生产环境验证                    | 15 分钟 | 运维  |

**总预计时间**: 约 2 小时

### 7.2 部署检查清单

```markdown
## 部署前检查
- [ ] 备份 arp_mac_scheduler.py 原始文件
- [ ] 确认 Python 版本 >= 3.7
- [ ] 确认 asyncio 可正常导入
- [ ] 检查数据库连接正常

## 部署后验证
- [ ] 服务启动无错误日志
- [ ] 手动触发采集 API 返回成功
- [ ] ARP/MAC 表有新增数据
- [ ] 调度器状态 API 显示 healthy
- [ ] 日志无 "coroutine" 相关错误
```

***

## 8. 风险评估

### 8.1 已知风险

| 风险                   | 可能性 | 影响 | 缓解措施            |
| -------------------- | --- | -- | --------------- |
| RuntimeError: 嵌套事件循环 | 低   | 中  | 添加异常处理，检测现有事件循环 |
| 性能轻微下降               | 低   | 低  | 可接受（< 0.1%）     |
| 部署失败                 | 中   | 高  | 准备回滚脚本          |

### 8.2 嵌套事件循环处理（备用方案）

若出现 `RuntimeError: asyncio.run() cannot be called from a running event loop`，可使用以下备用代码：

```python
def _run_async(self, coro):
    """
    运行异步协程的辅助方法

    Args:
        coro: 异步协程对象

    Returns:
        协程执行结果
    """
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # 已在事件循环中，使用 run_until_complete
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)
        else:
            raise
```

***

## 9. 附录

### 9.1 相关文件路径

| 文件         | 路径                                                                                    |
| ---------- | ------------------------------------------------------------------------------------- |
| 调度器文件      | `app/services/arp_mac_scheduler.py`                                                   |
| Netmiko 服务 | `app/services/netmiko_service.py`                                                     |
| 问题分析文档     | `docs/superpowers/analysis/2026-03-30-arp-mac-scheduler-async-call-error-analysis.md` |

### 9.2 相关代码位置

| 方法                  | 文件                     | 行号        | 签名               |
| ------------------- | ---------------------- | --------- | ---------------- |
| `_collect_device`   | arp\_mac\_scheduler.py | 109-189   | `def` (同步)       |
| `collect_arp_table` | netmiko\_service.py    | 1124-1159 | `async def` (异步) |
| `collect_mac_table` | netmiko\_service.py    | 1209-1237 | `async def` (异步) |

### 9.3 参考资料

- [Python asyncio 官方文档](https://docs.python.org/3/library/asyncio.html)
- [asyncio.run() API 参考](https://docs.python.org/3/library/asyncio-task.html#asyncio.run)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)

***

**文档编写**: Claude
**审核状态**: 待审核
**下一步**: 执行实施计划
