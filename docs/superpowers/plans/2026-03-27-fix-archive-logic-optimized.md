# IP 定位归档逻辑修复方案（优化版）

**创建日期**: 2026-03-27
**创建者**: 乐乐 (DevOps Agent)
**优化者**: Claude
**状态**: 待审批
**风险等级**: 🟠 中（涉及数据归档逻辑，历史表可恢复，评审问题已修正）

---

## 一、问题根因

### 1.1 当前行为描述

IP 定位 Ver3 采用"离线预计算 + 在线快照查询"架构，包含两个核心数据表：

- `ip_location_current`：当前活跃的 IP 定位快照（应为空）
- `ip_location_history`：历史归档记录（143,455 条）

**异常现象**：
- `ip_location_current` 表始终为空
- 所有计算结果被立即归档到 `ip_location_history`
- 当前表无法发挥"快照查询"作用

### 1.2 根因分析

归档逻辑 `_archive_offline_ips()` 使用 **错误的时间字段** 判断设备下线：

```python
# 当前错误逻辑（ip_location_calculator.py 第 592-594 行）
offline_records = self.db.query(IPLocationCurrent).filter(
    IPLocationCurrent.last_seen < threshold_time  # ❌ 使用 ARP 采集时间
).all()
```

**问题本质**：
- `last_seen` = ARP 采集时间（可能很旧，但设备仍在线）
- `calculated_at` = IP 定位计算时间（应作为判断依据）
- 当 ARP 采集间隔 > 30 分钟时，即使设备在线也会被归档

### 1.3 代码位置确认

| 项目 | 文件位置 | 行号 |
|------|----------|------|
| `_archive_offline_ips()` 方法 | `app/services/ip_location_calculator.py` | 577-628 |
| 问题代码（使用 last_seen） | 同上 | 592-594 |
| `ARPEntry` 数据类定义 | 同上 | 29-37 |
| `_load_arp_entries()` 方法 | 同上 | 161-200 |
| `calculate_batch()` 执行顺序 | 同上 | 479-486 |

---

## 二、修复方案设计（方案 C - 两级验证）

### 2.1 核心思想

采用两级验证机制判断设备下线：

```
┌─────────────────────────────────────────────────────────┐
│                   归档判断流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  步骤 1: 时间阈值检查                                   │
│  ┌─────────────────────────────────────────────┐       │
│  │ calculated_at < now - 30min ?              │       │
│  │  否 → 保留（计算时间新鲜）                 │       │
│  │  是 → 进入步骤 2                            │       │
│  └─────────────────────────────────────────────┘       │
│                          ↓                              │
│  步骤 2: ARP 存在性检查                                  │
│  ┌─────────────────────────────────────────────┐       │
│  │ IP 在 arp_current 表中存在吗？               │       │
│  │  是 → 保留（设备仍在线）                   │       │
│  │  否 → 归档（设备已下线）                   │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 执行顺序说明

> **📌 评审意见补充**（问题 3）

`calculate_batch()` 方法中的执行顺序（第 479-486 行）：

```python
# 第 479-486 行
self._save_results(results)       # 1. 保存/更新当前表
archived = self._archive_offline_ips()  # 2. 归档下线 IP
cleaned = self._cleanup_history()       # 3. 清理历史
```

**设计意图**：
- `_save_results()` 会将刚计算的记录写入当前表，`calculated_at = datetime.now()`
- 这些记录的 `calculated_at` 是当前时间，**永远不会**满足 `calculated_at < now - 30min`
- 因此刚计算的记录不会被归档，这是正确的行为

### 2.3 数据流图

```
┌──────────────────┐     ┌──────────────────┐
│  arp_current     │     │ ip_location_     │
│  (ARP 采集表)    │     │ current          │
│                  │     │ (当前快照表)     │
│  - ip_address ──┼────►│                  │
│  - mac_address  │     │  - calculated_at │
│  - last_seen    │     │  - last_seen     │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  │ 归档逻辑判断
                                  │ (两级验证)
                                  ↓
                         ┌──────────────────┐
                         │ ip_location_     │
                         │ history          │
                         │ (历史归档表)     │
                         │                  │
                         │  - archived_at   │
                         │  - first_seen    │
                         │  - last_seen     │
                         └──────────────────┘
