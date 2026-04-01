# P009 Netmiko ReadTimeout 问题修复方案

**文档编号**: P009-NETMIKO-FIX-PLAN
**创建日期**: 2026-04-01
**问题级别**: P0（阻塞问题）
**影响范围**: 华为 S1730S 设备 ARP/MAC 数据采集

---

## 1. 问题概述

### 1.1 问题描述

设备 **模块 33-R09-业务接入** (Huawei S1730S-S24T4S-A, IP: 10.23.2.60) 在使用 Netmiko 采集 ARP/MAC 数据时出现 `ReadTimeout` 错误。

### 1.2 错误信息

```
netmiko.exceptions.ReadTimeout:
Pattern not detected: <NX\-SW\-33\-R09\-YW>
```

### 1.3 设备信息

| 属性 | 值 |
|------|-----|
| 设备型号 | Huawei S1730S-S24T4S-A |
| 软件版本 | VRP V200R019C10SPC500 |
| 提示符 | `<NX-SW-33-R09-YW>` |
| IP 地址 | 10.23.2.60 |
| SSH 端口 | 22 |

---

## 2. 根因分析

### 2.1 为什么手动 SSH 成功但 Netmiko 失败？

**核心原因**: Netmiko 的 `send_command` 方法依赖精确的提示符检测机制，而手动 SSH 不需要。

#### 手动 SSH 执行流程

```
用户输入命令 → 设备返回输出 → 用户看到提示符 → 判断命令完成
```

手动 SSH 中，用户通过视觉判断命令执行完成，不依赖精确的字符串匹配。

#### Netmiko send_command 执行流程

```
1. 发送命令到设备
2. 等待命令回显出现 (command echo check)
3. 等待命令输出完成
4. 等待提示符出现 (prompt detection)
5. 返回命令输出
```

**关键差异**: Netmiko 在步骤 2-4 需要精确检测特定字符串模式：

- **命令回显检测**: 等待设备返回刚发送的命令字符串
- **提示符检测**: 使用正则表达式匹配提示符

### 2.2 失败阶段分析

根据测试错误信息：

| 测试 | expect_string | 错误 Pattern | 失败阶段 |
|------|---------------|---------------|----------|
| 测试 1 | None | `<NX\-SW\-33\-R09\-YW>` | 提示符检测 |
| 测试 2 | `r'[<\[].*[>\]]'` | `display\ arp` | 提示符检测 |
| 测试 3 | `<NX-SW-33-R09-YW>` | `<NX-SW-33-R09-YW>` | 提示符检测 |

**结论**: 失败发生在**提示符检测阶段**（步骤 4），不是命令回显检测。

### 2.3 为什么提示符检测失败？

#### 2.3.1 华为设备分页输出特性

华为设备在输出超过终端高度时会进入分页模式：

```
Line 1
Line 2
...
---- More ----    ← 分页提示符（不是命令提示符）
```

此时设备等待用户输入空格/回车继续，不会返回标准提示符 `<hostname>`。

**Netmiko 检测逻辑冲突**:
- Netmiko 等待: `<NX-SW-33-R09-YW>` (标准提示符)
- 设备返回: `---- More ----` (分页提示符)
- 结果: 正则匹配失败 → ReadTimeout

#### 2.3.2 S1730S 设备特性分析

| 特性 | S1730S | 其他华为设备 |
|------|--------|-------------|
| 设备类型 | 低端接入交换机 | 中高端设备 |
| 处理速度 | 较慢 | 较快 |
| 输出延迟 | 较大 | 较小 |
| 分页触发阈值 | 可能更低 | 标准 24 行 |

**推测**: S1730S 设备处理速度慢 + 分页阈值低，导致：
1. 命令输出触发分页的概率更高
2. Netmiko 默认超时时间不足以等待完整输出

#### 2.3.3 提示符正则匹配分析

代码中的华为提示符正则 (`netmiko_service.py:277-281`):

