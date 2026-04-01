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
# 各厂商 ARP/MAC 地址数据格式分析

**采集时间**: 2026-04-01 09:40  
**采集人**: 乐乐 (运维开发工程师)  
**文档版本**: 1.0

---

## 📋 概述

本报告分析了 3 家主流网络设备厂商（Huawei、Cisco、H3C）的 ARP 表和 MAC 地址表输出格式，为 `switch_manage` 项目的数据采集和解析逻辑提供依据。

### 测试设备信息

| 序号 | 设备名称 | 厂商 | IP 地址 | 设备型号 | 软件版本 |
|------|----------|------|---------|----------|----------|
| 1 | 模块 33-R03-业务接入 | Huawei | 10.23.2.56 | - | VRP |
| 2 | 模块 33-R08-IPMI 接入 | Cisco | 10.23.2.13 | - | Cisco IOS |
| 3 | 模块 33-R13-IPMI 接入 | H3C | 10.23.2.50 | S5120V3-28S-LI | Comware V7 7.1.070 |

---

## 🔍 ARP 表格式分析

### 1. Huawei (华为)

#### 命令
```bash
display arp
```

#### 输出示例
```
IP ADDRESS      MAC ADDRESS     EXPIRE(M) TYPE INTERFACE      VPN-INSTANCE      
                                          VLAN 
------------------------------------------------------------------------------
10.23.2.56      3cc7-86b4-72c4            I -  Vlanif2        VLAN2              
10.23.2.54      3cc7-86b4-7226  13        D-0  GE0/0/24       VLAN2              
                                          2    
------------------------------------------------------------------------------
Total:10        Dynamic:9       Static:0     Interface:1
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | IP ADDRESS | IP 地址 | `10.23.2.56` |
| 2 | MAC ADDRESS | MAC 地址（横线分隔） | `3cc7-86b4-72c4` |
| 3 | EXPIRE(M) | 过期时间（分钟），`-` 表示永久 | `13` 或 `-` |
| 4 | TYPE | 类型：`I`=本机，`D`=动态，`S`=静态 | `D-0` |
| 5 | INTERFACE | 接口名称 | `GE0/0/24` |
| 6 | VPN-INSTANCE | VPN 实例 | `VLAN2` |
| 7 | VLAN | VLAN ID（可能跨行显示） | `2` |

#### 注意事项
⚠️ **VLAN 字段可能跨行显示**：某些条目的 VLAN ID 会显示在下一行，解析时需要特殊处理

#### 解析代码建议
```python
def _parse_huawei_arp_table(output: str) -> List[Dict[str, Any]]:
    """解析华为 ARP 表"""
    arp_entries = []
    lines = output.strip().split('\n')
    
    # 跳过表头
    start_index = 0
    for i, line in enumerate(lines):
        if 'IP ADDRESS' in line and 'MAC ADDRESS' in line:
            start_index = i + 1
            break
    
    current_entry = None
    for line in lines[start_index:]:
        if not line.strip() or '---' in line or 'Total:' in line:
            continue
        
        # 检查是否是 VLAN 续行（只有 VLAN ID）
        if current_entry and line.strip().isdigit():
            current_entry['vlan_id'] = int(line.strip())
            continue
        
        parts = line.split()
        if len(parts) >= 5:
            try:
                entry = {
                    'ip_address': parts[0],
                    'mac_address': parts[1].upper().replace('-', ':'),  # 标准化为冒号分隔
                    'expire_minutes': parts[2] if parts[2] != '-' else None,
                    'type': parts[3],
                    'interface': parts[4],
                    'vlan_id': None  # 可能在下一行
                }
                # 检查是否有 inline VLAN
                if len(parts) > 5 and parts[5].startswith('VLAN'):
                    vlan_str = parts[5].replace('VLAN', '')
                    if vlan_str.isdigit():
                        entry['vlan_id'] = int(vlan_str)
                
                current_entry = entry
                arp_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return arp_entries
