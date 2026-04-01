---
ontology:
  id: DOC-2026-04-002-PLAN
  type: plan
  problem: ARP Current 数据错误
  problem_id: P008
  status: active
  created: 2026-04-01
  updated: 2026-04-01
  author: Claude
  tags:
    - documentation
---
# ARP Current 表数据错误修复方案 V2（优化版）

**方案时间**: 2026-04-01
**方案人**: Claude Code
**文档版本**: 2.0
**基于**: V1 方案评审反馈优化

---

## 1. 问题回顾

### 1.1 根因总结

| 根因 | 位置 | 影响 | 优先级 |
|------|------|------|--------|
| vendor 参数大小写未处理 | netmiko_service.py:683 | H3C/Huawei 设备错误走入 Cisco 分支 | P0 |
| 缺少 IP/MAC 格式验证 | netmiko_service.py:684-700 | 无效数据直接写入数据库 | P1 |
| 缺少调试日志 | netmiko_service.py:684-700 | 问题排查困难 | P1 |
| MAC 标准化逻辑错误 | 原方案 normalize_mac | 输出格式不正确 | P0 |

### 1.2 错误现象

数据库 `arp_current` 表：
- `ip_address` 字段：存储 MAC 地址（如 `3cc7-86b4-72c4`）
- `mac_address` 字段：存储截断数据（如 `D0`、`BAGG1`）

### 1.3 V1 方案评审发现的问题

| 问题 | 原方案代码 | 正确方案 |
|------|-----------|---------|
| MAC 标准化错误 | `replace('.', ':')` 得到 `xxxx:xxxx:xxxx` | 先清除分隔符再重组为 `xx:xx:xx:xx:xx:xx` |
| MAC 验证正则不匹配 | 只匹配 `xxxx-xxxx-xxxx` | 匹配多种格式 |

---

## 2. 修改清单

### 2.1 文件修改汇总

| 序号 | 文件 | 方法/位置 | 修改内容 | 优先级 |
|------|------|----------|----------|--------|
| 1 | netmiko_service.py | `_parse_arp_table` 约 683 行 | vendor 小写转换 | P0 |
| 2 | netmiko_service.py | `_parse_arp_table` | `_normalize_mac_address` 方法 | P0 |
| 3 | netmiko_service.py | `_parse_arp_table` | IP/MAC 格式验证正则 | P1 |
| 4 | netmiko_service.py | `_parse_arp_table` | 调试日志 | P1 |
| 5 | arp_mac_scheduler.py | `_collect_device_async` 约 304 行 | 二次数据验证 | P1 |

---

## 3. 代码对比

### 3.1 vendor 小写转换

**原代码（错误）**:
```python
# netmiko_service.py 第 683 行
if vendor in ['huawei', 'h3c']:  # ❌ 未处理大小写
    ...
```

**修正代码**:
```python
vendor_lower = vendor.lower().strip()  # ✅ 转换为小写
logger.debug(f"[ARP 解析] vendor={vendor}, vendor_lower={vendor_lower}")

if vendor_lower in ['huawei', 'h3c']:  # ✅ 使用小写匹配
    ...
```

**参考**: `parse_mac_table` 方法（第 720 行）已正确实现此逻辑。

---

### 3.2 MAC 标准化方法（核心修正）

**原方案代码（错误）**:
```python
def normalize_mac(mac_raw: str) -> str:
    mac = mac_raw.upper()
    if '-' in mac:
        mac = mac.replace('-', ':')  # 结果: xx:xx-xx:xx-xx:xx ❌
    elif '.' in mac and len(mac) == 14:
        mac = mac.replace('.', ':')  # 结果: xxxx:xxxx:xxxx ❌
    return mac
```

**问题分析**:
- Huawei/H3C 格式 `609b-b431-d2c3` → 替换后 `60:9b-b4:31-d2:c3`（混合分隔符）
- Cisco 格式 `xxxx.xxxx.xxxx` → 替换后 `xxxx:xxxx:xxxx`（格式错误）