```

---

## 三、评审意见汇总与采纳

> **来源**: `2026-03-27-review-archive-logic.md` + 乐乐评估意见

### 3.1 评审问题与修正

| 序号 | 评审问题 | 原方案建议 | 优化后方案 | 状态 |
|------|----------|------------|------------|------|
| 1 | ARPCurrent 模型导入冲突 | `from app.models... import ARPEntry as ARPCurrent` | **不导入模型，复用 `self._arp_entries`** | ✅ 已修正 |
| 2 | 重复查询 ARP 表 | `self.db.query(ARPCurrent.ip_address).all()` | **复用 `self._arp_entries`** | ✅ 已修正 |
| 3 | 执行顺序说明缺失 | 无 | **补充说明保存后归档的设计意图** | ✅ 已补充 |

### 3.2 修正详情

#### 🔴 问题 1: ARPCurrent 模型导入冲突

> **评审来源**: 评审报告第 36-50 行

**原方案问题**：
```python
# ❌ 错误：会覆盖现有 ARPEntry 数据类（第 29-37 行已定义）
from app.models.ip_location_current import ARPEntry as ARPCurrent
```

**代码现状**：
- `ip_location_calculator.py` 第 29-37 行定义了 `ARPEntry` 数据类
- 与 SQLAlchemy 模型同名，导入会覆盖数据类

**✅ 优化方案**：不导入模型，直接复用已加载的 `self._arp_entries`

---

#### 🟡 问题 2: 重复查询 ARP 表

> **评审来源**: 评审报告第 53-62 行

**原方案问题**：
```python
# ❌ 重新查询数据库（原方案第 202 行）
current_ips = set(
    row[0] for row in self.db.query(ARPCurrent.ip_address).all()
)
```

**代码现状**：
- `_load_arp_entries()` 在 `calculate_batch()` 第 419 行已调用
- `self._arp_entries` 已包含所有 ARP 数据

**✅ 优化方案**：
```python
# 复用已加载数据，避免重复查询
current_ips = {entry.ip_address for entry in self._arp_entries}
```

**性能提升**: 避免重复数据库查询，使用内存 `set` 查找（O(1)）

---

#### ⚪ 问题 3: 执行顺序说明缺失

> **评审来源**: 评审报告第 66-78 行

**补充说明**：

`_archive_offline_ips()` 在 `_save_results()` 之后执行是**设计意图**：
- 刚保存的记录 `calculated_at = datetime.now()`
- 这些记录不满足步骤 1 的时间阈值条件
- 因此不会被误归档

---

## 四、完整实现代码

### 4.1 修改位置

**文件**: `app/services/ip_location_calculator.py`
**方法**: `_archive_offline_ips()` (第 577-628 行)

### 4.2 修正后的代码

```python
def _archive_offline_ips(self) -> int:
    """
    归档下线的 IP

    两级验证逻辑：
    1. calculated_at 超过阈值（30 分钟未重新计算）
    2. 且不在当前 ARP 表中（设备真正下线）

    注意：此方法在 _save_results() 之后调用，刚计算的记录
    calculated_at 为当前时间，不会被步骤 1 筛选。

    Returns:
        归档的记录数
    """
    threshold_minutes = int(self._settings.get('offline_threshold_minutes', '30'))
    threshold_time = datetime.now() - timedelta(minutes=threshold_minutes)

    logger.info(f"检测下线 IP，阈值: {threshold_minutes} 分钟，截止时间: {threshold_time}")

    # 步骤 1：按 calculated_at 筛选候选记录（修正：使用 calculated_at 替代 last_seen）
    candidate_records = self.db.query(IPLocationCurrent).filter(
        IPLocationCurrent.calculated_at < threshold_time
    ).all()

    if not candidate_records:
        logger.info("没有需要归档的候选记录")
        return 0

    # 步骤 2：获取当前 ARP 表中的所有 IP
    # 优化：复用已加载的 self._arp_entries，避免重复查询数据库
    # 注意：_load_arp_entries() 在 calculate_batch() 第 419 行已调用
    current_ips = {entry.ip_address for entry in self._arp_entries}

    # 步骤 3：筛选出真正下线的 IP（不在当前 ARP 表中）
    offline_records = [
        record for record in candidate_records
        if record.ip_address not in current_ips
    ]

    if not offline_records:
        logger.info(f"候选记录 {len(candidate_records)} 条均在 ARP 表中，无需归档")
        return 0

    logger.info(f"发现 {len(offline_records)} 条下线 IP 记录，开始归档...")

    # 步骤 4：移动到历史表
    for record in offline_records:
        history = IPLocationHistory(
            ip_address=record.ip_address,
            mac_address=record.mac_address,
            arp_source_device_id=record.arp_source_device_id,
            arp_device_hostname=record.arp_device_hostname,
            arp_device_ip=record.arp_device_ip,
            arp_device_location=record.arp_device_location,
            mac_hit_device_id=record.mac_hit_device_id,
            mac_device_hostname=record.mac_device_hostname,
            mac_device_ip=record.mac_device_ip,
            mac_device_location=record.mac_device_location,
            access_interface=record.access_interface,
            vlan_id=record.vlan_id,
            confidence=record.confidence,
            is_uplink=record.is_uplink,
            is_core_switch=record.is_core_switch,
            match_type=record.match_type,
            first_seen=record.calculated_at,  # 使用 calculated_at 作为 first_seen
            last_seen=record.last_seen,
            archived_at=datetime.now()
        )
        self.db.add(history)
        self.db.delete(record)

    self.db.commit()
    logger.info(f"已归档 {len(offline_records)} 条下线 IP 记录")
    return len(offline_records)