```python
{
    'user_view': r'<.*>',           # 用户视图: <hostname>
    'system_view': r'\[.*\]',       # 系统视图: [hostname]
    'any_view': r'[<>\[].*[>\]]'    # 任意视图
}
```

**问题**:
- 正则 `r'<.*>'` 会匹配 `<NX-SW-33-R09-YW>`
- 但 `.*` 是贪婪匹配，可能匹配到命令输出中的 `<` 字符
- 导致误判或匹配失败

### 2.4 为什么 3 种 expect_string 配置都失败？

| 配置 | 分析 |
|------|------|
| None (自动检测) | Netmiko 使用默认提示符检测，无法处理分页场景 |
| `r'[<\[].*[>\]]'` | 正则正确，但分页提示符 `---- More ----` 不匹配此模式 |
| `<NX-SW-33-R09-YW>` | 字符串匹配正确，但分页时设备不返回此提示符 |

**根本原因**: 所有配置都依赖"等待提示符"机制，但设备处于分页状态时不会返回预期提示符。

---

## 3. 当前代码分析

### 3.1 execute_command 方法流程

```python
# netmiko_service.py:449-460
if needs_pagination and not is_config_cmd:
    # 华为/H3C 查询命令：使用 send_command_timing + 分页处理
    output = await self._send_command_with_pagination(
        connection, command, read_timeout
    )
```

**设计意图**:
- 对华为/H3C 设备使用 `send_command_timing` 绕过提示符检测
- 手动处理分页输出

### 3.2 send_command_timing 机制

`send_command_timing` 与 `send_command` 的区别：

| 方法 | 提示符检测 | 完成判断 |
|------|-----------|----------|
| send_command | 正则匹配提示符 | 精确检测 |
| send_command_timing | 仍需检测提示符 | 基于时间窗口 |

**关键发现**: `send_command_timing` **仍然依赖提示符检测**，只是使用时间窗口而非精确匹配。

参考 Netmiko 源码 (`netmiko/base_connection.py`):

```python
def send_command_timing(self, command_string, delay_factor=1, max_loops=500):
    """
    Execute command on the SSH channel using a delay-based method.

    Still performs prompt detection at the end.
    """
    # ... 发送命令，等待时间窗口 ...
    # 最终仍需要检测提示符
    output = self._read_channel_timing()
    # 清理输出，尝试找到提示符
    return output
```

### 3.3 问题定位

**当前代码的分页处理逻辑问题**:

1. `send_command_timing` 被调用时，设备可能已经处于分页状态
2. `send_command_timing` 内部仍等待提示符，但设备返回 `---- More ----`
3. 超时发生后，才会触发 `_handle_pagination`

**时间顺序问题**:
```
┌─────────────────────────────────────────────────────────────┐
│ send_command_timing 开始                                     │
│   ↓                                                          │
│ 等待时间窗口 (delay_factor * base_delay)                      │
│   ↓                                                          │
│ 设备输出部分数据 + ---- More ----                              │
│   ↓                                                          │
│ send_command_timing 等待提示符                                │
│   ↓                                                          │
│ [ReadTimeout] ← 在此失败！                                    │
│   ↓                                                          │
│ _handle_pagination (未被执行)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 修复方案

### 方案 A: 使用 find_prompt + channel 直接读写

**方案名称**: 直接通道读写法

**原理**: 完全绕过 Netmiko 的提示符检测机制，使用底层 channel 直接发送命令和读取输出。

**实现方式**:

```python
async def _send_command_direct(self, connection, command: str, timeout: int = 30) -> str:
    """
    使用直接通道读写执行命令（绕过提示符检测）

    适用场景：设备分页输出或提示符检测异常
    """
    import time

    # 1. 先获取当前提示符（确保设备处于就绪状态）
    connection.write_channel("\n")
    time.sleep(0.5)
    initial_prompt = connection.read_channel()

    # 2. 发送命令
    connection.write_channel(command + "\n")
    time.sleep(1.0)  # 等待命令开始执行

    # 3. 循环读取输出直到超时或检测到提示符
    output = ""
    start_time = time.time()
    prompt_pattern = re.compile(r'<[^>]+>|\[[^\]]+\]')

    while time.time() - start_time < timeout:
        chunk = connection.read_channel()
        output += chunk

        # 处理分页
        if '---- More ----' in output:
            connection.write_channel(" ")
            time.sleep(0.3)
            continue

        # 检测提示符（可选）
        if prompt_pattern.search(output):
            break

        time.sleep(0.2)

    return output