**修正代码（使用）**:
```python
import re
from loguru import logger

def _normalize_mac_address(self, mac: str) -> str:
    """
    标准化 MAC 地址为冒号分隔格式 (xx:xx:xx:xx:xx:xx)

    支持输入格式:
    - xxxx-xxxx-xxxx (Huawei/H3C)
    - xxxx.xxxx.xxxx (Cisco)
    - xx:xx:xx:xx:xx:xx (标准格式)

    Args:
        mac: 原始 MAC 地址字符串

    Returns:
        标准化后的 MAC 地址 (xx:xx:xx:xx:xx:xx)
    """
    mac_clean = re.sub(r'[^0-9A-Fa-f]', '', mac.upper())
    if len(mac_clean) != 12:
        logger.warning(f'[MAC 标准化] 无效 MAC: {mac}')
        return mac.upper()
    return ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
```

**验证测试**:
```python
# 输入                    输出
_normalize_mac_address("609b-b431-d2c3")    → "60:9B:B4:31:D2:C3"
_normalize_mac_address("2401.c7d9.2241")    → "24:01:C7:D9:22:41"
_normalize_mac_address("3C:C7:86:B4:72:C4") → "3C:C7:86:B4:72:C4"
_normalize_mac_address("invalid")           → "INVALID" (警告日志)
```

---

### 3.3 MAC 验证正则

**原方案代码（不完整）**:
```python
MAC_PATTERN = re.compile(r'^[0-9A-Fa-f]{4}([-:.])[0-9A-Fa-f]{4}\1[0-9A-Fa-f]{4}$')
# 只匹配 xxxx-xxxx-xxxx 格式
```

**修正代码（使用）**:
```python
MAC_PATTERN = re.compile(r'^[0-9A-Fa-f]{2}([-:.]?[0-9A-Fa-f]{2}){5}$')
```

**匹配测试**:
| 格式 | 示例 | 匹配结果 |
|------|------|---------|
| 横线分隔 | `609b-b431-d2c3` | ✅ |
| 点分隔 | `2401.c7d9.2241` | ✅ |
| 冒号分隔 | `3C:C7:86:B4:72:C4` | ✅ |
| 无分隔符 | `3CC786B472C4` | ✅ |
| 无效格式 | `invalid-mac` | ❌ |

---

### 3.4 IP 验证正则

```python
IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
```

**注意**: 此正则仅检查格式，不检查数值范围（如 0-255）。如需严格验证：
```python
def _validate_ip_address(self, ip: str) -> bool:
    """严格 IP 验证（数值范围 0-255）"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False
```

---

### 3.5 `_parse_arp_table` 方法完整修正代码

