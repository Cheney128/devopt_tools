# ARP/MAC 采集调度器工作流程分析报告

**分析日期**: 2026-03-30  
**分析对象**: switch_manage 项目 ARP/MAC 采集调度器  
**测试数据库**: 10.21.65.20:3307

---

## 1. 调度器启动流程

### 1.1 启动入口

调度器通过 `app/services/arp_mac_scheduler.py` 中的 `ARPMACScheduler` 类实现，启动流程如下：

```python
# 创建全局调度器实例（db 将在 start() 时传入）
arp_mac_scheduler = ARPMACScheduler(db=None, interval_minutes=30)

# 在应用启动时调用
def start(self, db: Session = None):
    if self._is_running:
        logger.warning("ARP/MAC 调度器已在运行中")
        return
    
    # 如果提供了新的 db，更新它
    if db:
        self.db = db
        self.netmiko = get_netmiko_service()
    
    # 添加定时任务
    self.scheduler.add_job(
        func=self._run_collection,
        trigger=IntervalTrigger(minutes=self.interval_minutes),
        id='arp_mac_collection',
        name='ARP/MAC 自动采集',
        replace_existing=True,
        misfire_grace_time=600  # 允许 10 分钟的错过执行宽限期
    )
    
    self.scheduler.start()
    self._is_running = True
    logger.info(f"ARP/MAC 调度器已启动，间隔：{self.interval_minutes} 分钟")
```

### 1.2 APScheduler 任务注册逻辑

| 参数 | 值 | 说明 |
|------|-----|------|
| `func` | `self._run_collection` | 定时任务回调函数 |
| `trigger` | `IntervalTrigger(minutes=30)` | 每 30 分钟触发一次 |
| `id` | `'arp_mac_collection'` | 任务唯一标识 |
| `name` | `'ARP/MAC 自动采集'` | 任务名称 |
| `replace_existing` | `True` | 覆盖已存在的同名任务 |
| `misfire_grace_time` | `600` | 允许 10 分钟的错过执行宽限期 |

### 1.3 定时任务触发机制

```
应用启动
    ↓
调用 arp_mac_scheduler.start(db)
    ↓
创建 BackgroundScheduler 实例
    ↓
注册定时任务 (每 30 分钟)
    ↓
启动调度器
    ↓
等待定时触发
```

**关键日志输出**:
```
[INFO] ARP/MAC 调度器已启动，间隔：30 分钟
```

---

## 2. 采集执行流程

### 2.1 定时任务回调 `_run_collection()`

```python
def _run_collection(self):
    """执行采集（定时任务回调）"""
    logger.info("开始执行 ARP/MAC 采集...")
    
    try:
        stats = self.collect_and_calculate()
        
        self._last_run = datetime.now()
        self._last_stats = stats
        
        # 更新失败计数
        collection = stats.get('collection', {})
        arp_success = collection.get('arp_success', 0)
        arp_failed = collection.get('arp_failed', 0)
        
        if arp_success == 0 and arp_failed > 0:
            self._consecutive_failures += 1
            logger.warning(f"ARP/MAC 采集失败，连续失败次数：{self._consecutive_failures}")
        else:
            if self._consecutive_failures > 0:
                logger.info(f"ARP/MAC 采集恢复，之前连续失败 {self._consecutive_failures} 次")
            self._consecutive_failures = 0
        
        logger.info(f"ARP/MAC 采集完成：成功 {arp_success} 台，失败 {arp_failed} 台")
        
    except Exception as e:
        logger.error(f"ARP/MAC 采集异常：{e}", exc_info=True)
        self._consecutive_failures += 1
```

### 2.2 采集 + 计算流程 `collect_and_calculate()`

