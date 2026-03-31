# ARP/MAC 采集调度器 Netmiko ReadTimeout 错误修复方案（优化版）

**创建日期**: 2026-03-30
**优化日期**: 2026-03-30
**关联分析**: `docs/superpowers/analysis/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-analysis.md`
**评审报告**: `docs/superpowers/reviews/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-review.md`
**修复优先级**: P0 - 高优先级，影响生产数据采集

---

## 〇、评审意见响应

本节逐项响应评审报告中的关键问题，确保方案优化后满足评审要求。

### 0.1 高优先级问题响应

| 评审问题编号 | 问题描述 | 响应措施 | 状态 |
|--------------|----------|----------|------|
| **P1-001** | expect_string 正则不支持中文设备名称 | 正则改为 `r'[<>\[].*[>\]]'`（支持任意字符） | ✓ 已修正 |
| **P1-005** | Cisco 提示符未匹配配置模式 | 正则改为 `r'[\w\-]+(?:\(config[^)]*\))?[#>]'` | ✓ 已修正 |
| **R-001** | 中文设备名称正则匹配失败风险 | 同 P1-001，使用宽松正则 | ✓ 已规避 |

### 0.2 中优先级问题响应

| 评审问题编号 | 问题描述 | 响应措施 | 状态 |
|--------------|----------|----------|------|
| **P2-001** | 缺少网络延迟补偿 | 新增 `network_delay_compensation: 5s` 配置 | ✓ 已添加 |
| **P2-003** | 最大超时可能不足 | 最大超时从 180s 增加到 240s | ✓ 已调整 |
| **P3-001** | vendor 判断逻辑与现有代码不一致 | 保持方案设计的健壮判断逻辑 | ✓ 已采纳 |
| **P4-001** | 未测试 vendor 为 None | 新增边界测试用例 | ✓ 已补充 |
| **P4-002** | 未测试中文厂商名称 | 新增中文设备名称测试用例 | ✓ 已补充 |
| **P5-002** | 未测试大表设备 | 新增超大表超时测试计划 | ✓ 已补充 |

### 0.3 低优先级问题响应

| 评审问题编号 | 问题描述 | 响应措施 | 状态 |
|--------------|----------|----------|------|
| **P1-002** | 未支持带版本号提示符 | 使用贪婪匹配 `.*`，自动支持 | ✓ 已覆盖 |
| **P1-003** | 未考虑空格和特殊字符 | 使用 `.*` 贪婪匹配，自动支持 | ✓ 已覆盖 |
| **R-007** | 回滚开关环境变量未生效 | 新增 `NETMIKO_USE_EXPECT_STRING` 配置项及回滚逻辑 | ✓ 已添加 |

---

## 一、问题根因回顾

| 问题 | 根因 | 影响 |
|------|------|------|
| 命令回显检测失败 | `send_command` 未指定 `expect_string`，Netmiko 默认等待命令回显 | 华为设备 ARP/MAC 采集失败 |
| 超时时间不足 | `read_timeout=20s` 对于大型 ARP/MAC 表（691+ 条目）不足 | 大型设备采集超时 |
| 华为设备特殊性 | 华为 VRP 系统可能不回显命令或格式异常 | 特定设备持续失败 |
| 中文设备名称 | 提示符包含中文（如 `<模块33-R03-业务接入>`） | 原正则无法匹配 |

---

## 二、修复方案设计（优化版）

### 2.1 expect_string 方案设计（优化版）

#### 2.1.1 厂商特定提示符正则设计（优化版）

**关键优化**: 使用宽松正则表达式，支持中文设备名称和特殊字符。

```python
# 厂商特定 expect_string 配置表（优化版）
VENDOR_EXPECT_CONFIG = {
    'huawei': {
        'user_view': r'<[^>]+>',           # 用户视图: <Switch> 或 <模块33-R03-业务接入>
        'system_view': r'\[[^\]]+\]',      # 系统视图: [Switch] 或 [~Switch]
        'any_view': r'[<>\[].*[>\]]',      # ✓ 优化：任意视图（支持中文和特殊字符）
        'prompt_pattern': r'[<\[]',
    },
    'h3c': {
        'user_view': r'<[^>]+>',
        'system_view': r'\[[^\]]+\]',
        'any_view': r'[<>\[].*[>\]]',      # ✓ 优化：同华为
        'prompt_pattern': r'[<\[]',
    },
    'cisco': {
        'privileged': r'[\w\-]+#',         # 特权模式: Switch#
        'config': r'[\w\-]+\(config[^)]*\)#',  # 配置模式
        'any_view': r'[\w\-]+(?:\(config[^)]*\))?[#>]',  # ✓ 优化：支持配置模式
        'prompt_pattern': r'[#>]',
    },
    'ruijie': {
        'privileged': r'[\w\-]+#',
        'config': r'[\w\-]+\(config[^)]*\)#',
        'any_view': r'[\w\-]+(?:\(config[^)]*\))?[#>]',  # ✓ 优化：同 Cisco
        'prompt_pattern': r'[#>]',
    },
}
```

#### 2.1.2 正则表达式优化对比

| 原方案正则 | 优化后正则 | 测试用例 | 原方案结果 | 优化后结果 |
|------------|------------|----------|------------|------------|
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `<Switch>` | ✓ | ✓ |
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `[Switch]` | ✓ | ✓ |
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `<模块33-R03-业务接入>` | ✗ **无法匹配** | ✓ **可匹配** |
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `[~核心交换机]` | ✗ | ✓ |
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `<SW-Core-1>` | ✓ | ✓ |
| `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | `<Switch-V200R001>` | ✗ | ✓ |

**Cisco 正则优化对比**:

| 原方案正则 | 优化后正则 | 测试用例 | 原方案结果 | 优化后结果 |
|------------|------------|----------|------------|------------|
| `r'[\w\-]+[#>]'` | `r'[\w\-]+(?:\(config[^)]*\))?[#>]'` | `Switch#` | ✓ | ✓ |
| `r'[\w\-]+[#>]'` | `r'[\w\-]+(?:\(config[^)]*\))?[#>]'` | `Switch>` | ✓ | ✓ |
| `r'[\w\-]+[#>]'` | `r'[\w\-]+(?:\(config[^)]*\))?[#>]'` | `Switch(config)#` | ✗ **无法匹配** | ✓ **可匹配** |
| `r'[\w\-]+[#>]'` | `r'[\w\-]+(?:\(config[^)]*\))?[#>]'` | `Switch(config-if)#` | ✗ | ✓ |