```

### 4.3 无需修改的部分

| 项目 | 说明 |
|------|------|
| 导入语句 | 不需要新增导入，复用现有 `self._arp_entries` |
| `_load_arp_entries()` | 保持不变 |
| `_save_results()` | 保持不变 |
| `_cleanup_history()` | 保持不变 |

---

## 五、测试计划

### 5.1 单元测试

#### 测试用例 1：IP 在 ARP 表中 → 不应归档

```python
def test_archive_ip_in_arp_table():
    """
    场景：IP 在 ARP 表中存在，且计算时间过期
    预期：不应归档（设备仍在线）
    """
    # 准备数据
    # 1. 创建 IPLocationCurrent 记录，calculated_at = 60 分钟前
    # 2. ARP 表中有该 IP（通过 self._arp_entries）

    # 执行归档
    archived_count = calculator._archive_offline_ips()

    # 验证
    assert archived_count == 0
    assert db.query(IPLocationCurrent).count() == 1
    assert db.query(IPLocationHistory).count() == 0
```

#### 测试用例 2：IP 不在 ARP 表中但计算时间新鲜 → 不应归档

```python
def test_archive_ip_fresh_calculation():
    """
    场景：IP 不在 ARP 表中，但 calculated_at = 5 分钟前
    预期：不应归档（可能是采集延迟）
    """
    # 准备数据
    # 1. 创建 IPLocationCurrent 记录，calculated_at = 5 分钟前
    # 2. self._arp_entries 中无该 IP

    # 执行归档
    archived_count = calculator._archive_offline_ips()

    # 验证
    assert archived_count == 0
    assert db.query(IPLocationCurrent).count() == 1
```

#### 测试用例 3：IP 不在 ARP 表中且计算时间过期 → 应归档

```python
def test_archive_ip_offline():
    """
    场景：IP 不在 ARP 表中，且 calculated_at = 60 分钟前
    预期：应归档（设备已下线）
    """
    # 准备数据
    # 1. 创建 IPLocationCurrent 记录，calculated_at = 60 分钟前
    # 2. self._arp_entries 中无该 IP

    # 执行归档
    archived_count = calculator._archive_offline_ips()

    # 验证
    assert archived_count == 1
    assert db.query(IPLocationCurrent).count() == 0
    assert db.query(IPLocationHistory).count() == 1

    # 验证历史记录字段
    history = db.query(IPLocationHistory).first()
    assert history.first_seen is not None
    assert history.archived_at is not None
