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
# ARP/MAC 采集调度器运行时错误分析报告

**分析日期**: 2026-03-30
**分析者**: Claude Code (Systematic Debugging)
**严重级别**: 高 - 影响生产数据采集

***

## 一、问题概述

ARP/MAC 采集调度器在修复异步调用问题后，运行时发现两个新的错误：

| 问题                    | 严重程度 | 影响范围                 |
| --------------------- | ---- | -------------------- |
| MAC 地址表解析失败           | 高    | 华为/H3C 设备 MAC 采集全部失败 |
| 数据库唯一键冲突 + Session 回滚 | 高    | ARP 数据采集异常，事务状态损坏    |

***

## 二、问题 1：MAC 地址表解析失败

### 2.1 现象描述

- **错误信息**: `Error parsing MAC table: no such group`
- **影响设备**: 模块 33-R03-业务接入
- **数据对比**:
  - `display arp` 命令返回 10 条记录 ✓
  - `display mac-address` 命令返回 691 个 items ✗ (解析失败)
  - 原始输出长度: 57124 characters (数据量大)

### 2.2 根因分析

**定位文件**: `app/services/netmiko_service.py:764-771`

**问题代码**:

```python
# 第 764 行 - 华为 MAC 地址表解析正则
match = re.search(r'([0-9A-Fa-f-]+)\s*(?:[/-]\s*(\d+)/\S*\s*(\S+))', line)
if match:
    mac_raw = match.group(1)
    mac_entries.append({
        "mac_address": mac_raw.upper(),
        "vlan_id": int(match.group(2)),
        "interface": match.group(3).strip(),
        "address_type": match.group(4).lower()  # ❌ BUG: group(4) 不存在!
    })
```

**错误原因**:

1. **正则表达式设计错误**: 该正则只有 **3 个捕获组**，但代码尝试访问 `group(4)`
   - `group(1)`: MAC地址 `([0-9A-Fa-f-]+)`
   - `group(2)`: VLAN号 `(\d+)`
   - `group(3)`: 接口名 `(\S+)`
   - `group(4)`: **不存在!**
2. **正则表达式无法匹配完整格式**: 华为 MAC 地址表实际输出格式：
   ```
   MAC Address    VLAN/VSI    Learned-From        Type
   0011-2233-4455 1/-         GE1/0/1             dynamic
   ```
   当前正则无法正确提取 `Type` 字段。
3. **异常吞没**: 第 714-715 行捕获异常但仅打印日志，返回空列表：
   ```python
   except Exception as e:
       print(f"Error parsing MAC table: {e}")
   ```

### 2.3 修复方案

**方案 A: 修复正则表达式** (推荐)

```python
def _parse_huawei_mac_table(self, output: str) -> List[Dict[str, Any]]:
    """解析华为/H3C MAC地址表"""
    mac_entries = []

    # 华为/H3C MAC地址表格式：
    # MAC Address    VLAN/VSI    Learned-From        Type
    # 0011-2233-4455 1/-         GE1/0/1             dynamic

    lines = output.strip().split('\n')
    for line in lines:
        # 跳过标题行和空行
        if not line.strip() or re.match(r'MAC\s+Address', line, re.IGNORECASE):
            continue

        # 使用更精确的正则匹配华为格式
        # 格式: MAC地址 VLAN/VSI 接口 类型
        # 修正后的正则: 4 个捕获组
        match = re.search(
            r'([0-9A-Fa-f-]+)\s+'  # group(1): MAC地址
            r'(\d+)/[^\s]*\s+'     # group(2): VLAN号 (格式: 1/- 或 1/100)
            r'(\S+)\s+'            # group(3): 接口名
            r'(\S+)',              # group(4): 类型 (dynamic/static等)
            line
        )
        if match:
            mac_entries.append({
                "mac_address": match.group(1).upper(),
                "vlan_id": int(match.group(2)),
                "interface": match.group(3).strip(),
                "address_type": match.group(4).lower()
            })

    return mac_entries
```