```python
def _parse_arp_table(self, output: str, vendor: str) -> List[Dict[str, Any]]:
    """
    解析 ARP 表输出（优化版）

    修复问题:
    1. vendor 大小写处理
    2. MAC 地址标准化
    3. IP/MAC 格式验证
    4. 调试日志
    """
    from loguru import logger

    arp_entries = []
    lines = output.strip().split('\n')

    # 1. vendor 小写转换
    vendor_lower = vendor.lower().strip()
    logger.debug(f"[ARP 解析] vendor={vendor}, vendor_lower={vendor_lower}")

    # 2. 表头识别
    start_index = 0
    for i, line in enumerate(lines):
        if 'IP' in line.upper() and 'MAC' in line.upper():
            start_index = i + 1
            logger.debug(f"[ARP 解析] 表头识别在第 {i} 行: {line.strip()}")
            break

    # 3. 验证正则
    IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    MAC_PATTERN = re.compile(r'^[0-9A-Fa-f]{2}([-:.]?[0-9A-Fa-f]{2}){5}$')

    # 4. 数据行解析
    for line in lines[start_index:]:
        if not line.strip():
            continue
        if '---' in line or 'Total:' in line or 'Type:' in line:
            continue

        parts = line.split()
        if len(parts) < 4:
            logger.warning(f"[ARP 解析] 行字段不足: {line.strip()}")
            continue

        try:
            if vendor_lower in ['huawei', 'h3c']:
                # Huawei/H3C 格式: IP MAC VLAN Interface [Aging] [Type]
                ip = parts[0]
                mac_raw = parts[1]
                vlan = parts[2] if parts[2].isdigit() else None
                interface = parts[3]

                # 数据验证
                if not IP_PATTERN.match(ip):
                    logger.warning(f"[ARP 解析] 无效 IP: {ip}, 跳过")
                    continue
                if not MAC_PATTERN.match(mac_raw):
                    logger.warning(f"[ARP 解析] 无效 MAC: {mac_raw}, 跳过")
                    continue

                entry = {
                    'ip_address': ip,
                    'mac_address': self._normalize_mac_address(mac_raw),
                    'vlan_id': int(vlan) if vlan else None,
                    'interface': interface
                }
            else:  # cisco
                # Cisco 格式: Protocol IP Age MAC Type Interface
                ip = parts[1]
                mac_raw = parts[3]

                # 数据验证
                if not IP_PATTERN.match(ip):
                    logger.warning(f"[ARP 解析] 无效 IP: {ip}, 跳过")
                    continue
                if not MAC_PATTERN.match(mac_raw):
                    logger.warning(f"[ARP 解析] 无效 MAC: {mac_raw}, 跳过")
                    continue

                entry = {
                    'ip_address': ip,
                    'mac_address': self._normalize_mac_address(mac_raw),
                    'vlan_id': None,
                    'interface': parts[5] if len(parts) > 5 else parts[4]
                }

            arp_entries.append(entry)
            logger.debug(f"[ARP 解析] 成功解析: IP={entry['ip_address']}, MAC={entry['mac_address']}")

        except (ValueError, IndexError) as e:
            logger.warning(f"[ARP 解析] 解析失败: {line.strip()}, error={e}")
            continue

    logger.info(f"[ARP 解析] vendor={vendor_lower}, 共解析 {len(arp_entries)} 条有效记录")
    return arp_entries
```

---

### 3.6 `arp_mac_scheduler.py` 二次数据验证

```python
# arp_mac_scheduler.py _collect_device_async 方法中
# 在写入数据库前添加二次验证

import re

# 验证正则（标准化后的格式）
IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
MAC_PATTERN = re.compile(r'^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$')

def validate_arp_entry(entry: dict) -> bool:
    """
    二次验证 ARP 条目数据完整性

    Args:
        entry: ARP 条目字典

    Returns:
        True: 数据有效，False: 数据无效
    """
    required_fields = ['ip_address', 'mac_address']
    for field in required_fields:
        if not entry.get(field):
            logger.warning(f"[ARP 验证] 缺少必要字段: {field}")
            return False

    # IP 格式检查
    if not IP_PATTERN.match(entry['ip_address']):
        logger.warning(f"[ARP 验证] 无效 IP 格式: {entry['ip_address']}")
        return False

    # MAC 格式检查（冒号分隔，已标准化）
    if not MAC_PATTERN.match(entry['mac_address']):
        logger.warning(f"[ARP 验证] 无效 MAC 格式: {entry['mac_address']}")
        return False

    return True

# 使用示例（在写入数据库前）
valid_entries = [e for e in arp_table if validate_arp_entry(e)]
invalid_count = len(arp_table) - len(valid_entries)
if invalid_count > 0:
    logger.warning(f"[ARP 采集] 设备 {device.hostname} 过滤无效条目: {invalid_count} 条")
logger.info(f"[ARP 采集] 设备 {device.hostname} 有效条目: {len(valid_entries)}/{len(arp_table)}")
```

---

## 4. 单元测试

### 4.1 测试用例清单