```

### 5.2 集成测试

```bash
# 1. 清空当前表
sqlite3 switch_manage.db "DELETE FROM ip_location_current;"

# 2. 执行 ARP 采集
python scripts/collect_arp.py

# 3. 执行 IP 定位计算
python -m app.services.ip_location_calculator

# 4. 验证当前表有数据
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_current;"
# 预期：> 0

# 5. 验证历史表无新增（刚计算的不应被归档）
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_history;"
# 预期：与之前相同
```

---

## 六、回滚方案

### 6.1 代码回滚

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage

# 1. 恢复备份文件
BACKUP_FILE=$(ls -t app/services/ip_location_calculator.py.backup.* | head -1)
cp $BACKUP_FILE app/services/ip_location_calculator.py

# 2. 验证恢复
diff $BACKUP_FILE app/services/ip_location_calculator.py
# 预期：无输出（文件相同）
```

### 6.2 数据回滚（如归档错误）

```bash
# 查看最近归档的记录
sqlite3 switch_manage.db "
SELECT ip_address, archived_at
FROM ip_location_history
WHERE archived_at > datetime('now', '-1 hour')
ORDER BY archived_at DESC;
"

# 手动恢复误归档的记录
sqlite3 switch_manage.db "
INSERT INTO ip_location_current (
    ip_address, mac_address, arp_source_device_id,
    calculated_at, last_seen
)
SELECT
    ip_address, mac_address, arp_source_device_id,
    first_seen, last_seen
FROM ip_location_history
WHERE ip_address = '192.168.1.100'
ORDER BY archived_at DESC LIMIT 1;

DELETE FROM ip_location_history WHERE ip_address = '192.168.1.100';
"
```

---

## 七、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 归档逻辑错误导致数据丢失 | 低 | 高 | 历史表可恢复，所有字段均保留 |
| 误归档在线设备 | 低 | 中 | 两级验证机制，30 分钟缓冲时间 |
| 测试覆盖不全 | 中 | 中 | 编写 3 个核心测试用例 + 集成测试 |
| 部署后兼容性问题 | 低 | 低 | 保留备份，可快速回滚 |

---

## 八、实施检查清单

### 实施前

- [ ] 备份 `ip_location_calculator.py`
- [ ] 记录当前 `ip_location_current` 记录数
- [ ] 记录当前 `ip_location_history` 记录数

### 实施中

- [ ] 修改 `_archive_offline_ips()` 方法（第 577-628 行）
- [ ] 无需新增导入语句
- [ ] 运行单元测试 `pytest tests/test_ip_location_archive.py -v`

### 实施后

- [ ] 执行一次完整计算
- [ ] 验证 `ip_location_current` 有数据
- [ ] 验证 `ip_location_history` 无异常新增
- [ ] 检查日志无错误

---

## 附录：变更对比

### 原方案 vs 优化方案

| 项目 | 原方案 | 优化方案 |
|------|--------|----------|
| ARPCurrent 导入 | `from app.models.ip_location_current import ARPEntry as ARPCurrent` | **无需导入** |
| 获取当前 IP 列表 | `self.db.query(ARPCurrent.ip_address).all()` | `{e.ip_address for e in self._arp_entries}` |
| 执行顺序说明 | 无 | **补充说明** |
| 性能 | 额外数据库查询 | **复用已加载数据，零额外查询** |
| 代码复杂度 | 需要处理命名冲突 | **简洁，无额外依赖** |

### 关键代码修改对比

```python
# 原方案（有问题）
from app.models.ip_location_current import ARPEntry as ARPCurrent  # ❌ 命名冲突

current_ips = set(
    row[0] for row in self.db.query(ARPCurrent.ip_address).all()  # ❌ 重复查询
)

# 优化方案（推荐）
# 无需导入，复用已有数据
current_ips = {entry.ip_address for entry in self._arp_entries}  # ✅ 零额外查询
```

---

**审批状态**: 待审批
**下一步**: 等待审批后执行实施步骤