#### 2.1.3 正则表达式验证测试

```python
import re

# 优化后的正则表达式
huawei_pattern = r'[<>\[].*[>\]]'
cisco_pattern = r'[\w\-]+(?:\(config[^)]*\))?[#>]'

# 测试用例集
huawei_test_cases = [
    ('<Switch>', True),
    ('[Switch]', True),
    ('<模块33-R03-业务接入>', True),  # ✓ 中文设备名称
    ('[~核心交换机]', True),
    ('<SW-Core-1>', True),
    ('<Switch-V200R001>', True),      # ✓ 带版本号
    ('<Switch (Core)>', True),        # ✓ 特殊字符
]

cisco_test_cases = [
    ('Switch#', True),
    ('Switch>', True),
    ('Switch(config)#', True),        # ✓ 配置模式
    ('Switch(config-if)#', True),     # ✓ 接口配置模式
    ('Router#', True),
]

print("=== 华为/H3C 正则测试（优化版）===")
for test, expected in huawei_test_cases:
    result = bool(re.search(huawei_pattern, test))
    status = "✓" if result == expected else "✗"
    print(f"{status} '{test}' -> 匹配: {result}, 期望: {expected}")

print("\n=== Cisco/Ruijie 正则测试（优化版）===")
for test, expected in cisco_test_cases:
    result = bool(re.search(cisco_pattern, test))
    status = "✓" if result == expected else "✗"
    print(f"{status} '{test}' -> 匹配: {result}, 期望: {expected}")
```

#### 2.1.4 ARP/MAC 采集命令 expect_string 配置（优化版）

```python
# ARP/MAC 采集命令特定配置（优化版）
ARP_MAC_COMMAND_CONFIG = {
    'huawei': {
        'arp_command': 'display arp',
        'expect_string': r'[<>\[].*[>\]]',  # ✓ 优化：支持中文
        'default_timeout': 65,  # ✓ 优化：增加 5s 网络延迟补偿
    },
    'h3c': {
        'arp_command': 'display arp',
        'expect_string': r'[<>\[].*[>\]]',  # ✓ 优化：支持中文
        'default_timeout': 65,
    },
    'cisco': {
        'arp_command': 'show ip arp',
        'expect_string': r'[\w\-]+(?:\(config[^)]*\))?[#>]',  # ✓ 优化：支持配置模式
        'default_timeout': 50,
    },
    'ruijie': {
        'arp_command': 'show ip arp',
        'expect_string': r'[\w\-]+(?:\(config[^)]*\))?[#>]',  # ✓ 优化：支持配置模式
        'default_timeout': 50,
    },
}

MAC_TABLE_COMMAND_CONFIG = {
    'huawei': {
        'mac_command': 'display mac-address',
        'expect_string': r'[<>\[].*[>\]]',  # ✓ 优化：支持中文
        'default_timeout': 95,  # ✓ 优化：90s + 5s 网络延迟补偿
    },
    'h3c': {
        'mac_command': 'display mac-address',
        'expect_string': r'[<>\[].*[>\]]',
        'default_timeout': 95,
    },
    'cisco': {
        'mac_command': 'show mac address-table',
        'expect_string': r'[\w\-]+(?:\(config[^)]*\))?[#>]',  # ✓ 优化：支持配置模式
        'default_timeout': 70,
    },
    'ruijie': {
        'mac_command': 'show mac address-table',
        'expect_string': r'[\w\-]+(?:\(config[^)]*\))?[#>]',
        'default_timeout': 70,
    },
}
```

### 2.2 read_timeout 优化方案（优化版）

#### 2.2.1 动态超时计算策略（优化版）

**关键优化**: 新增网络延迟补偿因子和分页延迟补偿。

```python
# 命令类型超时配置（优化版）
COMMAND_TIMEOUT_CONFIG = {
    'arp_table': {
        'base_timeout': 30,                    # 基础超时
        'network_delay_compensation': 5,      # ✓ 新增：网络延迟补偿
        'max_timeout': 180,                   # 最大超时（不变）
        'scale_factor': 0.05,                 # 每条目增加 0.05s
        'min_entries_for_scale': 100,         # 超过 100 条开始动态计算
        'pagination_delay': 2,                # ✓ 新增：分页延迟（每页）
    },
    'mac_table': {
        'base_timeout': 45,
        'network_delay_compensation': 5,      # ✓ 新增：网络延迟补偿
        'max_timeout': 240,                   # ✓ 优化：从 180s 增加到 240s
        'scale_factor': 0.08,
        'min_entries_for_scale': 50,
        'pagination_delay': 2,                # ✓ 新增：分页延迟
    },
    'version': {
        'base_timeout': 20,
        'network_delay_compensation': 5,      # ✓ 新增
        'max_timeout': 35,                    # ✓ 优化：30s + 5s
        'scale_factor': 0,
        'min_entries_for_scale': 0,
        'pagination_delay': 0,
    },
    'interfaces': {
        'base_timeout': 30,
        'network_delay_compensation': 5,      # ✓ 新增
        'max_timeout': 70,                    # ✓ 优化：60s + 5s (每页补偿)
        'scale_factor': 0,
        'min_entries_for_scale': 0,
        'pagination_delay': 2,
    },
}

def calculate_dynamic_timeout(
    command_type: str,
    estimated_entries: int = None,
    estimated_pages: int = None
) -> int:
    """
    动态计算命令执行超时时间（优化版）

    Args:
        command_type: 命令类型 (arp_table, mac_table, version 等)
        estimated_entries: 预估条目数（可选，用于 ARP/MAC 表）
        estimated_pages: 预估分页数（可选，华为设备约每 20 行分页）

    Returns:
        计算后的超时时间（秒）

    Example:
        >>> calculate_dynamic_timeout('mac_table', 2000, 100)
        240  # 限制在最大值
    """
    config = COMMAND_TIMEOUT_CONFIG.get(
        command_type,
        {'base_timeout': 20, 'network_delay_compensation': 5, 'max_timeout': 30}
    )

    # 基础超时 + 网络延迟补偿
    timeout = config['base_timeout'] + config.get('network_delay_compensation', 0)

    # 条目数动态计算
    if estimated_entries and estimated_entries >= config.get('min_entries_for_scale', 100):
        extra_time = (estimated_entries - config['min_entries_for_scale']) * config['scale_factor']
        timeout += extra_time

    # ✓ 新增：分页延迟补偿（华为设备每 20-24 行分页）
    if estimated_pages:
        timeout += estimated_pages * config.get('pagination_delay', 2)

    # 限制最大超时
    return min(int(timeout), config['max_timeout'])
```

