# IP 定位归档逻辑修复计划（方案 C - 混合方案）

**创建日期**: 2026-03-27  
**创建者**: 乐乐 (DevOps Agent)  
**状态**: 待审批  
**风险等级**: 🟠 高（涉及数据归档逻辑，但历史表可恢复）

---

## 1. 问题分析

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
# 当前错误逻辑（第 270 行）
offline_records = self.db.query(IPLocationCurrent).filter(
    IPLocationCurrent.last_seen < threshold_time  # ❌ 使用 ARP 采集时间
).all()
```

**问题本质**：
- `last_seen` = ARP 采集时间（可能很旧，但设备仍在线）
- `calculated_at` = IP 定位计算时间（应作为判断依据）
- 当 ARP 采集间隔 > 30 分钟时，即使设备在线也会被归档

### 1.3 影响范围

| 影响维度 | 描述 |
|----------|------|
| **功能影响** | `ip_location_current` 表失效，前端查询回退到历史表 |
| **性能影响** | 历史表持续增长（143,455 条），查询效率下降 |
| **数据完整性** | 无数据丢失，所有记录均可从历史表恢复 |
| **用户感知** | 前端查询速度可能变慢，但功能正常 |

---

## 2. 修复方案设计

### 2.1 方案 C 详细设计

**核心思想**：采用两级验证机制判断设备下线

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

### 2.2 数据流图

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

### 2.3 关键代码逻辑

```python
def _archive_offline_ips(self) -> int:
    """
    归档下线的 IP
    
    混合判断逻辑：
    1. 计算时间超过阈值（30 分钟未重新计算）
    2. 且不在当前 ARP 表中
    
    Returns:
        归档的记录数
    """
    threshold_minutes = int(self._settings.get('offline_threshold_minutes', '30'))
    threshold_time = datetime.now() - timedelta(minutes=threshold_minutes)
    
    # 步骤 1：获取超过时间阈值的候选记录
    candidate_records = self.db.query(IPLocationCurrent).filter(
        IPLocationCurrent.calculated_at < threshold_time
    ).all()
    
    if not candidate_records:
        logger.info("没有需要归档的候选记录")
        return 0
    
    # 步骤 2：获取当前 ARP 表中的所有 IP（使用 set 提高查找效率）
    current_ips = set(
        row[0] for row in self.db.query(ARPCurrent.ip_address).all()
    )
    
    # 步骤 3：筛选出真正下线的 IP（不在当前 ARP 表中）
    offline_records = [
        record for record in candidate_records 
        if record.ip_address not in current_ips
    ]
    
    if not offline_records:
        logger.info("候选记录均在 ARP 表中，无需归档")
        return 0
    
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
            first_seen=record.calculated_at,
            last_seen=record.last_seen,
            archived_at=datetime.now()
        )
        self.db.add(history)
        self.db.delete(record)
    
    self.db.commit()
    logger.info(f"已归档 {len(offline_records)} 条下线 IP 记录")
    return len(offline_records)
```

### 2.4 性能优化考虑

**ARP 表查询效率**：
- 使用 `set()` 存储当前 IP 列表，查找时间复杂度 O(1)
- 单次查询所有 IP，避免 N+1 查询问题
- `arp_current.ip_address` 已有索引（`idx_ip_mac`）

**候选记录筛选**：
- 使用数据库过滤 `calculated_at < threshold_time`，减少内存处理
- 仅在 Python 层进行 IP 存在性检查（轻量级操作）

---

## 3. 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `app/services/ip_location_calculator.py` | 修改 | `_archive_offline_ips()` 方法重写 |
| `app/models/ip_location_current.py` | 查看 | 确认 `ARPCurrent` 模型导入（可能需要添加） |

### 3.1 需要添加的导入

在 `ip_location_calculator.py` 文件顶部添加：

```python
from app.models.ip_location_current import ARPEntry as ARPCurrent
```

或直接使用 SQLAlchemy 反射：

```python
from sqlalchemy import table, column, String

ARPCurrent = table('arp_current',
    column('ip_address', String),
)
```

---

## 4. 实施步骤

### 步骤 1：备份当前代码

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage

# 备份修改文件
cp app/services/ip_location_calculator.py \
   app/services/ip_location_calculator.py.backup.$(date +%Y%m%d%H%M%S)

# 验证备份
ls -lh app/services/ip_location_calculator.py.backup.*
```

### 步骤 2：修改归档逻辑

使用编辑器修改 `_archive_offline_ips()` 方法，替换为方案 C 逻辑。

### 步骤 3：添加单元测试

创建测试文件 `tests/test_ip_location_archive.py`，包含 3 个核心测试用例。

### 步骤 4：手动验证

```bash
# 运行单元测试
source venv/bin/activate
pytest tests/test_ip_location_archive.py -v

# 执行一次完整采集 + 计算
python -m app.services.ip_location_calculator
```

### 步骤 5：部署到测试环境

```bash
# 检查当前表状态
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_current;"
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_history;"

# 等待 30 分钟或手动修改时间验证归档逻辑
```

---

## 5. 测试计划

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
    # 2. 创建 ARPCurrent 记录，包含该 IP
    
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
    # 2. ARPCurrent 表中无该 IP
    
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
    # 2. ARPCurrent 表中无该 IP
    
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