```python
def collect_and_calculate(self) -> dict:
    """采集 ARP+MAC 并触发 IP 定位计算"""
    logger.info("开始采集 + 计算流程")

    # 步骤 1: 采集 ARP 和 MAC
    collection_stats = self.collect_all_devices()

    if collection_stats.get('arp_success', 0) == 0:
        logger.error("ARP 采集全部失败，跳过 IP 定位计算")
        return {
            'collection': collection_stats,
            'calculation': {'error': 'ARP collection failed'}
        }

    # 步骤 2: 触发 IP 定位计算
    try:
        calculator = get_ip_location_calculator(self.db)
        calculation_stats = calculator.calculate_batch()
        
        logger.info(f"IP 定位计算完成：{calculation_stats}")
        
        return {
            'collection': collection_stats,
            'calculation': calculation_stats
        }
    except Exception as e:
        logger.error(f"IP 定位计算失败：{str(e)}")
        return {
            'collection': collection_stats,
            'calculation': {'error': str(e)}
        }
```

### 2.3 批量采集 `collect_all_devices()`

```python
def collect_all_devices(self) -> dict:
    """采集所有活跃设备的 ARP 和 MAC 表"""
    start_time = datetime.now()
    logger.info(f"开始批量采集 ARP 和 MAC 表，时间：{start_time}")

    # 获取所有活跃设备
    devices = self.db.query(Device).filter(
        Device.status == 'active'
    ).all()

    if not devices:
        logger.warning("没有活跃设备需要采集")
        return {'success': 0, 'failed': 0, 'error': 'No active devices'}

    logger.info(f"共有 {len(devices)} 台设备需要采集")

    # 采集统计
    stats = {
        'arp_success': 0,
        'arp_failed': 0,
        'mac_success': 0,
        'mac_failed': 0,
        'total_arp_entries': 0,
        'total_mac_entries': 0,
        'devices': []
    }

    # 逐个设备采集
    for device in devices:
        device_stats = self._collect_device(device)
        stats['devices'].append(device_stats)
        
        if device_stats['arp_success']:
            stats['arp_success'] += 1
            stats['total_arp_entries'] += device_stats.get('arp_entries_count', 0)
        else:
            stats['arp_failed'] += 1
        
        if device_stats['mac_success']:
            stats['mac_success'] += 1
            stats['total_mac_entries'] += device_stats.get('mac_entries_count', 0)
        else:
            stats['mac_failed'] += 1

    # 记录总耗时
    end_time = datetime.now()
    stats['start_time'] = start_time.isoformat()
    stats['end_time'] = end_time.isoformat()
    stats['duration_seconds'] = (end_time - start_time).total_seconds()

    logger.info(f"批量采集完成：{stats}")
    return stats
```

### 2.4 单设备采集 `_collect_device()`

```python
def _collect_device(self, device: Device) -> dict:
    """采集单个设备的 ARP 和 MAC 表"""
    device_stats = {
        'device_id': device.id,
        'device_hostname': device.hostname,
        'arp_success': False,
        'mac_success': False,
        'arp_entries_count': 0,
        'mac_entries_count': 0,
    }

    try:
        # 采集 ARP 表
        arp_table = self.netmiko.collect_arp_table(device)
        if arp_table:
            # 清空并保存
            self.db.query(ARPEntry).filter(
                ARPEntry.device_id == device.id
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

        # 采集 MAC 表
        mac_table = self.netmiko.collect_mac_table(device)
        if mac_table:
            # 清空并保存
            self.db.query(MACAddressCurrent).filter(
                MACAddressCurrent.device_id == device.id
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
        logger.error(f"设备 {device.hostname} 采集失败：{str(e)}")
        self.db.rollback()
        device_stats['error'] = str(e)

    return device_stats
```

### 2.5 Netmiko 服务调用

#### ARP 表采集