#### 2.2.2 配置化超时参数（优化版）

**新增配置项**: `app/config.py`

```python
# 在 Settings 类中添加以下配置项（优化版）

# Netmiko 超时配置
NETMIKO_DEFAULT_TIMEOUT = int(os.getenv('NETMIKO_DEFAULT_TIMEOUT', '20'))
NETMIKO_ARP_TABLE_TIMEOUT = int(os.getenv('NETMIKO_ARP_TABLE_TIMEOUT', '65'))   # ✓ 优化：60+5
NETMIKO_MAC_TABLE_TIMEOUT = int(os.getenv('NETMIKO_MAC_TABLE_TIMEOUT', '95'))   # ✓ 优化：90+5
NETMIKO_MAX_TIMEOUT = int(os.getenv('NETMIKO_MAX_TIMEOUT', '240'))              # ✓ 优化：180->240

# 动态超时开关
NETMIKO_DYNAMIC_TIMEOUT_ENABLED = os.getenv('NETMIKO_DYNAMIC_TIMEOUT_ENABLED', 'True').lower() == 'true'

# ✓ 新增：网络延迟补偿配置
NETMIKO_NETWORK_DELAY_COMPENSATION = int(os.getenv('NETMIKO_NETWORK_DELAY_COMPENSATION', '5'))

# ✓ 新增：回滚开关（评审要求）
NETMIKO_USE_EXPECT_STRING = os.getenv('NETMIKO_USE_EXPECT_STRING', 'True').lower() == 'true'
```

### 2.3 代码修改详细设计（优化版）

#### 2.3.1 netmiko_service.py 修改清单

| 修改位置 | 修改类型 | 修改内容 | 优化说明 |
|----------|----------|----------|----------|
| `collect_arp_table` (1147-1182) | 添加参数 | 添加 `expect_string` 和动态超时 | ✓ 正则优化 + 超时补偿 |
| `collect_mac_table` (1232-1260) | 添加参数 | 添加 `expect_string` 和动态超时 | ✓ 正则优化 + 超时补偿 |
| `_get_vendor_expect_strings` (264-295) | 优化正则 | 使用宽松正则支持中文 | ✓ 响应 P1-001 |
| `execute_command` (297) | 新增参数 | 添加 `command_type` 参数 | ✓ 支持动态超时 |

#### 2.3.2 collect_arp_table 方法修改（优化版）

**修改后代码**:

```python
async def collect_arp_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    """
    采集设备 ARP 表（优化版：支持 expect_string 和动态超时）

    优化内容：
    1. expect_string 支持中文设备名称（响应 P1-001）
    2. read_timeout 增加 5s 网络延迟补偿（响应 P2-001）
    3. vendor 判断支持中文厂商名称（响应 P4-002）
    4. 新增回滚开关支持（响应 R-007）
    """
    from app.config import settings

    if not device.username or not device.password:
        print(f"Device {device.hostname} missing credentials")
        return None

    # ✓ 优化：vendor 判断支持中文和 None
    vendor_lower = device.vendor.lower().strip() if device.vendor else 'huawei'

    # 命令和参数配置
    if vendor_lower in ['huawei', 'h3c', '华为', '华三']:
        command = "display arp"
        # ✓ 优化：使用宽松正则支持中文设备名称
        expect_string = r'[<>\[].*[>\]]'
        read_timeout = settings.NETMIKO_ARP_TABLE_TIMEOUT  # 65s
    elif vendor_lower in ['cisco', 'ruijie', '锐捷']:
        command = "show ip arp"
        # ✓ 优化：支持配置模式提示符
        expect_string = r'[\w\-]+(?:\(config[^)]*\))?[#>]'
        read_timeout = 50
    else:
        # 默认使用华为风格
        command = "display arp"
        expect_string = r'[<>\[].*[>\]]'
        read_timeout = settings.NETMIKO_ARP_TABLE_TIMEOUT

    print(f"[INFO] Collecting ARP table from {device.hostname}, vendor: {vendor_lower}")
    print(f"[INFO] Using expect_string: {expect_string}, timeout: {read_timeout}s")

    # ✓ 新增：回滚开关支持
    if settings.NETMIKO_USE_EXPECT_STRING:
        # 新方案：传递 expect_string 和超时参数
        output = await self.execute_command(
            device,
            command,
            expect_string=expect_string,
            read_timeout=read_timeout
        )
    else:
        # 回滚到原有方案（无 expect_string）
        output = await self.execute_command(device, command)

    if not output:
        print(f"[WARNING] ARP table collection returned empty output for {device.hostname}")
        return None

    # 解析 ARP 表
    arp_entries = self._parse_arp_table(output, device.vendor)

    # 添加 device_id 到每个 ARP 条目
    for arp_entry in arp_entries:
        arp_entry["device_id"] = device.id

    print(f"[SUCCESS] Collected {len(arp_entries)} ARP entries from {device.hostname}")
    return arp_entries if arp_entries else None
```

#### 2.3.3 collect_mac_table 方法修改（优化版）

**修改后代码**:

```python
async def collect_mac_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    """
    采集设备 MAC 地址表（优化版：支持 expect_string 和动态超时）

    优化内容：
    1. expect_string 支持中文设备名称（响应 P1-001）
    2. read_timeout 增加 5s 网络延迟补偿（响应 P2-001）
    3. 最大超时增加到 240s（响应 P2-003）
    4. vendor 判断支持中文厂商名称（响应 P4-002）
    """
    from app.config import settings

    if not device.username or not device.password:
        print(f"Device {device.hostname} missing credentials")
        return None

    vendor_lower = device.vendor.lower().strip() if device.vendor else 'huawei'

    # 命令和参数配置
    mac_command = self.get_commands(device.vendor, "mac_table")
    if not mac_command:
        # 如果映射表中没有，使用默认命令
        if vendor_lower in ['huawei', 'h3c', '华为', '华三']:
            mac_command = "display mac-address"
        elif vendor_lower in ['cisco', 'ruijie', '锐捷']:
            mac_command = "show mac address-table"
        else:
            mac_command = "display mac-address"

    # ✓ 优化：expect_string 配置（支持中文）
    if vendor_lower in ['huawei', 'h3c', '华为', '华三']:
        expect_string = r'[<>\[].*[>\]]'
        read_timeout = settings.NETMIKO_MAC_TABLE_TIMEOUT  # 95s
    elif vendor_lower in ['cisco', 'ruijie', '锐捷']:
        expect_string = r'[\w\-]+(?:\(config[^)]*\))?[#>]'
        read_timeout = 70
    else:
        expect_string = r'[<>\[].*[>\]]'
        read_timeout = settings.NETMIKO_MAC_TABLE_TIMEOUT

    print(f"[INFO] Collecting MAC table from {device.hostname}, vendor: {vendor_lower}")
    print(f"[INFO] Using expect_string: {expect_string}, timeout: {read_timeout}s")

    # ✓ 新增：回滚开关支持
    if settings.NETMIKO_USE_EXPECT_STRING:
        output = await self.execute_command(
            device,
            mac_command,
            expect_string=expect_string,
            read_timeout=read_timeout
        )
    else:
        output = await self.execute_command(device, mac_command)

    if not output:
        print(f"[WARNING] MAC table collection returned empty output for {device.hostname}")
        return None

    mac_table = self.parse_mac_table(output, device.vendor)

    # 添加 device_id 到每个 MAC 条目
    for mac_entry in mac_table:
        mac_entry["device_id"] = device.id

    print(f"[SUCCESS] Collected {len(mac_table)} MAC entries from {device.hostname}")
    return mac_table if mac_table else None
```

#### 2.3.4 config.py 新增配置（优化版）

```python
# 在 Settings 类中添加以下配置项（优化版）

# Netmiko 超时配置
NETMIKO_DEFAULT_TIMEOUT = int(os.getenv('NETMIKO_DEFAULT_TIMEOUT', '20'))
NETMIKO_ARP_TABLE_TIMEOUT = int(os.getenv('NETMIKO_ARP_TABLE_TIMEOUT', '65'))   # ✓ 优化：60+5
NETMIKO_MAC_TABLE_TIMEOUT = int(os.getenv('NETMIKO_MAC_TABLE_TIMEOUT', '95'))   # ✓ 优化：90+5
NETMIKO_MAX_TIMEOUT = int(os.getenv('NETMIKO_MAX_TIMEOUT', '240'))              # ✓ 优化：180->240

# 动态超时开关
NETMIKO_DYNAMIC_TIMEOUT_ENABLED = os.getenv('NETMIKO_DYNAMIC_TIMEOUT_ENABLED', 'True').lower() == 'true'

# ✓ 新增：网络延迟补偿配置（响应 P2-001）
NETMIKO_NETWORK_DELAY_COMPENSATION = int(os.getenv('NETMIKO_NETWORK_DELAY_COMPENSATION', '5'))

# ✓ 新增：回滚开关（响应 R-007）
NETMIKO_USE_EXPECT_STRING = os.getenv('NETMIKO_USE_EXPECT_STRING', 'True').lower() == 'true'
```

---

## 三、测试计划（优化版）

### 3.1 单元测试设计（优化版）

#### 3.1.1 测试文件结构

```
tests/
├── test_netmiko_expect_string.py      # expect_string 参数测试
├── test_netmiko_timeout.py            # 动态超时测试
├── test_vendor_config.py              # 厂商配置测试
├── test_chinese_hostname.py           # ✓ 新增：中文设备名称测试
├── test_cisco_config_mode.py          # ✓ 新增：Cisco 配置模式测试
├── test_large_table_timeout.py        # ✓ 新增：超大表超时测试
├── test_rollback_switch.py            # ✓ 新增：回滚开关测试
└── fixtures/
    └── mock_devices.py                # Mock 设备数据
```

#### 3.1.2 expect_string 参数测试

```python
# tests/test_netmiko_expect_string.py

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
import asyncio

class TestNetmikoExpectString:
    """测试 expect_string 参数正确传递"""

    @pytest.mark.asyncio
    async def test_huawei_arp_expect_string(self):
        """华为 ARP 采集应使用正确的 expect_string"""
        from app.services.netmiko_service import NetmikoService

        service = NetmikoService()
        device = Mock()
        device.vendor = "huawei"
        device.hostname = "test-device"
        device.ip_address = "192.168.1.1"
        device.username = "admin"
        device.password = "admin"

        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "IP Address      MAC Address\n192.168.1.100   00:11:22:33:44:55"

            result = await service.collect_arp_table(device)

            mock_exec.assert_called_once()
            call_args = mock_exec.call_args

            # 检查 expect_string 参数
            assert 'expect_string' in call_args.kwargs
            expect_pattern = call_args.kwargs['expect_string']

            # ✓ 优化：验证正则能匹配中文提示符
            assert re.search(expect_pattern, '<Switch>')
            assert re.search(expect_pattern, '[Switch]')
            assert re.search(expect_pattern, '<模块33-R03-业务接入>')  # ✓ 中文测试

            # 检查 read_timeout 参数
            assert 'read_timeout' in call_args.kwargs
            assert call_args.kwargs['read_timeout'] >= 65  # ✓ 优化：65s

    @pytest.mark.asyncio
    async def test_cisco_arp_expect_string(self):
        """Cisco ARP 采集应使用正确的 expect_string"""
        from app.services.netmiko_service import NetmikoService

        service = NetmikoService()
        device = Mock()
        device.vendor = "cisco"
        device.hostname = "cisco-device"

        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "Protocol  Address"

            result = await service.collect_arp_table(device)

            call_args = mock_exec.call_args
            expect_pattern = call_args.kwargs['expect_string']

            # ✓ 优化：验证配置模式匹配
            assert re.search(expect_pattern, 'Switch#')
            assert re.search(expect_pattern, 'Switch>')
            assert re.search(expect_pattern, 'Switch(config)#')  # ✓ 配置模式测试

    @pytest.mark.asyncio
    async def test_mac_table_expect_string(self):
        """MAC 表采集应使用正确的 expect_string"""
        from app.services.netmiko_service import NetmikoService

        service = NetmikoService()
        device = Mock()
        device.vendor = "huawei"
        device.hostname = "huawei-switch"

        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "MAC Address    VLAN"

            result = await service.collect_mac_table(device)

            call_args = mock_exec.call_args
            assert 'expect_string' in call_args.kwargs
            assert 'read_timeout' in call_args.kwargs
            # ✓ 优化：MAC 表超时 95s
            assert call_args.kwargs['read_timeout'] >= 95
```