**方案 B: 使用空格分隔的简单解析**

```python
def _parse_huawei_mac_table(self, output: str) -> List[Dict[str, Any]]:
    """解析华为/H3C MAC地址表 - 使用空格分隔"""
    mac_entries = []
    lines = output.strip().split('\n')

    for line in lines:
        if not line.strip() or 'MAC Address' in line:
            continue

        parts = line.split()
        if len(parts) >= 4:
            # 华为格式: MAC VLAN/VSI 接口 类型
            mac_raw = parts[0]
            vlan_part = parts[1]  # 格式: "1/-" 或 "10/100"

            # 提取 VLAN 号
            vlan_id = int(vlan_part.split('/')[0]) if '/' in vlan_part else int(vlan_part)

            mac_entries.append({
                "mac_address": mac_raw.upper(),
                "vlan_id": vlan_id,
                "interface": parts[2],
                "address_type": parts[3].lower() if len(parts) > 3 else "dynamic"
            })

    return mac_entries
```

***

## 三、问题 2：数据库唯一键冲突 + Session 事务回滚

### 3.1 现象描述

- **错误信息 1**: `pymysql.err.IntegrityError: Duplicate entry '3cc7-86b4-7298-214' for key 'uq_arp_current_ip_device'`
- **错误信息 2**: `This Session's transaction has been rolled back`
- **冲突键值**: `ip_address=3cc7-86b4-7298` + `arp_device_id=214`

### 3.2 根因分析

**定位文件**: `app/services/arp_mac_scheduler.py:147-207`

**问题流程**:

```
1. 删除旧数据 (第 147-149 行)
   self.db.query(ARPEntry).filter(ARPEntry.arp_device_id == device.id).delete()

2. 添加新数据 (第 151-161 行)
   for entry in arp_table:
       arp_entry = ARPEntry(...)
       self.db.add(arp_entry)

3. 提交事务 (第 202 行)
   self.db.commit()
```

**问题原因**:

1. **唯一键约束未在代码中定义**: 数据库存在 `uq_arp_current_ip_device` 约束，但 `ARPEntry` 模型 (`app/models/ip_location_current.py`) 未声明：
   ```python
   # 当前模型定义 - 缺少唯一约束
   __table_args__ = (
       Index('idx_ip_mac', 'ip_address', 'mac_address'),
   )
   ```
2. **并发采集导致重复插入**: 多设备采集时，同一 IP 可能被多台设备同时发现，先执行的 `delete()` 只删除了该设备的数据，其他设备的同名 IP 数据仍存在。
3. **Session 状态损坏**: 唯一键冲突后 Session 进入 "rolled back" 状态，后续数据库操作全部失败：
   ```python
   # 第 205-209 行的错误处理
   except Exception as e:
       self.db.rollback()  # Session 已损坏，rollback 无效
       device_stats['error'] = str(e)
   ```

### 3.3 数据关系分析

```
arp_current 表结构:
┌─────────────────────┬──────────────────────────┐
│ ip_address          │ 有索引                    │
│ mac_address         │                          │
│ arp_device_id       │                          │
│ unique_key          │ uq_arp_current_ip_device │ ← (ip_address + arp_device_id)
└─────────────────────┴──────────────────────────┘

场景说明:
- 同一 IP (192.168.1.100) 可能出现在多台设备的 ARP 表中
- 但唯一约束要求 (ip_address + arp_device_id) 组合唯一
- 删除只删除当前设备的数据，其他设备的同 IP 数据不受影响
- 插入时如果该 IP 已被其他设备记录，且 arp_device_id 相同，则冲突
```

### 3.4 修复方案

**方案 A: 使用 UPSERT 策略** (推荐)