```python
# netmiko_service.py
async def collect_arp_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    """采集设备 ARP 表"""
    if not device.username or not device.password:
        print(f"Device {device.hostname} missing credentials")
        return None

    # 根据设备厂商选择命令
    if device.vendor == "huawei":
        command = "display arp"
    elif device.vendor == "h3c":
        command = "display arp"
    elif device.vendor == "cisco":
        command = "show ip arp"
    else:
        command = "display arp"  # 默认使用华为命令
    
    output = await self.execute_command(device, command)
    if not output:
        return None

    # 解析 ARP 表
    arp_entries = self._parse_arp_table(output, device.vendor)
    
    # 添加 device_id 到每个 ARP 条目
    for arp_entry in arp_entries:
        arp_entry["device_id"] = device.id

    return arp_entries if arp_entries else None
```

#### MAC 表采集

```python
# netmiko_service.py
async def collect_mac_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
    """采集设备 MAC 地址表"""
    if not device.username or not device.password:
        print(f"Device {device.hostname} missing credentials")
        return None

    mac_command = self.get_commands(device.vendor, "mac_table")
    if not mac_command:
        return None

    output = await self.execute_command(device, mac_command)
    if not output:
        return None

    mac_table = self.parse_mac_table(output, device.vendor)

    # 添加 device_id 到每个 MAC 条目
    for mac_entry in mac_table:
        mac_entry["device_id"] = device.id

    return mac_table if mac_table else None
```

---

## 3. 数据流分析

### 3.1 完整数据流图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         调度器启动                                       │
│  arp_mac_scheduler.start(db)                                           │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      APScheduler 定时任务                                │
│  每 30 分钟触发 _run_collection()                                         │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    调用 collect_and_calculate()                         │
│  1. 采集 ARP 和 MAC                                                        │
│  2. 触发 IP 定位计算                                                       │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    调用 collect_all_devices()                           │
│  1. 查询所有 status='active' 的设备                                        │
│  2. 逐个设备调用 _collect_device()                                       │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   _collect_device(device)                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  步骤 1: 调用 netmiko.collect_arp_table(device)                   │   │
│  │    → SSH 连接设备                                                  │   │
│  │    → 执行 "display arp" 或 "show ip arp"                          │   │
│  │    → 解析输出为结构化数据                                          │   │
│  │    → 清空 arp_current 表中该设备的旧数据                           │   │
│  │    → 插入新的 ARP 记录（带 collection_batch_id）                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  步骤 2: 调用 netmiko.collect_mac_table(device)                   │   │
│  │    → SSH 连接设备                                                  │
│  │    → 执行 "display mac-address" 或 "show mac address-table"      │   │
│  │    → 解析输出为结构化数据                                          │   │
│  │    → 清空 mac_current 表中该设备的旧数据                           │   │
│  │    → 插入新的 MAC 记录                                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  步骤 3: 提交事务 db.commit()                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    调用 get_ip_location_calculator()                    │
│  读取 arp_current 和 mac_current 表                                      │
│  执行 IP 定位计算                                                         │
│  写入 ip_location_current 表                                             │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         数据库表                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  arp_current     │  │  mac_current     │  │  ip_location_current │ │
│  │  - id            │  │  - id            │  │  - id                │ │
│  │  - ip_address    │  │  - mac_address   │  │  - ip_address        │ │
│  │  - mac_address   │  │  - mac_device_id │  │  - mac_address       │ │
│  │  - arp_device_id │  │  - mac_interface │  │  - location_device   │ │
│  │  - vlan_id       │  │  - vlan_id       │  │  - location_interface│ │
│  │  - arp_interface │  │  - is_trunk      │  │  - confidence        │ │
│  │  - last_seen     │  │  - last_seen     │  │  - batch_id          │ │
│  │  - collection_   │  │  - collection_   │  │  - calculated_at     │ │
│  │    batch_id      │  │    batch_id      │  │                      │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 时序图