```

---

### 2. Cisco (思科)

#### 命令
```bash
show ip arp
```

#### 输出示例
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  10.23.2.13              -   2401.c7d9.2241  ARPA   Vlan2
Internet  10.23.2.1               3   609b.b431.d2c3  ARPA   Vlan2
Internet  10.23.2.59              9   3cc7.86b4.7242  ARPA   Vlan2
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | Protocol | 协议类型 | `Internet` |
| 2 | Address | IP 地址 | `10.23.2.13` |
| 3 | Age (min) | 存活时间（分钟），`-` 表示本机 | `-` 或 `3` |
| 4 | Hardware Addr | MAC 地址（点分隔） | `2401.c7d9.2241` |
| 5 | Type | 封装类型 | `ARPA` |
| 6 | Interface | 接口名称 | `Vlan2` |

#### 注意事项
- MAC 地址使用**点分隔**格式（xxxx.xxxx.xxxx）
- 第一列是协议类型，解析时应跳过

#### 解析代码建议
```python
def _parse_cisco_arp_table(output: str) -> List[Dict[str, Any]]:
    """解析 Cisco ARP 表"""
    arp_entries = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # 跳过表头和空行
        if not line.strip() or 'Protocol' in line or 'Address' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 6:
            try:
                entry = {
                    'ip_address': parts[1],  # 第 2 列是 IP
                    'mac_address': parts[3].upper().replace('.', ':'),  # 标准化
                    'age_minutes': parts[2] if parts[2] != '-' else '0',
                    'type': parts[4],
                    'interface': parts[5]
                }
                arp_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return arp_entries
```

---

### 3. H3C (新华三)

#### 命令
```bash
display arp
```

#### 输出示例
```
  Type: S-Static   D-Dynamic   O-Openflow   R-Rule   M-Multiport  I-Invalid
IP address      MAC address    VLAN/VSI name Interface                Aging Type
10.23.2.1       609b-b431-d2c3 2             BAGG1                    927   D   
10.23.2.16      f4a4-d6de-8aa9 2             BAGG1                    1093  D   
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | IP address | IP 地址 | `10.23.2.1` |
| 2 | MAC address | MAC 地址（横线分隔） | `609b-b431-d2c3` |
| 3 | VLAN/VSI name | VLAN ID | `2` |
| 4 | Interface | 接口名称 | `BAGG1` |
| 5 | Aging | 存活时间（秒） | `927` |
| 6 | Type | 类型：`D`=动态，`S`=静态，`I`=本机 | `D` |

#### 注意事项
- 第一行是类型说明，需要跳过
- MAC 地址使用**横线分隔**格式（xxxx-xxxx-xxxx）
- Aging 单位是**秒**（Huawei 是分钟）

#### 解析代码建议
```python
def _parse_h3c_arp_table(output: str) -> List[Dict[str, Any]]:
    """解析 H3C ARP 表"""
    arp_entries = []
    lines = output.strip().split('\n')
    
    # 跳过类型说明行和表头
    start_index = 0
    for i, line in enumerate(lines):
        if 'IP address' in line and 'MAC address' in line:
            start_index = i + 1
            break
    
    for line in lines[start_index:]:
        if not line.strip():
            continue
        
        parts = line.split()
        if len(parts) >= 6:
            try:
                entry = {
                    'ip_address': parts[0],
                    'mac_address': parts[1].upper().replace('-', ':'),  # 标准化
                    'vlan_id': int(parts[2]) if parts[2].isdigit() else None,
                    'interface': parts[3],
                    'aging_seconds': int(parts[4]) if parts[4].isdigit() else None,
                    'type': parts[5]
                }
                arp_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return arp_entries
```

---

## 🔍 MAC 地址表格式分析

### 1. Huawei (华为)

#### 命令
```bash
display mac-address
```

#### 输出示例
```
-------------------------------------------------------------------------------
MAC Address    VLAN/VSI/BD                       Learned-From        Type      
-------------------------------------------------------------------------------
0cda-411d-0331 1/-/-                             GE0/0/24            dynamic   
0cda-411d-0333 1/-/-                             GE0/0/24            dynamic   
3cc7-86b4-7226 2/-/-                             GE0/0/24            dynamic   
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | MAC Address | MAC 地址（横线分隔） | `0cda-411d-0331` |
| 2 | VLAN/VSI/BD | VLAN/VSI/BD 信息（格式：VLAN/-/-） | `1/-/-` |
| 3 | Learned-From | 学习到的接口 | `GE0/0/24` |
| 4 | Type | 类型：`dynamic`/`static`/`blackhole` | `dynamic` |

#### 解析代码建议
```python
def _parse_huawei_mac_table(output: str) -> List[Dict[str, Any]]:
    """解析华为 MAC 地址表"""
    mac_entries = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # 跳过表头和分隔线
        if not line.strip() or '---' in line or 'MAC Address' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 4:
            try:
                vlan_str = parts[1].split('/')[0]  # 提取 VLAN 部分
                entry = {
                    'mac_address': parts[0].upper().replace('-', ':'),
                    'vlan_id': int(vlan_str) if vlan_str.isdigit() else None,
                    'interface': parts[2],
                    'address_type': parts[3].lower()
                }
                mac_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return mac_entries