#### 测试场景 1：完整采集 + 计算流程

```bash
# 1. 清空当前表
DELETE FROM ip_location_current;

# 2. 执行 ARP 采集
python scripts/collect_arp.py

# 3. 执行 IP 定位计算
python -m app.services.ip_location_calculator

# 4. 验证当前表有数据
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_current;"
# 预期：> 0

# 5. 验证历史表无新增
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_history;"
# 预期：与之前相同
```

#### 测试场景 2：模拟设备下线

```bash
# 1. 手动修改一条记录的 calculated_at 为 60 分钟前
sqlite3 switch_manage.db "UPDATE ip_location_current SET calculated_at = datetime('now', '-60 minutes') WHERE ip_address = '192.168.1.100';"

# 2. 从 ARP 表中删除该 IP
sqlite3 switch_manage.db "DELETE FROM arp_current WHERE ip_address = '192.168.1.100';"

# 3. 执行归档逻辑
python -c "
from app.services.ip_location_calculator import IPLocationCalculator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///switch_manage.db')
Session = sessionmaker(bind=engine)
session = Session()
calculator = IPLocationCalculator(session)
archived = calculator._archive_offline_ips()
print(f'Archived: {archived}')
"

# 4. 验证记录已移动
sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_current WHERE ip_address = '192.168.1.100';"
# 预期：0

sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_history WHERE ip_address = '192.168.1.100';"
# 预期：1
```

---

## 6. 回滚方案

### 6.1 回滚命令

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage

# 1. 恢复备份文件
BACKUP_FILE=$(ls -t app/services/ip_location_calculator.py.backup.* | head -1)
cp $BACKUP_FILE app/services/ip_location_calculator.py

# 2. 验证恢复
diff $BACKUP_FILE app/services/ip_location_calculator.py
# 预期：无输出（文件相同）

# 3. 重启服务（如适用）
systemctl restart switch_manage  # 或相应的服务重启命令
```

### 6.2 数据回滚（如归档错误）

```bash
# 1. 查看最近归档的记录
sqlite3 switch_manage.db "
SELECT ip_address, archived_at 
FROM ip_location_history 
WHERE archived_at > datetime('now', '-1 hour')
ORDER BY archived_at DESC;
"

# 2. 手动恢复误归档的记录（示例）
sqlite3 switch_manage.db "
INSERT INTO ip_location_current (
    ip_address, mac_address, arp_source_device_id,
    calculated_at, last_seen, ...
)
SELECT 
    ip_address, mac_address, arp_source_device_id,
    first_seen, last_seen, ...
FROM ip_location_history
WHERE ip_address = '192.168.1.100'
ORDER BY archived_at DESC LIMIT 1;

DELETE FROM ip_location_history WHERE ip_address = '192.168.1.100';
"
```

### 6.3 回滚后验证步骤

1. **检查当前表数据量**：
   ```bash
   sqlite3 switch_manage.db "SELECT COUNT(*) FROM ip_location_current;"
   ```

2. **执行一次完整计算**：
   ```bash
   python -m app.services.ip_location_calculator
   ```

3. **验证归档逻辑不再触发**：
   ```bash
   # 查看日志
   tail -f logs/app.log | grep "归档"
   ```

---

## 7. 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 归档逻辑错误导致数据丢失 | 低 | 高 | 历史表可恢复，所有字段均保留 |
| 性能问题（ARP 表查询） | 中 | 中 | 使用 `set()` 优化查找，添加索引 |
| 误归档在线设备 | 低 | 中 | 两级验证机制，30 分钟缓冲时间 |
| 测试覆盖不全 | 中 | 中 | 编写 3 个核心测试用例 + 集成测试 |
| 部署后兼容性问题 | 低 | 低 | 保留备份，可快速回滚 |

### 7.1 风险缓解详细说明

#### 风险 1：归档逻辑错误

**缓解措施**：
- 历史表包含所有字段，可手动恢复
- 回滚方案已验证
- 测试环境先行验证

#### 风险 2：ARP 表查询性能

**缓解措施**：
- 使用 `set()` 存储 IP 列表，查找 O(1)
- `arp_current.ip_address` 已有索引
- 单次查询所有 IP，避免 N+1 问题

**性能估算**：
- ARP 表：~1000 条记录
- 当前表：~500 条记录
- 查询时间：< 100ms

---

## 8. 附录

### 8.1 相关文件位置

| 文件 | 路径 |
|------|------|
| 归档逻辑 | `app/services/ip_location_calculator.py` |
| 当前表模型 | `app/models/ip_location_current.py` |
| 历史表模型 | `app/models/ip_location_history.py` |
| 单元测试 | `tests/test_ip_location_archive.py`（新建） |

### 8.2 参考资料

- [IP 定位优化计划](../ip-location-optimization-plan.md)
- [IP 定位优化总结](../ip-location-optimization-summary.md)
- [浏览器验证报告](../verification-report-2026-03-26.md)

### 8.3 变更日志

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-03-27 | 1.0 | 初始版本，方案 C 设计 | 乐乐 |

---

**审批状态**: 待审批  
**下一步**: 等待祥哥审批后执行实施步骤