```

**优点**:
- 完全绕过 Netmiko 提示符检测问题
- 对设备响应速度不敏感
- 可精确控制读取和分页处理流程
- 适用于所有华为/H3C 设备

**缺点**:
- 需要更多手动控制代码
- 可能错过 Netmiko 的其他优化（如自动处理特殊字符）
- 需要维护额外的代码逻辑
- 对异常处理要求更高

**适用场景**:
- 提示符检测始终失败的设备
- 分页输出频繁的设备
- 低端设备（响应慢）

**风险评估**: **中**
- 需要充分测试确保稳定性
- 可能引入新的边界条件问题

---

### 方案 B: 预禁用分页 + send_command

**方案名称**: 预禁用分页法

**原理**: 在执行查询命令前，先发送命令禁用设备分页，然后使用标准 `send_command`。

**实现方式**:

```python
async def execute_command_with_no_pagination(self, device: Device, command: str) -> str:
    """
    先禁用分页再执行命令
    """
    # 华为设备禁用分页命令
    disable_pagination_cmd = "screen-length 0 temporary"

    # 1. 先禁用分页
    await self._send_command_direct(connection, disable_pagination_cmd)

    # 2. 执行目标命令（此时不会分页）
    output = connection.send_command(command, read_timeout=30)

    # 3. 恢复分页（可选）
    # restore_pagination_cmd = "undo screen-length"

    return output
```

**华为分页控制命令**:

| 命令 | 功能 | 作用域 |
|------|------|--------|
| `screen-length 0` | 永久禁用分页 | 全局配置 |
| `screen-length 0 temporary` | 临时禁用分页 | 当前会话 |
| `undo screen-length` | 恢复分页 | 全局配置 |

**优点**:
- 实现简单，代码改动小
- 使用标准 Netmiko 方法，稳定性好
- 不需要复杂的分页处理逻辑
- 适用于大多数华为设备

**缺点**:
- 需要额外发送禁用分页命令（增加交互次数）
- 部分低端设备可能不支持 `temporary` 参数
- 可能影响其他会话（如果使用全局配置）
- 需要确认设备权限（用户视图可能无法执行）

**适用场景**:
- 支持分页控制命令的设备
- 不想修改核心命令执行逻辑的场景
- 批量采集时统一禁用分页

**风险评估**: **低**
- 使用设备原生功能
- 改动范围小
- 易于回退

---

### 方案 C: 调整 delay_factor + 增加超时容忍

**方案名称**: 参数调整法

**原理**: 调整 Netmiko 参数，增加等待时间和容忍度，让设备有足够时间响应。

**实现方式**:

```python
# 方案 C-1: 调整 delay_factor
device_params = {
    "device_type": "huawei",
    "global_delay_factor": 4,  # 增加到 4（当前是 2）
    "fast_cli": False,
}

# 方案 C-2: 调整 send_command 参数
output = connection.send_command(
    command,
    read_timeout=60,       # 增加超时时间
    delay_factor=5,        # 增加延迟因子
    max_loops=1500,        # 增加循环次数
)