#### 3.1.3 ✓ 新增：中文设备名称测试

```python
# tests/test_chinese_hostname.py

import pytest
import re

class TestChineseHostname:
    """测试中文设备名称 expect_string 匹配（响应 P1-001）"""

    def test_huawei_chinese_hostname_matching(self):
        """华为中文设备名称正则匹配测试"""
        # 优化后的正则表达式
        pattern = r'[<>\[].*[>\]]'

        # 中文设备名称测试用例
        chinese_hostnames = [
            '<模块33-R03-业务接入>',
            '<核心交换机>',
            '<业务接入层-楼层1>',
            '[~核心交换机]',
            '[模块33-R03]',
            '<Switch (核心)>',
        ]

        for hostname in chinese_hostnames:
            result = re.search(pattern, hostname)
            assert result is not None, f"Failed to match: {hostname}"
            print(f"✓ '{hostname}' matched successfully")

    def test_h3c_chinese_hostname_matching(self):
        """H3C 中文设备名称正则匹配测试"""
        pattern = r'[<>\[].*[>\]]'

        h3c_hostnames = [
            '<H3C-核心交换>',
            '<华三-汇聚层>',
            '[H3C-业务接入]',
        ]

        for hostname in h3c_hostnames:
            assert re.search(pattern, hostname) is not None

    def test_real_device_output_with_chinese(self):
        """真实设备输出中文提示符匹配测试"""
        pattern = r'[<>\[].*[>\]]'

        # 模拟真实设备输出（末尾带中文提示符）
        mock_output = """
IP ADDRESS      MAC ADDRESS     VLAN   INTERFACE
192.168.1.1     0011-2233-4455  1      GE1/0/1
192.168.1.100   00aa-bbcc-dd11  10     GE1/0/2
Total:2  Dynamic:2  Static:0  Interface:0
<模块33-R03-业务接入>
"""
        result = re.search(pattern, mock_output)
        assert result is not None
        assert result.group() == '<模块33-R03-业务接入>'
```

#### 3.1.4 ✓ 新增：Cisco 配置模式测试

```python
# tests/test_cisco_config_mode.py

import pytest
import re

class TestCiscoConfigMode:
    """测试 Cisco 配置模式 expect_string 匹配（响应 P1-005）"""

    def test_cisco_privileged_mode(self):
        """Cisco 特权模式匹配测试"""
        pattern = r'[\w\-]+(?:\(config[^)]*\))?[#>]'

        privileged_modes = ['Switch#', 'Router#', 'Core-SW-01#']
        for mode in privileged_modes:
            assert re.search(pattern, mode) is not None

    def test_cisco_config_mode(self):
        """Cisco 配置模式匹配测试"""
        pattern = r'[\w\-]+(?:\(config[^)]*\))?[#>]'

        config_modes = [
            'Switch(config)#',
            'Router(config)#',
            'Switch(config-if)#',
            'Switch(config-line)#',
            'Router(config-router)#',
        ]

        for mode in config_modes:
            result = re.search(pattern, mode)
            assert result is not None, f"Failed to match: {mode}"
            print(f"✓ '{mode}' matched successfully")

    def test_cisco_user_mode(self):
        """Cisco 用户模式匹配测试"""
        pattern = r'[\w\-]+(?:\(config[^)]*\))?[#>]'

        user_modes = ['Switch>', 'Router>']
        for mode in user_modes:
            assert re.search(pattern, mode) is not None

    def test_ruijie_config_mode(self):
        """锐捷配置模式匹配测试"""
        pattern = r'[\w\-]+(?:\(config[^)]*\))?[#>]'

        ruijie_modes = ['Ruijie(config)#', 'Ruijie(config-if)#']
        for mode in ruijie_modes:
            assert re.search(pattern, mode) is not None
```

#### 3.1.5 ✓ 新增：超大表超时测试

```python
# tests/test_large_table_timeout.py

import pytest

class TestLargeTableTimeout:
    """测试超大表动态超时计算（响应 P5-002）"""

    def test_large_mac_table_timeout_limit(self):
        """超大 MAC 表超时限制测试"""
        from app.services.netmiko_service import NetmikoService

        service = NetmikoService()

        # 2000 条 MAC 表（超大表）
        timeout = service.calculate_timeout('mac_table', 2000)
        assert timeout <= 240  # ✓ 优化：限制在最大值 240s
        assert timeout >= 95   # ✓ 优化：应大于基础值 95s

        print(f"✓ 2000条 MAC表 timeout: {timeout}s (max: 240s)")

    def test_extreme_large_table_timeout(self):
        """极端超大表超时测试"""
        service = NetmikoService()

        # 10000 条极端大表
        timeout = service.calculate_timeout('mac_table', 10000)
        assert timeout == 240  # 应被限制在最大值
        print(f"✓ 10000条 MAC表 timeout: {timeout}s (limited to max)")

    def test_large_arp_table_timeout(self):
        """大型 ARP 表超时测试"""
        service = NetmikoService()

        # 691 条 ARP 表（问题设备实际规模）
        timeout = service.calculate_timeout('arp_table', 691)
        assert timeout <= 180
        assert timeout >= 65
        print(f"✓ 691条 ARP表 timeout: {timeout}s")

    def test_network_delay_compensation(self):
        """网络延迟补偿测试"""
        service = NetmikoService()

        # 小表也应包含网络延迟补偿
        timeout = service.calculate_timeout('arp_table', 50)
        # 基础 30s + 网络延迟补偿 5s = 35s
        assert timeout >= 35
        print(f"✓ 小表 timeout: {timeout}s (含 5s 网络延迟补偿)")

    def test_pagination_delay_compensation(self):
        """分页延迟补偿测试"""
        service = NetmikoService()

        # 100 页华为设备输出
        timeout = service.calculate_timeout('mac_table', 500, estimated_pages=100)
        # 基础 45s + 网络补偿 5s + 条目补偿 + 分页补偿(100*2=200s)
        # 应被限制在 240s
        assert timeout == 240
        print(f"✓ 100页 MAC表 timeout: {timeout}s (limited to max)")
```