```
调度器          数据库          Netmiko 服务        设备
  │              │                 │              │
  │─start()─────>│                 │              │
  │              │                 │              │
  │◄─调度器启动───│                 │              │
  │              │                 │              │
  │ [等待 30 分钟]  │                 │              │
  │              │                 │              │
  │─_run_collection()              │              │
  │              │                 │              │
  │─collect_all_devices()          │              │
  │              │                 │              │
  │─query(Device)─>                │              │
  │◄─设备列表─────│                 │              │
  │              │                 │              │
  │─_collect_device(device1)       │              │
  │              │                 │              │
  │              │─collect_arp_table()─>          │
  │              │                 │─SSH 连接────>│
  │              │                 │<─连接成功────│
  │              │                 │─display arp─>│
  │              │                 │<─ARP 输出────│
  │              │                 │─解析 ARP────>│
  │              │                 │              │
  │              │<─DELETE arp_current            │
  │              │─INSERT arp_current            │
  │              │                 │              │
  │              │─collect_mac_table()─>          │
  │              │                 │─display mac-address─>│
  │              │                 │<─MAC 输出────│
  │              │                 │─解析 MAC────>│
  │              │                 │              │
  │              │<─DELETE mac_current            │
  │              │─INSERT mac_current            │
  │              │                 │              │
  │              │─commit()──────>│              │
  │              │                 │              │
  │◄─采集完成─────│                 │              │
  │              │                 │              │
  │─calculate_batch()              │              │
  │              │                 │              │
  │─SELECT arp_current, mac_current              │
  │◄─ARP/MAC 数据──│                 │              │
  │              │                 │              │
  │─INSERT ip_location_current                   │
  │              │                 │              │
  │◄─计算完成─────│                 │              │
  │              │                 │              │
```

---

## 4. 数据库表结构说明

### 4.1 arp_current 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | Integer | Primary Key | 自增 ID |
| `ip_address` | String(50) | Not Null, Index | IP 地址 |
| `mac_address` | String(17) | Not Null | MAC 地址 |
| `arp_device_id` | Integer | Not Null | ARP 来源设备 ID |
| `vlan_id` | Integer | Nullable | VLAN ID |
| `arp_interface` | String(100) | Nullable | ARP 接口 |
| `source_type` | String(20) | Nullable | 来源类型 |
| `last_seen` | DateTime | Not Null, Index | 最后发现时间 |
| `collection_batch_id` | String(64) | Not Null, Index | 采集批次 ID |
| `created_at` | DateTime | Not Null | 创建时间 |
| `updated_at` | DateTime | Not Null | 更新时间 |

**索引**:
- `idx_ip_mac`: (ip_address, mac_address) 复合索引

### 4.2 mac_current 表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | Integer | Primary Key | 自增 ID |
| `mac_address` | String(17) | Not Null, Index | MAC 地址 |
| `mac_device_id` | Integer | Not Null, Index | MAC 来源设备 ID |
| `mac_interface` | String(100) | Not Null | MAC 接口 |
| `vlan_id` | Integer | Nullable | VLAN ID |
| `is_trunk` | Boolean | Nullable | 是否 Trunk 接口 |
| `interface_description` | String(255) | Nullable | 接口描述 |
| `source_type` | String(20) | Nullable | 来源类型 |
| `last_seen` | DateTime | Not Null, Index | 最后发现时间 |
| `collection_batch_id` | String(64) | Nullable | 采集批次 ID |
| `created_at` | DateTime | Not Null | 创建时间 |
| `updated_at` | DateTime | Not Null | 更新时间 |

### 4.3 devices 表（参考）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | Integer | Primary Key | 设备 ID |
| `hostname` | String(255) | Not Null, Index | 设备主机名 |
| `ip_address` | String(50) | Unique, Not Null | 设备管理 IP |
| `vendor` | String(50) | Not Null | 厂商 (huawei/cisco/h3c/ruijie) |
| `model` | String(100) | Not Null | 设备型号 |
| `status` | String(20) | Not Null | 状态 (active/inactive) |
| `login_port` | Integer | Not Null | SSH 端口 |
| `username` | String(100) | Nullable | 登录用户名 |
| `password` | String(255) | Nullable | 登录密码 |

---

## 5. 日志输出说明

### 5.1 调度器启动日志

```
[INFO] ARP/MAC 调度器已启动，间隔：30 分钟
```