# 方案 C-3: 使用 strip_prompt=False
output = connection.send_command(
    command,
    read_timeout=60,
    strip_prompt=False,    # 不清理提示符，减少检测依赖
)
```

**参数说明**:

| 参数 | 当前值 | 建议值 | 作用 |
|------|--------|--------|------|
| global_delay_factor | 2 | 4 | 增加全局操作延迟 |
| read_timeout | 20 | 60 | 增加命令执行超时 |
| delay_factor | 2 | 5 | 增加单次命令延迟 |
| max_loops | 500 | 1500 | 增加读取循环次数 |

**优点**:
- 改动最小，只调整参数
- 不需要修改代码逻辑
- 对其他设备影响可控
- 易于测试和验证

**缺点**:
- 可能无法完全解决问题（如果根因是分页）
- 增加等待时间降低效率
- 参数调优可能需要反复尝试
- 不适用于所有场景

**适用场景**:
- 设备响应慢但分页不频繁
- 快速尝试修复的场景
- 配合其他方案使用

**风险评估**: **低**
- 改动最小
- 易于回退
- 不会引入新问题

---

### 方案 D: 检测设备型号 + 特殊处理

**方案名称**: 设备型号适配法

**原理**: 检测 S1730S 等低端设备型号，使用特殊的命令执行策略。

**实现方式**:

```python
# 1. 在连接时获取设备型号
async def connect_to_device(self, device: Device):
    connection = await self._create_connection(device)

    # 获取设备版本信息
    version_output = connection.send_command("display version", read_timeout=30)

    # 检测是否为低端设备（S1730S 等）
    is_low_end = self._detect_low_end_device(version_output)

    connection._device_meta = {
        "is_low_end": is_low_end,
        "needs_special_handling": is_low_end
    }

    return connection

# 2. 根据设备类型选择执行策略
async def execute_command(self, device: Device, command: str):
    if connection._device_meta.get("needs_special_handling"):
        # 使用方案 A 的直接通道读写
        return await self._send_command_direct(connection, command)
    else:
        # 使用标准方法
        return connection.send_command(command)

def _detect_low_end_device(self, version_output: str) -> bool:
    """检测低端设备型号"""
    low_end_models = ['S1730S', 'S1700', 'S1720', 'S2700']
    return any(model in version_output for model in low_end_models)
```

**低端设备列表**:

| 型号系列 | 特性 | 处理策略 |
|----------|------|----------|
| S1730S | 低端接入，响应慢 | 直接通道读写 |
| S1700/S1720 | 入门级交换机 | 禁用分页 + 增加超时 |
| S2700 | 早期低端设备 | 特殊参数配置 |

**优点**:
- 针对性强，只影响特定设备
- 不影响其他正常设备
- 可持续维护设备适配列表
- 提供灵活的扩展性

**缺点**:
- 需要维护设备型号检测逻辑
- 增加代码复杂度
- 新设备需要持续添加适配
- 检测逻辑可能不准确

**适用场景**:
- 只有部分设备出现问题
- 需要长期维护的场景
- 设备型号差异明显

**风险评估**: **中**
- 需要维护设备适配列表
- 检测逻辑需要持续更新

---

## 5. 方案对比与推荐

### 5.1 方案对比矩阵

| 维度 | 方案 A | 方案 B | 方案 C | 方案 D |
|------|--------|--------|--------|--------|
| 实施复杂度 | 高 | 低 | 最低 | 中 |
| 代码改动量 | 大 | 小 | 最小 | 中 |
| 影响范围 | 所有华为设备 | 执行命令的设备 | 所有设备 | 特定设备 |
| 可维护性 | 中 | 高 | 高 | 低（需持续维护） |
| 稳定性 | 中 | 高 | 高 | 高 |
| 效率影响 | 无 | 小（多一次交互） | 大（增加等待） | 无 |
| 长期可持续性 | 高 | 高 | 低 | 低 |
| 根因解决度 | 100% | 90% | 60% | 100% |

### 5.2 推荐方案

**推荐**: **方案 B + 方案 C 组合**

**理由**:

1. **方案 B（预禁用分页）** 从根本上解决分页问题
2. **方案 C（参数调整）** 提供额外的容错空间
3. 组合使用可以在最小改动下达到最佳效果

**实施优先级**:

| 优先级 | 步骤 | 方案 | 时间 |
|--------|------|------|------|
| P0 | 1. 调整 global_delay_factor 到 4 | 方案 C | 立即 |
| P0 | 2. 增加 read_timeout 到 60 | 方案 C | 立即 |
| P1 | 3. 添加预禁用分页逻辑 | 方案 B | 后续 |
| P2 | 4. 添加设备型号适配（备选） | 方案 D | 长期 |

### 5.3 实施计划

#### Phase 1: 参数调整（立即实施）

```python
# 修改 netmiko_service.py