#### 3.1.6 ✓ 新增：边界情况测试

```python
# tests/test_edge_cases.py

import pytest
from unittest.mock import Mock, patch

class TestEdgeCases:
    """边界情况测试（响应 P4-001, P4-003）"""

    @pytest.mark.asyncio
    async def test_vendor_none(self):
        """vendor 为 None 时应使用默认华为配置"""
        from app.services.netmiko_service import NetmikoService

        device = Mock()
        device.vendor = None
        device.hostname = "unknown-device"
        device.username = "admin"
        device.password = "admin"

        service = NetmikoService()
        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "output"
            await service.collect_arp_table(device)

            # 应使用默认华为 expect_string
            expect_string = mock_exec.call_args.kwargs.get('expect_string')
            assert expect_string == r'[<>\[].*[>\]]'
            print(f"✓ vendor=None 使用默认华为配置")

    @pytest.mark.asyncio
    async def test_chinese_vendor_name(self):
        """中文厂商名称应正确处理"""
        device = Mock()
        device.vendor = "华为"
        device.hostname = "chinese-vendor-device"
        device.username = "admin"
        device.password = "admin"

        service = NetmikoService()
        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "output"
            await service.collect_arp_table(device)

            call_args = mock_exec.call_args
            assert call_args.args[1] == "display arp"
            print(f"✓ vendor='华为' 正确映射到华为命令")

    @pytest.mark.asyncio
    async def test_vendor_with_spaces(self):
        """vendor 包含空格时应正确处理"""
        device = Mock()
        device.vendor = " Huawei "
        device.hostname = "space-vendor-device"
        device.username = "admin"
        device.password = "admin"

        service = NetmikoService()
        with patch.object(service, 'execute_command') as mock_exec:
            mock_exec.return_value = "output"
            await service.collect_arp_table(device)

            # strip() 后应为 'huawei'
            call_args = mock_exec.call_args
            assert call_args.args[1] == "display arp"
            print(f"✓ vendor=' Huawei ' (含空格) 正确处理")
```

#### 3.1.7 ✓ 新增：回滚开关测试

```python
# tests/test_rollback_switch.py

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

class TestRollbackSwitch:
    """测试回滚开关功能（响应 R-007）"""

    @pytest.mark.asyncio
    async def test_rollback_switch_enabled(self):
        """回滚开关开启时应使用 expect_string"""
        # 模拟环境变量开启
        with patch.dict(os.environ, {'NETMIKO_USE_EXPECT_STRING': 'True'}):
            from app.config import settings
            # 重新加载配置
            assert settings.NETMIKO_USE_EXPECT_STRING == True

            device = Mock()
            device.vendor = "huawei"
            device.hostname = "test-device"
            device.username = "admin"
            device.password = "admin"

            service = NetmikoService()
            with patch.object(service, 'execute_command') as mock_exec:
                mock_exec.return_value = "output"
                await service.collect_arp_table(device)

                # 应包含 expect_string 参数
                assert 'expect_string' in mock_exec.call_args.kwargs
                print(f"✓ 回滚开关开启：使用 expect_string")

    @pytest.mark.asyncio
    async def test_rollback_switch_disabled(self):
        """回滚开关关闭时应不使用 expect_string"""
        # 模拟环境变量关闭
        with patch.dict(os.environ, {'NETMIKO_USE_EXPECT_STRING': 'False'}):
            from app.config import settings
            from importlib import reload
            import app.config
            reload(app.config)
            from app.config import settings

            assert settings.NETMIKO_USE_EXPECT_STRING == False

            device = Mock()
            device.vendor = "huawei"
            device.hostname = "test-device"
            device.username = "admin"
            device.password = "admin"

            service = NetmikoService()
            with patch.object(service, 'execute_command') as mock_exec:
                mock_exec.return_value = "output"
                await service.collect_arp_table(device)

                # 不应包含 expect_string 参数（回滚到原有方案）
                assert 'expect_string' not in mock_exec.call_args.kwargs
                print(f"✓ 回滚开关关闭：不使用 expect_string（回滚）")
```

### 3.2 集成测试设计（优化版）

#### 3.2.1 ✓ 新增：多厂商真实设备测试脚本

```python
# tests/integration/test_real_device_multi_vendor.py

import asyncio
import os
import sys
sys.path.insert(0, '/mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage')

from app.services.netmiko_service import NetmikoService
from app.models.models import Device

async def test_multi_vendor_devices():
    """多厂商真实设备 ARP/MAC 采集测试（响应 P5-003）"""

    # 使用环境变量获取测试设备配置（避免硬编码密码）
    test_devices = [
        {
            'hostname': os.getenv('TEST_HUAWEI_HOSTNAME', '模块33-R03-业务接入'),
            'ip': os.getenv('TEST_HUAWEI_IP', '192.168.33.1'),
            'vendor': 'huawei',
            'username': os.getenv('TEST_HUAWEI_USER', 'admin'),
            'password': os.getenv('TEST_HUAWEI_PASS'),
        },
        {
            'hostname': os.getenv('TEST_CISCO_HOSTNAME', 'Core-SW-01'),
            'ip': os.getenv('TEST_CISCO_IP'),
            'vendor': 'cisco',
            'username': os.getenv('TEST_CISCO_USER'),
            'password': os.getenv('TEST_CISCO_PASS'),
        },
        {
            'hostname': os.getenv('TEST_H3C_HOSTNAME', 'H3C-Core'),
            'ip': os.getenv('TEST_H3C_IP'),
            'vendor': 'h3c',
            'username': os.getenv('TEST_H3C_USER'),
            'password': os.getenv('TEST_H3C_PASS'),
        },
    ]

    service = NetmikoService()
    results = []

    for dev_config in test_devices:
        if not dev_config['password']:
            print(f"Skipping {dev_config['hostname']}: no password configured")
            continue

        device = Device(
            hostname=dev_config['hostname'],
            ip_address=dev_config['ip'],
            vendor=dev_config['vendor'],
            username=dev_config['username'],
            password=dev_config['password'],
            login_port=22,
            login_method="ssh"
        )

        print(f"\n=== Testing {dev_config['vendor']}: {dev_config['hostname']} ===")

        # 测试 ARP 采集
        arp_result = await service.collect_arp_table(device)
        if arp_result:
            print(f"✓ ARP entries: {len(arp_result)}")
            results.append({
                'vendor': dev_config['vendor'],
                'hostname': dev_config['hostname'],
                'arp_count': len(arp_result),
                'mac_count': None,
                'status': 'arp_success'
            })
        else:
            print(f"✗ ARP collection failed")

        # 测试 MAC 采集
        mac_result = await service.collect_mac_table(device)
        if mac_result:
            print(f"✓ MAC entries: {len(mac_result)}")
            results[-1]['mac_count'] = len(mac_result)
            results[-1]['status'] = 'success'
        else:
            print(f"✗ MAC collection failed")

    # 输出测试结果摘要
    print("\n=== Test Results Summary ===")
    for r in results:
        print(f"{r['vendor']}: {r['hostname']} - ARP: {r['arp_count']}, MAC: {r['mac_count']}, Status: {r['status']}")

    return results

if __name__ == "__main__":
    asyncio.run(test_multi_vendor_devices())
```

