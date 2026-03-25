# IP 定位预计算优化实施计划

> 创建日期：2026-03-25
> 分支：feature/ip-location-optimization
> 目标：根治 N+1 查询问题，将查询从 O(N) 优化到 O(1)

---

## 1. 需求分析

### 1.1 现状

数据库中已存在以下表：
- `arp_current` - ARP 表数据（IP → MAC 映射）
- `mac_current` - MAC 地址表数据（MAC → 接口映射）
- `ip_location_current` - IP 定位结果（5,519 条记录）
- `devices` - 设备信息表

### 1.2 问题

`ip_location_current` 表缺少冗余设备信息：
- 查询 IP 列表时需要循环查询 `devices` 表获取设备名称、位置等
- 导致 N+1 查询问题：1 次主查询 + N 次关联查询

### 1.3 解决方案

通过预计算 + 冗余字段：
1. 在 `ip_location_current` 添加冗余设备字段
2. 定时任务（每 10 分钟）预计算并更新
3. 查询时直接读取冗余字段，无需关联查询

---

## 2. 数据库变更

### 2.1 添加冗余字段到 ip_location_current

```sql
-- 添加 ARP 来源设备冗余字段
ALTER TABLE ip_location_current
ADD COLUMN arp_device_hostname VARCHAR(255) COMMENT 'ARP来源设备主机名' AFTER arp_source_device_id,
ADD COLUMN arp_device_ip VARCHAR(50) COMMENT 'ARP来源设备IP' AFTER arp_device_hostname,
ADD COLUMN arp_device_location VARCHAR(255) COMMENT 'ARP来源设备位置' AFTER arp_device_ip;

-- 添加 MAC 命中设备冗余字段
ALTER TABLE ip_location_current
ADD COLUMN mac_device_hostname VARCHAR(255) COMMENT 'MAC命中设备主机名' AFTER mac_hit_device_id,
ADD COLUMN mac_device_ip VARCHAR(50) COMMENT 'MAC命中设备IP' AFTER mac_device_hostname,
ADD COLUMN mac_device_location VARCHAR(255) COMMENT 'MAC命中设备位置' AFTER mac_device_ip;

-- 添加索引优化查询
CREATE INDEX idx_ip_location_status ON ip_location_current(batch_status);
CREATE INDEX idx_ip_location_last_seen ON ip_location_current(last_seen);
```

### 2.2 创建历史表 ip_location_history

```sql
CREATE TABLE ip_location_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL,
    mac_address VARCHAR(17) NOT NULL,

    -- ARP 来源设备信息
    arp_source_device_id INT,
    arp_device_hostname VARCHAR(255),
    arp_device_ip VARCHAR(50),
    arp_device_location VARCHAR(255),

    -- MAC 命中设备信息
    mac_hit_device_id INT,
    mac_device_hostname VARCHAR(255),
    mac_device_ip VARCHAR(50),
    mac_device_location VARCHAR(255),

    -- 定位信息
    access_interface VARCHAR(100),
    vlan_id INT,
    confidence DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    is_uplink TINYINT(1) NOT NULL DEFAULT 0,
    is_core_switch TINYINT(1) NOT NULL DEFAULT 0,
    match_type VARCHAR(20) NOT NULL,

    -- 时间信息
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    archived_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_history_ip (ip_address),
    INDEX idx_history_mac (mac_address),
    INDEX idx_history_archived (archived_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IP定位历史表（保留30天）';
```

---

## 3. 文件清单

### 3.1 新建文件

| 文件路径 | 说明 |
|---------|------|
| `scripts/migrate_ip_location_add_columns.py` | 迁移脚本：添加冗余字段 |
| `scripts/create_ip_location_history.py` | 迁移脚本：创建历史表 |
| `app/models/ip_location.py` | ORM 模型定义 |
| `app/services/ip_location_calculator.py` | 预计算服务类 |
| `app/api/endpoints/ip_location.py` | API 端点（可选） |
| `tests/unit/test_ip_location_calculator.py` | 单元测试 |

### 3.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `app/models/__init__.py` | 导出新模型 |
| `app/services/backup_scheduler.py` | 添加 IP 定位定时任务 |
| `app/main.py` | 启动时初始化调度器 |

---

## 4. 实施步骤

### Step 1: 数据库迁移（约 10 分钟）

```bash
# 执行迁移脚本
python scripts/migrate_ip_location_add_columns.py
python scripts/create_ip_location_history.py
```

### Step 2: 创建 ORM 模型

```python
# app/models/ip_location.py
```

### Step 3: 实现预计算服务

核心方法：
- `_load_arp_entries()` - 批量加载 ARP 数据
- `_load_mac_entries()` - 批量加载 MAC 数据
- `_load_devices()` - 批量加载设备信息
- `calculate_batch()` - 主计算逻辑
- `_archive_offline_ips()` - 下线检测归档

### Step 4: 集成定时任务

```python
# 在 backup_scheduler.py 中添加
scheduler.add_job(
    func=ip_location_calculator.calculate_batch,
    trigger='interval',
    minutes=10,
    id='ip_location_calculation'
)
```

### Step 5: 测试验证

```bash
# 运行单元测试
pytest tests/unit/test_ip_location_calculator.py -v

# 手动触发一次预计算
python -c "from app.services.ip_location_calculator import IPLocationCalculator; IPLocationCalculator().calculate_batch()"
```

---

## 5. 验证标准

1. **表结构验证**
   - `ip_location_current` 包含 6 个新增冗余字段
   - `ip_location_history` 表已创建

2. **数据正确性验证**
   - 冗余字段数据与 `devices` 表一致
   - 预计算结果准确

3. **性能验证**
   - 查询 IP 列表不再触发 N+1 查询
   - 单次查询时间 < 100ms（1000 条记录）

4. **定时任务验证**
   - 每 10 分钟自动执行
   - 失败时记录错误日志

---

## 6. 回滚方案

```sql
-- 删除新增字段
ALTER TABLE ip_location_current
DROP COLUMN arp_device_hostname,
DROP COLUMN arp_device_ip,
DROP COLUMN arp_device_location,
DROP COLUMN mac_device_hostname,
DROP COLUMN mac_device_ip,
DROP COLUMN mac_device_location;

-- 删除历史表
DROP TABLE IF EXISTS ip_location_history;
```

---

## 7. 时间估计

| 阶段 | 预计时间 |
|-----|---------|
| 数据库迁移 | 10 分钟 |
| ORM 模型 | 15 分钟 |
| 预计算服务 | 30 分钟 |
| 定时任务集成 | 15 分钟 |
| 测试编写 | 20 分钟 |
| 验证测试 | 10 分钟 |
| **总计** | **1.5 小时** |