```

---

### 2. Cisco (思科)

#### 命令
```bash
show mac address-table
```

#### 输出示例
```
          Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
 All    0100.0ccc.cccc    STATIC      CPU
   2    00e0.fc09.bcf9    DYNAMIC     Gi1/0/45
   2    04da.d25c.24b0    DYNAMIC     Po1
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | Vlan | VLAN ID | `2` 或 `All` |
| 2 | Mac Address | MAC 地址（点分隔） | `00e0.fc09.bcf9` |
| 3 | Type | 类型：`DYNAMIC`/`STATIC`/`SECURE` | `DYNAMIC` |
| 4 | Ports | 端口名称 | `Gi1/0/45` |

#### 注意事项
- 有表头和分隔线需要跳过
- MAC 地址使用**点分隔**格式
- VLAN 可能是 `All`（表示所有 VLAN）

#### 解析代码建议
```python
def _parse_cisco_mac_table(output: str) -> List[Dict[str, Any]]:
    """解析 Cisco MAC 地址表"""
    mac_entries = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # 跳过表头、分隔线和空行
        if not line.strip():
            continue
        if 'Mac Address Table' in line or '----' in line:
            continue
        if 'Vlan' in line and 'Mac Address' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 4:
            try:
                vlan_str = parts[0]
                entry = {
                    'vlan_id': int(vlan_str) if vlan_str.isdigit() else None,
                    'mac_address': parts[1].upper().replace('.', ':'),
                    'address_type': parts[2].lower(),
                    'interface': parts[3]
                }
                mac_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return mac_entries
```

---

### 3. H3C (新华三)

#### 命令
```bash
display mac-address
```

#### 输出示例
```
MAC Address      VLAN ID    State            Port/Nickname            Aging
04da-d25c-24af   1          Learned          BAGG5                    Y
00e0-fc09-bcf9   2          Learned          GE1/0/16                 Y
2053-83a5-5896   2          Learned          BAGG1                    Y
```

#### 字段解析

| 列号 | 字段名 | 说明 | 示例 |
|------|--------|------|------|
| 1 | MAC Address | MAC 地址（横线分隔） | `04da-d25c-24af` |
| 2 | VLAN ID | VLAN ID | `1` |
| 3 | State | 状态：`Learned`/`Static` | `Learned` |
| 4 | Port/Nickname | 端口名称 | `BAGG5` |
| 5 | Aging | 老化状态：`Y`=老化，`N`=不老化 | `Y` |

#### 解析代码建议
```python
def _parse_h3c_mac_table(output: str) -> List[Dict[str, Any]]:
    """解析 H3C MAC 地址表"""
    mac_entries = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # 跳过表头和空行
        if not line.strip() or 'MAC Address' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 5:
            try:
                entry = {
                    'mac_address': parts[0].upper().replace('-', ':'),
                    'vlan_id': int(parts[1]) if parts[1].isdigit() else None,
                    'state': parts[2].lower(),
                    'interface': parts[3],
                    'aging': parts[4] == 'Y'
                }
                mac_entries.append(entry)
            except (ValueError, IndexError):
                continue
    
    return mac_entries
```

---

## 📊 格式对比总结

### ARP 表对比

| 特性 | Huawei | Cisco | H3C |
|------|--------|-------|-----|
| **命令** | `display arp` | `show ip arp` | `display arp` |
| **MAC 分隔符** | 横线 `-` | 点 `.` | 横线 `-` |
| **IP 列位置** | 第 1 列 | 第 2 列 | 第 1 列 |
| **VLAN 字段** | 有（可能跨行） | 无（在 Interface 中） | 有（第 3 列） |
| **老化时间单位** | 分钟 | 分钟 | 秒 |
| **类型标识** | `I`/`D`/`S` | `ARPA` | `D`/`S`/`I` |

### MAC 表对比

| 特性 | Huawei | Cisco | H3C |
|------|--------|-------|-----|
| **命令** | `display mac-address` | `show mac address-table` | `display mac-address` |
| **MAC 分隔符** | 横线 `-` | 点 `.` | 横线 `-` |
| **VLAN 列位置** | 第 2 列 | 第 1 列 | 第 2 列 |
| **类型字段名** | Type | Type | State |
| **类型值** | dynamic/static | DYNAMIC/STATIC | Learned/Static |