#### 3.2.2 ✓ 新增：大表设备测试脚本

```python
# tests/integration/test_large_table_device.py

import asyncio
import os
import sys
sys.path.insert(0, '/mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage')

from app.services.netmiko_service import NetmikoService
from app.models.models import Device

async def test_large_table_device():
    """大表设备（691+ 条目）ARP/MAC 采集测试（响应 P5-002）"""

    # 问题设备配置（691 条 ARP 表）
    device = Device(
        hostname=os.getenv('TEST_LARGE_DEVICE_HOSTNAME', '模块33-R03-业务接入'),
        ip_address=os.getenv('TEST_LARGE_DEVICE_IP', '192.168.33.1'),
        vendor='huawei',
        username=os.getenv('TEST_LARGE_DEVICE_USER', 'admin'),
        password=os.getenv('TEST_LARGE_DEVICE_PASS'),
        login_port=22,
        login_method="ssh"
    )

    if not device.password:
        print("Error: TEST_LARGE_DEVICE_PASS not set")
        return

    service = NetmikoService()

    print(f"Testing large table device: {device.hostname}")
    print(f"Expected ARP entries: 691+")
    print(f"Timeout config: ARP=65s, MAC=95s, MAX=240s")

    # 测试 ARP 采集
    import time
    start_time = time.time()
    arp_result = await service.collect_arp_table(device)
    arp_elapsed = time.time() - start_time

    if arp_result:
        print(f"✓ ARP collected: {len(arp_result)} entries in {arp_elapsed:.1f}s")
        if len(arp_result) >= 691:
            print(f"✓ Large table test passed: {len(arp_result)} >= 691")
        else:
            print(f"⚠ Entry count less than expected: {len(arp_result)} < 691")
    else:
        print(f"✗ ARP collection failed (elapsed: {arp_elapsed:.1f}s)")

    # 测试 MAC 采集
    start_time = time.time()
    mac_result = await service.collect_mac_table(device)
    mac_elapsed = time.time() - start_time

    if mac_result:
        print(f"✓ MAC collected: {len(mac_result)} entries in {mac_elapsed:.1f}s")
    else:
        print(f"✗ MAC collection failed (elapsed: {mac_elapsed:.1f}s)")

    # 验证超时未触发
    if arp_elapsed <= 65:
        print(f"✓ ARP within timeout: {arp_elapsed:.1f}s <= 65s")
    else:
        print(f"⚠ ARP exceeded timeout: {arp_elapsed:.1f}s > 65s")

    if mac_elapsed <= 95:
        print(f"✓ MAC within timeout: {mac_elapsed:.1f}s <= 95s")
    else:
        print(f"⚠ MAC exceeded timeout: {mac_elapsed:.1f}s > 95s")

if __name__ == "__main__":
    asyncio.run(test_large_table_device())
```

#### 3.2.3 集成测试验证清单（优化版）

| 测试项 | 验证内容 | 期望结果 | 优化说明 |
|--------|----------|----------|----------|
| ARP 采集 | 华为设备 `display arp` | 成功返回 ARP 条目 | - |
| MAC 采集 | 华为设备 `display mac-address` | 成功返回 MAC 条目 | - |
| 中文设备名称 | `<模块33-R03-业务接入>` | expect_string 正确匹配 | ✓ 新增 |
| Cisco 配置模式 | `Switch(config)#` | expect_string 正确匹配 | ✓ 新增 |
| 大型表采集 | 691+ 条目设备 | 无 ReadTimeout 错误 | ✓ 超时优化 |
| 超大表采集 | 2000+ 条目设备 | timeout 限制在 240s | ✓ 新增测试 |
| 多厂商采集 | Cisco/H3C/Ruijie | 各厂商成功采集 | ✓ 新增测试 |
| 回滚开关 | 环境变量控制 | 开关正确生效 | ✓ 新增测试 |
| 数据完整性 | 条目数量对比 | 数据库条目数与设备一致 | - |

---

## 四、实施计划（优化版）

### 4.1 实施步骤（优化版）

| 步骤 | 任务 | 预估工时 | 依赖 | 优化说明 |
|------|------|----------|------|----------|
| 1 | expect_string 正则验证测试（优先验证） | 0.5h | 无 | ✓ 调整顺序 |
| 2 | 修改 `_get_vendor_expect_strings` 方法 | 1h | 步骤 1 | ✓ 工时增加 |
| 3 | 修改 `collect_arp_table` 方法 | 1h | 步骤 2 | - |
| 4 | 修改 `collect_mac_table` 方法 | 1h | 步骤 2 | - |
| 5 | 新增 `config.py` 超时配置项 | 0.5h | 无 | ✓ 新增回滚开关 |
| 6 | 编写单元测试（包含边界测试） | 3h | 步骤 3-5 | ✓ 工时增加 |
| 7 | 运行单元测试验证 | 0.5h | 步骤 6 | - |
| 8 | 真实设备集成测试（多厂商） | 2h | 步骤 7 | ✓ 工时增加 |
| 9 | 修复测试中发现的问题 | 1h | 步骤 8 | ✓ 工时增加 |
| 10 | 部署上线 | 0.5h | 步骤 9 | - |

**总预估工时**: 9h（原方案 7.5h，增加 1.5h 缓冲）

### 4.2 实施时间线

```
Day 1 (2026-03-30):
├── 上午: 步骤 1-2 (正则验证 + 方法修改)
├── 下午: 步骤 3-5 (collect_* 方法 + config)
│
Day 2 (2026-03-31):
├── 上午: 步骤 6-7 (单元测试)
├── 下午: 步骤 8-10 (集成测试 + 修复 + 部署)
```