### 5.2 采集开始日志

```
[INFO] 开始执行 ARP/MAC 采集...
[INFO] 开始采集 + 计算流程
[INFO] 开始批量采集 ARP 和 MAC 表，时间：2026-03-30T10:00:00
[INFO] 共有 5 台设备需要采集
```

### 5.3 单设备采集日志

**成功场景**:
```
[INFO] 设备 SW-Core-01 ARP 采集成功：150 条
[INFO] 设备 SW-Core-01 MAC 采集成功：320 条
```

**空结果场景**:
```
[WARNING] 设备 SW-Access-01 ARP 采集返回空结果
[WARNING] 设备 SW-Access-01 MAC 采集返回空结果
```

**失败场景**:
```
[ERROR] 设备 SW-Access-02 采集失败：Connection timeout
```

### 5.4 采集完成日志

```
[INFO] 批量采集完成：{'arp_success': 4, 'arp_failed': 1, 'mac_success': 4, 'mac_failed': 1, 'total_arp_entries': 600, 'total_mac_entries': 1280, 'start_time': '2026-03-30T10:00:00', 'end_time': '2026-03-30T10:05:30', 'duration_seconds': 330.5}
[INFO] ARP/MAC 采集完成：成功 4 台，失败 1 台
```

### 5.5 IP 定位计算日志

```
[INFO] IP 定位计算完成：{'total_ips': 600, 'located': 580, 'unlocated': 20, 'duration_seconds': 15.2}
```

### 5.6 失败场景日志

**连续失败**:
```
[WARNING] ARP/MAC 采集失败，连续失败次数：1
[WARNING] ARP/MAC 采集失败，连续失败次数：2
[WARNING] ARP/MAC 采集失败，连续失败次数：3
```

**采集恢复**:
```
[INFO] ARP/MAC 采集恢复，之前连续失败 3 次
```

**异常场景**:
```
[ERROR] ARP/MAC 采集异常：Database connection lost
Traceback (most recent call last):
  ...
```

### 5.7 通过日志判断采集是否正常

| 日志模式 | 判断 |
|----------|------|
| `ARP 采集成功：X 条` + `MAC 采集成功：Y 条` | ✅ 正常 |
| `采集返回空结果` | ⚠️ 设备可能无 ARP/MAC 表 |
| `采集失败：XXX` | ❌ 采集失败，需检查网络/凭据 |
| `连续失败次数：3` | 🔴 健康状态降级 |
| `批量采集完成：{'arp_success': 0, ...}` | 🔴 全部失败，IP 定位计算跳过 |

---

## 6. 与架构设计文档的对照

### 6.1 架构设计要求（docs/功能需求/ip-location-ver3/整体架构设计.md）

| 要求项 | 架构设计描述 | 实际实现 | 一致性 |
|--------|-------------|---------|--------|
| **采集组件** | 复用现有 ARP/MAC 采集器，采集完成后写当前表并追加历史表 | ✅ 实现了采集当前表 (arp_current/mac_current)，**未实现历史表** | ⚠️ 部分一致 |
| **采集批次号** | 生成采集批次号 (collection_batch_id) | ✅ 已实现，格式：`batch_YYYYMMDDHHMMSS_uuid` | ✅ 一致 |
| **计算组件** | 采集完成后触发增量计算 | ✅ `collect_and_calculate()` 在采集后调用 `calculate_batch()` | ✅ 一致 |
| **定时兜底** | 定时任务每日执行一次全量重建 | ⚠️ 仅支持固定间隔 (30 分钟)，**无每日全量重建机制** | ⚠️ 部分一致 |
| **双机制触发** | 采集触发 + 定时兜底 | ⚠️ 仅实现定时触发，**采集完成触发未实现** | ⚠️ 部分一致 |
| **事务保护** | 同一批次写入采用事务控制 | ✅ 使用 `db.commit()` 和 `db.rollback()` | ✅ 一致 |
| **失败回滚** | 失败回滚到上一个有效批次 | ⚠️ 实现了 `db.rollback()`，**但无批次版本管理** | ⚠️ 部分一致 |
| **健康状态** | 记录完整执行日志 | ✅ 实现了 `consecutive_failures` 和 `health_status` | ✅ 一致 |