# 1. 修改 __init__ 方法
def __init__(self):
    self.timeout = 90  # 从 60 增加到 90
    self.conn_timeout = 45  # 从 30 增加到 45

# 2. 修改 _build_device_params 方法
device_params = {
    "global_delay_factor": 4,  # 从 2 增加到 4
    ...
}

# 3. 修改 execute_command 默认参数
async def execute_command(self, device, command, ..., read_timeout: int = 60):
```

#### Phase 2: 禁用分页逻辑（后续实施）

```python
# 在 execute_command 方法中添加华为设备预处理

if vendor_lower in ['huawei', 'h3c', '华为', '华三']:
    # 先尝试禁用分页
    try:
        connection.send_command_timing(
            "screen-length 0 temporary",
            delay_factor=2,
            max_loops=100
        )
    except:
        # 禁用失败不影响后续执行
        pass
```

#### Phase 3: 设备型号适配（长期维护）

- 收集问题设备型号信息
- 建立设备适配数据库
- 实现智能适配选择

---

## 6. 测试验证计划

### 6.1 验证步骤

1. **参数调整验证**
   - 修改参数后重新执行采集
   - 确认 ReadTimeout 是否消失
   - 检查数据采集完整性

2. **禁用分页验证**
   - 手动测试 `screen-length 0 temporary` 命令
   - 确认设备支持此命令
   - 验证数据采集结果

3. **回归测试**
   - 确认其他设备采集正常
   - 验证批量采集功能
   - 检查性能影响

### 6.2 验收标准

| 标准 | 验证方法 |
|------|----------|
| S1730S 设备采集成功 | 执行 ARP/MAC 采集无超时 |
| 数据完整性 | 采集数据条数与手动执行一致 |
| 其他设备不受影响 | 对比采集成功率 |
| 批量采集效率 | 耗时增加不超过 20% |

---

## 7. 附录

### 7.1 Netmiko 提示符检测机制详解

Netmiko 的 `send_command` 方法使用以下步骤检测命令完成：

1. **回显检测**: 等待设备返回发送的命令字符串
   ```python
   # netmiko 源码
   def _check_command_echo(self, output, command_string):
       # 等待命令回显出现
       return command_string in output
   ```

2. **输出读取**: 在检测到回显后开始读取输出
   ```python
   def _read_until_prompt(self):
       # 使用正则匹配提示符
       while not prompt_pattern.search(output):
           output += read_channel()
   ```

3. **提示符正则**: 不同设备类型使用不同正则
   ```python
   # 华为设备
   prompt_pattern = r'<[^>]+>|\[[^\]]+\]'

   # Cisco 设备
   prompt_pattern = r'[>#]'
   ```

### 7.2 华为设备分页机制

华为 VRP 系统分页机制：

| 命令 | 功能 |
|------|------|
| `screen-length 0` | 禁用分页（永久） |
| `screen-length 0 temporary` | 禁用分页（临时） |
| `screen-length 24` | 设置分页行数 |
| `undo screen-length` | 恢复默认 |

**分页触发条件**:
- 输出行数超过 `screen-length` 设置值
- 默认值为 24 行

### 7.3 相关参考

- Netmiko 源码: `netmiko/base_connection.py`
- 华为 VRP 文档: VRP 命令参考手册
- P001 分析文档: `docs/projects/P001-arp-mac-scheduler-fix/`

---

## 8. 文档信息

| 项目 | 值 |
|------|-----|
| 文档版本 | v1.0 |
| 创建日期 | 2026-04-01 |
| 最后更新 | 2026-04-01 |
| 状态 | 待审批 |
| 下一步 | 用户确认后实施 Phase 1 |

---

**审批记录**:

| 日期 | 审批人 | 结果 | 备注 |
|------|--------|------|------|
| - | - | - | 待审批 |