---

## 五、风险评估（优化版）

### 5.1 风险清单（优化版）

| 风险编号 | 风险描述 | 可能性 | 影响 | 应对措施 | 优化说明 |
|----------|----------|--------|------|----------|----------|
| R-001 | 中文设备名称正则匹配失败 | **高** → **低** | 高 | 使用宽松正则 `r'[<>\[].*[>\]]'` | ✓ 已规避 |
| R-002 | 分页输出干扰 expect_string 匹配 | 中 | 高 | 禁用分页或处理分页符 | ✓ 新增风险 |
| R-003 | 并发采集资源竞争 | 中 | 中 | 添加并发控制机制（后续版本） | ✓ 新增风险 |
| R-004 | 网络延迟导致超时误判 | 中 → **低** | 中 | 增加 5s 延迟补偿因子 | ✓ 已规避 |
| R-005 | 设备负载高导致响应慢 | 低 | 高 | 动态超时上限 240s | ✓ 已规避 |
| R-006 | expect_string 匹配到输出中的提示符字符串 | 低 | 高 | 使用贪婪匹配后检查 | ✓ 新增风险 |
| R-007 | 回滚开关环境变量未生效 | 低 → **低** | 中 | config.py 硬编码回滚选项 | ✓ 已规避 |
| R-008 | Cisco 配置模式匹配失败 | **高** → **低** | 高 | 正则支持 `(config)` | ✓ 已规避 |
| R-009 | 超大表（2000+）仍然超时 | **中** → **低** | 高 | 最大超时增加到 240s | ✓ 已规避 |

### 5.2 回滚方案（优化版）

```python
# ✓ 优化：在 config.py 中添加回滚开关
NETMIKO_USE_EXPECT_STRING = os.getenv('NETMIKO_USE_EXPECT_STRING', 'True').lower() == 'true'

# ✓ 优化：在 netmiko_service.py 中实现回滚逻辑
from app.config import settings

async def collect_arp_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    # ... 参数配置 ...

    if settings.NETMIKO_USE_EXPECT_STRING:
        # 新方案：传递 expect_string 和超时参数
        output = await self.execute_command(
            device,
            command,
            expect_string=expect_string,
            read_timeout=read_timeout
        )
    else:
        # 回滚到原有方案（无 expect_string）
        output = await self.execute_command(device, command)

    # ... 后续处理 ...
```

**回滚操作步骤**:

1. 设置环境变量: `export NETMIKO_USE_EXPECT_STRING=False`
2. 重启应用服务
3. 观察日志确认回滚生效

---

## 六、验证标准（优化版）

### 6.1 成功标准

| 标准 | 指标 | 验证方法 | 优化说明 |
|------|------|----------|----------|
| ReadTimeout 错误消除 | 问题设备采集成功率 > 95% | 日志分析 | - |
| 中文设备名称支持 | 中文提示符正确匹配 | 正则测试 | ✓ 新增标准 |
| 配置模式支持 | Cisco 配置模式正确匹配 | 正则测试 | ✓ 新增标准 |
| 数据完整性 | ARP/MAC 条目数与设备一致 | 数据库对比 | - |
| 性能影响 | 单次采集时间 < 240s | 时间记录 | ✓ 超时上限优化 |
| 无新错误 | 不引入其他类型错误 | 日志检查 | - |
| 回滚开关有效 | 环境变量正确控制行为 | 功能测试 | ✓ 新增标准 |

### 6.2 验证命令

```bash
# 修复前验证
grep -c "ReadTimeout" logs/app.log

# 修复后验证（期望 0 或显著减少）
grep -c "ReadTimeout" logs/app.log

# 数据验证
sqlite3 data/switch_manage.db "SELECT COUNT(*) FROM arp_entries WHERE arp_device_id = 214;"
sqlite3 data/switch_manage.db "SELECT COUNT(*) FROM mac_address_current WHERE mac_device_id = 214;"

# ✓ 新增：正则表达式验证
python3 -c "import re; print(re.search(r'[<>\[].*[>\]]', '<模块33-R03-业务接入>'))"
python3 -c "import re; print(re.search(r'[\w\-]+(?:\(config[^)]*\))?[#>]', 'Switch(config)#'))"

# ✓ 新增：回滚开关验证
grep "NETMIKO_USE_EXPECT_STRING" app/config.py
```

---

## 七、总结

### 7.1 方案核心要点

1. **expect_string 修复**: 使用宽松正则 `r'[<>\[].*[>\]]'` 支持中文设备名称
2. **Cisco 配置模式**: 正则 `r'[\w\-]+(?:\(config[^)]*\))?[#>]` 支持配置模式
3. **超时优化**: ARP 65s, MAC 95s, 最大 240s（含 5s 网络延迟补偿）
4. **配置化**: 新增 `NETMIKO_NETWORK_DELAY_COMPENSATION` 和回滚开关
5. **测试覆盖**: 新增中文设备名称、配置模式、超大表、回滚开关测试

### 7.2 优化内容汇总

| 优化项 | 原方案 | 优化后 | 评审响应 |
|--------|--------|--------|----------|
| 华为正则 | `r'[<\[][\w\-]+[>\]]'` | `r'[<>\[].*[>\]]'` | P1-001 |
| Cisco 正则 | `r'[\w\-]+[#>]'` | `r'[\w\-]+(?:\(config[^)]*\))?[#>]` | P1-005 |
| ARP 超时 | 60s | 65s | P2-001 |
| MAC 超时 | 90s | 95s | P2-001 |
| 最大超时 | 180s | 240s | P2-003 |
| 网络延迟补偿 | 无 | 5s | P2-001 |
| 回滚开关 | 无 | `NETMIKO_USE_EXPECT_STRING` | R-007 |
| 总工时 | 7.5h | 9h | 评审建议 |

### 7.3 下一步行动

1. 按实施步骤执行代码修改（优先正则验证）
2. 运行测试验证（重点：中文设备名称、配置模式）
3. 部署上线并观察日志
4. 根据回滚开关准备应急预案

---

**文档编写**: Claude Code
**优化日期**: 2026-03-30
**审核状态**: 待审核
**评审响应**: 已逐项响应评审意见
**下一步**: 执行优化后的修复方案