### 6.2 数据分层对照

| 数据层 | 架构设计 | 实际实现 | 状态 |
|--------|---------|---------|------|
| 当前 ARP 表 | `arp_current` | ✅ `app/models/ip_location_current.py:ARPEntry` | ✅ 已实现 |
| 历史 ARP 表 | `arp_history` | ❌ 未实现 | ❌ 缺失 |
| 当前 MAC 表 | `mac_current` | ✅ `app/models/ip_location_current.py:MACAddressCurrent` | ✅ 已实现 |
| 历史 MAC 表 | `mac_history` | ❌ 未实现 | ❌ 缺失 |
| 当前 IP 定位表 | `ip_location_current` | ✅ (通过 `get_ip_location_calculator()` 调用) | ✅ 已实现 |

### 6.3 差距分析

#### 已实现功能 ✅
1. 定时采集调度器（30 分钟间隔）
2. 批量采集所有活跃设备
3. 采集数据写入当前表（arp_current/mac_current）
4. 采集批次号生成
5. 采集后触发 IP 定位计算
6. 事务保护（commit/rollback）
7. 健康状态监控（连续失败计数）

#### 缺失功能 ❌
1. **历史表支持**：缺少 `arp_history` 和 `mac_history` 表，无法进行审计和回放
2. **每日全量重建**：缺少定时全量计算机制，仅支持固定间隔采集触发
3. **采集触发计算**：架构设计提到"采集任务结束后触发增量计算"，但当前实现仅支持定时触发
4. **批次版本管理**：缺少批次版本号，无法实现"原子替换当前有效版本"和"回滚到上一个有效批次"

#### 建议改进 🔧
1. 添加历史表模型和写入逻辑
2. 增加每日全量计算定时任务
3. 实现批次版本管理（version 字段）
4. 增加采集完成事件触发机制

---

## 7. 关键代码片段及说明

### 7.1 调度器初始化

```python
# app/services/arp_mac_scheduler.py
class ARPMACScheduler:
    def __init__(self, db: Optional[Session] = None, interval_minutes: int = 30):
        self.db = db
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self._is_running = False
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None
        self._consecutive_failures: int = 0
        self.netmiko = get_netmiko_service() if db else None
```

**说明**:
- 支持可选的数据库会话参数
- 默认采集间隔 30 分钟
- 使用 APScheduler 的 BackgroundScheduler
- 维护运行状态和失败计数

### 7.2 批次 ID 生成

```python
collection_batch_id=f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
```

**说明**:
- 格式：`batch_YYYYMMDDHHMMSS_XXXXXXXX`
- 时间戳精确到秒
- UUID 前 8 位保证唯一性
- 示例：`batch_20260330100000_a1b2c3d4`

### 7.3 事务保护

```python
try:
    # 采集 ARP 表
    arp_table = self.netmiko.collect_arp_table(device)
    if arp_table:
        # 清空并保存
        self.db.query(ARPEntry).filter(
            ARPEntry.device_id == device.id
        ).delete()
        
        for entry in arp_table:
            arp_entry = ARPEntry(...)
            self.db.add(arp_entry)
    
    # 采集 MAC 表
    mac_table = self.netmiko.collect_mac_table(device)
    if mac_table:
        # 清空并保存
        self.db.query(MACAddressCurrent).filter(
            MACAddressCurrent.device_id == device.id
        ).delete()
        
        for entry in mac_table:
            mac_entry = MACAddressCurrent(...)
            self.db.add(mac_entry)
    
    # 提交事务
    self.db.commit()

except Exception as e:
    logger.error(f"设备 {device.hostname} 采集失败：{str(e)}")
    self.db.rollback()
    device_stats['error'] = str(e)
```