| 序号 | 测试场景 | 输入 | 期望输出 | 优先级 |
|------|----------|------|----------|--------|
| 1 | H3C vendor 大小写 | vendor="H3C" | 正确解析 IP/MAC | P0 |
| 2 | Huawei vendor 大小写 | vendor="Huawei" | 正确解析 IP/MAC | P0 |
| 3 | MAC 横线格式标准化 | "609b-b431-d2c3" | "60:9B:B4:31:D2:C3" | P0 |
| 4 | MAC 点格式标准化 | "2401.c7d9.2241" | "24:01:C7:D9:22:41" | P0 |
| 5 | MAC 冒号格式标准化 | "3C:C7:86:B4:72:C4" | "3C:C7:86:B4:72:C4" | P0 |
| 6 | 无效 MAC 处理 | "invalid-mac" | 警告日志 + 返回原值 | P1 |
| 7 | 无效 IP 过滤 | "not-an-ip" | 条目被跳过 | P1 |
| 8 | 无效 MAC 过滤 | "xxx-xxx-xxx" | 条目被跳过 | P1 |
| 9 | 二次验证通过 | 有效条目 | True | P1 |
| 10 | 二次验证失败 | 缺少字段 | False | P1 |

### 4.2 测试代码示例

```python
# tests/test_arp_parser.py
import pytest
from app.services.netmiko_service import NetmikoService

class TestMACNormalization:
    """MAC 地址标准化测试"""

    @pytest.fixture
    def service(self):
        return NetmikoService()

    def test_huawei_mac_format(self, service):
        """测试华为横线格式标准化"""
        result = service._normalize_mac_address("609b-b431-d2c3")
        assert result == "60:9B:B4:31:D2:C3"

    def test_cisco_mac_format(self, service):
        """测试思科点格式标准化"""
        result = service._normalize_mac_address("2401.c7d9.2241")
        assert result == "24:01:C7:D9:22:41"

    def test_standard_mac_format(self, service):
        """测试标准冒号格式"""
        result = service._normalize_mac_address("3C:C7:86:B4:72:C4")
        assert result == "3C:C7:86:B4:72:C4"

    def test_invalid_mac(self, service):
        """测试无效 MAC 处理"""
        result = service._normalize_mac_address("invalid")
        assert result == "INVALID"  # 返回原值大写

class TestVendorCaseInsensitive:
    """vendor 大小写测试"""

    def test_h3c_uppercase(self):
        """测试 H3C 大写 vendor"""
        vendor = "H3C"
        vendor_lower = vendor.lower().strip()
        assert vendor_lower == "h3c"
        assert vendor_lower in ['huawei', 'h3c']

    def test_huawei_mixedcase(self):
        """测试 Huawei 混合大小写"""
        vendor = "Huawei"
        vendor_lower = vendor.lower().strip()
        assert vendor_lower == "huawei"
        assert vendor_lower in ['huawei', 'h3c']

class TestARPValidation:
    """ARP 条目验证测试"""

    def test_valid_entry(self):
        """测试有效条目"""
        entry = {
            'ip_address': '10.23.2.1',
            'mac_address': '60:9B:B4:31:D2:C3'
        }
        assert validate_arp_entry(entry) == True

    def test_invalid_ip_entry(self):
        """测试无效 IP 条目"""
        entry = {
            'ip_address': 'invalid-ip',
            'mac_address': '60:9B:B4:31:D2:C3'
        }
        assert validate_arp_entry(entry) == False

    def test_missing_field_entry(self):
        """测试缺少字段条目"""
        entry = {'ip_address': '10.23.2.1'}
        assert validate_arp_entry(entry) == False
```

---

## 5. 实施步骤

### 5.1 实施计划

```
阶段 1: 代码修改 (预计 1.5 小时)
├── 1.1 修改 netmiko_service.py
│   ├── 添加 _normalize_mac_address 方法
│   ├── 修改 _parse_arp_table 方法
│   │   ├── vendor 小写转换
│   │   ├── IP/MAC 格式验证正则
│   │   ├── 数据验证逻辑
│   │   └── 调试日志
│   └── 本地语法检查
│
├── 1.2 修改 arp_mac_scheduler.py
│   ├── 添加 validate_arp_entry 函数
│   ├── 在写入前添加二次验证
│   └── 本地语法检查
│
└── 1.3 本地代码审查

阶段 2: 测试验证 (预计 1 小时)
├── 2.1 单元测试
│   ├── MAC 标准化测试
│   ├── vendor 大小写测试
│   └── 数据验证测试
│
├── 2.2 设备采集测试
│   ├── H3C 设备采集 (10.23.2.50)
│   ├── Huawei 设备采集 (10.23.2.56)
│   └── Cisco 设备采集 (10.23.2.13)
│
└── 2.3 数据库验证
    ├── ip_address 字段为 IP 格式
    ├── mac_address 字段为冒号分隔 MAC
    └── 无无效数据记录
```