---

## 🔧 对现有代码的影响

### 当前问题确认

根据 MEMORY.md 中记录的问题：
> `arp_current` 表字段：
> - `ip_address`：实际的数据是 MAC 地址
> - `mac_address`：实际数据是类似 "D0" 等数据

**根因分析**：

现有代码 `_parse_arp_table` 方法（`netmiko_service.py` 第 679-685 行）假设华为设备输出格式为：
```python
entry = {
    'ip_address': parts[0],
    'mac_address': parts[1].upper(),
    'vlan_id': int(parts[2]) if parts[2].isdigit() else None,
    'interface': parts[3] if len(parts) > 3 else None
}
```

但**实际采集到的数据显示**：
1. Huawei 设备输出格式与代码假设**一致**（IP 在第 1 列，MAC 在第 2 列）
2. 问题可能出在**表头识别失败**导致从错误行开始解析
3. 或者设备输出包含**特殊字符/格式**导致 split() 分割异常

### 修复建议

#### 1. 增强表头识别

```python
# 当前代码
for i, line in enumerate(lines):
    if 'IP' in line and 'MAC' in line:
        start_index = i + 1
        break

# 改进后
for i, line in enumerate(lines):
    # 更精确的表头匹配
    if 'IP ADDRESS' in line.upper() and 'MAC ADDRESS' in line.upper():
        start_index = i + 1
        break
    # 备用模式：检查是否有典型 ARP 表头特征
    if re.search(r'IP\s+ADDRESS.*MAC\s+ADDRESS', line, re.IGNORECASE):
        start_index = i + 1
        break
```

#### 2. 添加数据验证

```python
# 在添加到结果前验证 IP 和 MAC 格式
import re

IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
MAC_PATTERN = re.compile(r'^[0-9A-Fa-f]{2}([-:])[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}\1[0-9A-Fa-f]{2}$')

def _validate_arp_entry(ip: str, mac: str) -> bool:
    """验证 ARP 条目格式"""
    return bool(IP_PATTERN.match(ip) and MAC_PATTERN.match(mac))
```

#### 3. 添加调试日志

```python
logger.debug(f"ARP 原始输出:\n{output}")
logger.debug(f"解析后条目数：{len(arp_entries)}")
for entry in arp_entries[:5]:  # 只记录前 5 条
    logger.debug(f"  ARP 条目：{entry}")
```

---

## 📝 后续行动项

| 编号 | 任务 | 优先级 | 状态 |
|------|------|--------|------|
| 1 | 修复 `_parse_arp_table` 表头识别逻辑 | P0 | ⏳ 待处理 |
| 2 | 添加 IP/MAC 格式验证 | P0 | ⏳ 待处理 |
| 3 | 统一 MAC 地址格式（标准化为冒号分隔） | P1 | ⏳ 待处理 |
| 4 | 添加解析调试日志 | P1 | ⏳ 待处理 |
| 5 | 更新 `_parse_huawei_mac_table` 处理 VLAN 跨行 | P2 | ⏳ 待处理 |
| 6 | 添加 H3C 设备解析支持 | P2 | ⏳ 待处理 |

---

## 📎 附录：原始数据样本

### Huawei ARP 样本（10 条）
```
IP ADDRESS      MAC ADDRESS     EXPIRE(M) TYPE INTERFACE      VPN-INSTANCE      
                                          VLAN 
------------------------------------------------------------------------------
10.23.2.56      3cc7-86b4-72c4            I -  Vlanif2        VLAN2              
10.23.2.54      3cc7-86b4-7226  13        D-0  GE0/0/24       VLAN2              
10.23.2.55      3cc7-86b4-7336  12        D-0  GE0/0/24       VLAN2              
```

### Cisco ARP 样本（3 条）
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  10.23.2.13              -   2401.c7d9.2241  ARPA   Vlan2
Internet  10.23.2.1               3   609b.b431.d2c3  ARPA   Vlan2
Internet  10.23.2.59              9   3cc7.86b4.7242  ARPA   Vlan2
```

### H3C ARP 样本（10 条）
```
  Type: S-Static   D-Dynamic   O-Openflow   R-Rule   M-Multiport  I-Invalid
IP address      MAC address    VLAN/VSI name Interface                Aging Type
10.23.2.1       609b-b431-d2c3 2             BAGG1                    927   D   
10.23.2.16      f4a4-d6de-8aa9 2             BAGG1                    1093  D   
```

---

**文档结束**