**说明**:
- 单个设备采集在一个事务内完成
- ARP 和 MAC 采集要么都成功，要么都回滚
- 异常时回滚避免脏数据

### 7.4 健康状态计算

```python
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

**健康状态定义**:
- `healthy`: 正常运行，无失败或失败后已恢复
- `degraded`: 有 1-2 次连续失败
- `unhealthy`: 调度器未运行或连续失败≥3 次

---

## 8. 总结

### 8.1 工作流程总结

```
调度器启动
    ↓
APScheduler 注册定时任务（30 分钟）
    ↓
定时触发 _run_collection()
    ↓
调用 collect_and_calculate()
    ├─→ collect_all_devices()
    │   ├─→ 查询所有 active 设备
    │   └─→ 逐个调用 _collect_device()
    │       ├─→ netmiko.collect_arp_table()
    │       │   ├─→ SSH 连接设备
    │       │   ├─→ 执行 display arp / show ip arp
    │       │   ├─→ 解析 ARP 表
    │       │   └─→ 清空并插入 arp_current
    │       └─→ netmiko.collect_mac_table()
    │           ├─→ SSH 连接设备
    │           ├─→ 执行 display mac-address / show mac address-table
    │           ├─→ 解析 MAC 表
    │           └─→ 清空并插入 mac_current
    └─→ get_ip_location_calculator().calculate_batch()
        ├─→ 读取 arp_current 和 mac_current
        ├─→ 执行 IP 定位计算
        └─→ 写入 ip_location_current
    ↓
记录采集统计和健康状态
```

### 8.2 验证方法

#### 方法 1: 查看调度器状态
```python
from app.services.arp_mac_scheduler import arp_mac_scheduler

status = arp_mac_scheduler.get_status()
print(status)
# 输出:
# {
#   'scheduler': 'arp_mac',
#   'is_running': True,
#   'interval_minutes': 30,
#   'last_run': '2026-03-30T10:00:00',
#   'next_run': '2026-03-30T10:30:00',
#   'consecutive_failures': 0,
#   'health_status': 'healthy'
# }
```

#### 方法 2: 查询数据库
```sql
-- 查看最新采集批次
SELECT collection_batch_id, COUNT(*) as arp_count, MAX(last_seen) as last_seen
FROM arp_current
GROUP BY collection_batch_id
ORDER BY last_seen DESC
LIMIT 5;

-- 查看设备采集情况
SELECT 
    d.hostname,
    COUNT(DISTINCT a.id) as arp_entries,
    COUNT(DISTINCT m.id) as mac_entries,
    MAX(a.last_seen) as last_arp_seen,
    MAX(m.last_seen) as last_mac_seen
FROM devices d
LEFT JOIN arp_current a ON d.id = a.arp_device_id
LEFT JOIN mac_current m ON d.id = m.mac_device_id
WHERE d.status = 'active'
GROUP BY d.id, d.hostname;
```

#### 方法 3: 查看应用日志
```bash
# 实时查看采集日志
tail -f logs/app.log | grep -E "ARP|MAC|采集"

# 查看最近一次采集
grep "批量采集完成" logs/app.log | tail -1
```

### 8.3 风险点

| 风险点 | 影响 | 缓解措施 |
|--------|------|----------|
| 单设备采集失败导致整个事务回滚 | 该设备 ARP 和 MAC 数据都丢失 | 已实现，符合预期 |
| 无历史表支持 | 无法审计和回放历史数据 | 建议后续迭代添加 |
| 无每日全量重建 | 长期运行可能积累数据漂移 | 建议添加每日定时全量计算 |
| 无批次版本管理 | 无法实现原子切换和回滚 | 建议添加 version 字段 |
| 采集间隔固定 30 分钟 | 无法根据网络规模动态调整 | 已支持通过参数配置 |

---

**报告生成时间**: 2026-03-30 13:10 GMT+8  
**分析工具**: Superpowers systematic-debugging  
**项目路径**: `/mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage/`