```python
# 使用 merge 或 INSERT ON DUPLICATE KEY UPDATE
async def _collect_device_async(self, device: Device) -> dict:
    # ... 采集逻辑 ...

    # 处理 ARP 表 - 使用 UPSERT
    if arp_table and not isinstance(arp_table, Exception):
        for entry in arp_table:
            # 先查询是否存在
            existing = self.db.query(ARPEntry).filter(
                ARPEntry.ip_address == entry['ip_address'],
                ARPEntry.arp_device_id == device.id
            ).first()

            if existing:
                # 更新现有记录
                existing.mac_address = entry['mac_address']
                existing.vlan_id = entry.get('vlan_id')
                existing.arp_interface = entry.get('interface')
                existing.last_seen = datetime.now()
            else:
                # 插入新记录
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

        self.db.commit()
```

**方案 B: 使用 SQLAlchemy merge**

```python
# 使用 Session.merge() 自动处理 INSERT/UPDATE
for entry in arp_table:
    arp_entry = ARPEntry(
        ip_address=entry['ip_address'],
        mac_address=entry['mac_address'],
        arp_device_id=device.id,
        # ... 其他字段 ...
    )
    # merge 会自动判断是 INSERT 还是 UPDATE
    self.db.merge(arp_entry)

self.db.commit()
```

**方案 C: 添加事务隔离和 Session 恢复**

```python
async def _collect_device_async(self, device: Device) -> dict:
    # 使用独立事务，失败不影响其他设备
    try:
        # ... 采集逻辑 ...

        # 使用 flush 检测冲突，而非直接 commit
        try:
            self.db.flush()  # 先 flush 检测错误
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # 重新尝试 UPSERT
            self._save_arp_with_upsert(arp_table, device)
            self.db.commit()

    except Exception as e:
        # 确保 Session 状态正确恢复
        if self.db.in_transaction():
            self.db.rollback()
        # 创建新的 Session 继续后续操作
        self.db = SessionLocal()
```

**方案 D: 移除或调整唯一约束** (不推荐)

如果业务允许同一 IP 出现在多台设备的 ARP 表中，可考虑移除唯一约束或改为 `(ip_address, mac_address)` 组合唯一。

***

## 四、修复优先级建议

| 问题           | 优先级 | 修复难度 | 预估影响                 |
| ------------ | --- | ---- | -------------------- |
| MAC 地址表解析失败  | P0  | 低    | 华为/H3C 设备 MAC 采集全面恢复 |
| Session 事务回滚 | P1  | 中    | ARP 数据采集稳定性提升        |

***

## 五、修复验证清单

### 5.1 MAC 地址表解析验证

- [ ] 单元测试：华为 MAC 地址表解析测试通过
- [ ] 集成测试：模拟设备返回 691+ 条 MAC 记录解析成功
- [ ] 真实设备测试：模块 33-R03-业务接入 MAC 采集成功

### 5.2 数据库唯一键冲突验证

- [ ] 单元测试：UPSERT 逻辑测试通过
- [ ] 并发测试：多设备同时采集 ARP 数据无冲突
- [ ] 异常恢复测试：Session 回滚后自动恢复

***

## 六、附录：代码文件位置

| 文件                                  | 行号      | 问题类型         |
| ----------------------------------- | ------- | ------------ |
| `app/services/netmiko_service.py`   | 764-771 | MAC 解析正则错误   |
| `app/services/netmiko_service.py`   | 714-715 | 异常吞没         |
| `app/services/arp_mac_scheduler.py` | 147-149 | ARP 删除逻辑     |
| `app/services/arp_mac_scheduler.py` | 151-161 | ARP 插入逻辑     |
| `app/services/arp_mac_scheduler.py` | 205-209 | Session 回滚处理 |
| `app/models/ip_location_current.py` | 38-40   | 缺少唯一约束定义     |

***

## 七、总结

本次分析发现了两个独立的运行时错误：

1. **MAC 地址表解析失败**: 正则表达式设计错误导致访问不存在的捕获组，需要修正正则表达式格式。
2. **数据库唯一键冲突**: 数据采集使用 delete + insert 策略，但唯一约束导致重复插入失败，Session 状态损坏。需要改为 UPSERT 策略。

两个问题均属于代码实现缺陷，修复后 ARP/MAC 采集功能应能正常运行。