### 5.2 验证 SQL

```sql
-- 验证 H3C 设备数据正确性
SELECT
    d.hostname,
    a.ip_address,
    a.mac_address,
    a.vlan_id,
    a.arp_interface
FROM arp_current a
JOIN devices d ON a.arp_device_id = d.id
WHERE d.vendor = 'H3C' OR d.vendor = 'h3c'
ORDER BY a.last_seen DESC
LIMIT 10;

-- 验证字段格式
SELECT
    ip_address,
    mac_address,
    CASE
        WHEN ip_address REGEXP '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$'
        THEN 'IP格式正确'
        ELSE 'IP格式错误'
    END AS ip_check,
    CASE
        WHEN mac_address REGEXP '^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$'
        THEN 'MAC格式正确'
        ELSE 'MAC格式错误'
    END AS mac_check
FROM arp_current
ORDER BY last_seen DESC
LIMIT 20;
```

---

## 6. 回滚方案

### 6.1 回滚条件

| 条件 | 说明 |
|------|------|
| 采集数据仍有错误 | IP/MAC 字段仍错位 |
| 正常数据被过滤 | 验证逻辑过于严格 |
| 服务启动异常 | 语法错误或导入失败 |

### 6.2 回滚步骤

```bash
# 1. 回滚代码
git checkout app/services/netmiko_service.py
git checkout app/services/arp_mac_scheduler.py

# 2. 重启服务
systemctl restart switch_manage  # 或使用项目启动命令

# 3. 验证回滚
# 检查服务日志确认无错误
# 手动触发一次采集确认功能正常
```

### 6.3 备份文件（已有）

| 文件 | 备份位置 |
|------|---------|
| netmiko_service.py | `app/services/netmiko_service.py.backup.20260330_final_fix` |
| arp_mac_scheduler.py | `app/services/arp_mac_scheduler.py.backup.20260330_181317` |

---

## 7. 实施检查清单

```
□ 代码修改完成
□ 本地语法检查通过
□ 单元测试通过
□ H3C 设备采集测试通过
□ Huawei 设备采集测试通过
□ Cisco 设备采集测试通过
□ 数据库字段验证通过
□ 调试日志输出正常
□ Git 提交完成
```

---

## 附录

### A. 参考文档

| 文档 | 路径 |
|------|------|
| 根因分析报告 | docs/superpowers/analysis/2026-04-01-arp-current-data-error-root-cause.md |
| V1 修复方案 | docs/superpowers/plans/2026-04-01-arp-current-fix-plan.md |
| V1 方案评审 | docs/superpowers/reviews/2026-04-01-arp-current-fix-plan-review.md |
| 厂商格式分析 | docs/superpowers/analysis/各厂商 ARP-MAC 地址数据格式分析.md |

### B. 各厂商 ARP 表格式对比

| 特性 | Huawei | Cisco | H3C |
|------|--------|-------|-----|
| 命令 | `display arp` | `show ip arp` | `display arp` |
| MAC 分隔符 | 横线 `-` | 点 `.` | 横线 `-` |
| IP 列位置 | 第 1 列 (parts[0]) | 第 2 列 (parts[1]) | 第 1 列 (parts[0]) |
| MAC 列位置 | 第 2 列 (parts[1]) | 第 4 列 (parts[3]) | 第 2 列 (parts[1]) |
| 列数 | 6+ 列 | 6 列 | 6 列 |

---

**文档结束**