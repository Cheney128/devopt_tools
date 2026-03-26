# IP 定位表结构优化方案 - N+1 查询根治

**版本**: 1.0  
**创建日期**: 2026-03-25  
**决策者**: 祥哥

---

## 一、现状分析

### 当前表结构

| 表名 | 记录数 | 用途 |
|------|--------|------|
| `arp_entries` | 3,047 | 历史 ARP 记录（全量） |
| `mac_addresses` | 15,601 | 历史 MAC 记录（全量） |
| `ip_location_current` | 5,519 | **当前定位结果**（预计算表，已存在） |
| `arp_current` | ? | 当前 ARP 快照 |
| `mac_current` | ? | 当前 MAC 快照 |
| `arp_history` | ? | 历史归档 |
| `mac_history` | ? | 历史归档 |

### 当前问题

`ip_location_current` 表**已存在**，但查询时仍在循环内逐条查 `mac_addresses` 和 `devices`：

```python
# locate_ip 方法 (ip_location_service.py:243-269)
for arp_entry in arp_entries:
    mac_entries = db.query(MACAddress).filter(...).all()  # N 次
    device = db.query(Device).filter(...).first()         # N 次
```

**根本原因**：`ip_location_current` 表字段不完整，缺少冗余的设备名、位置信息，导致查询时仍需 JOIN。

---

## 二、优化方案

### 2.1 表结构改造

#### 改造 `ip_location_current`（当前定位表）

**新增字段**（冗余设计，避免 JOIN）：

```sql
ALTER TABLE ip_location_current 
ADD COLUMN device_name VARCHAR(100) COMMENT '设备名称（冗余，避免 JOIN devices 表）' AFTER mac_hit_device_id,
ADD COLUMN device_ip VARCHAR(50) COMMENT '设备 IP 地址' AFTER device_name,
ADD COLUMN device_role VARCHAR(50) COMMENT '设备角色 (核心/汇聚/接入)' AFTER device_ip,
ADD COLUMN location VARCHAR(200) COMMENT '位置信息 (机房/楼层)' AFTER device_role,
ADD COLUMN is_offline TINYINT(1) DEFAULT 0 COMMENT '是否已下线' AFTER batch_status,
ADD COLUMN offline_time DATETIME NULL COMMENT '下线时间' AFTER is_offline,
ADD COLUMN offline_reason VARCHAR(50) NULL COMMENT '下线原因' AFTER offline_time,
ADD INDEX idx_device_name (device_name),
ADD INDEX idx_location (location),
ADD INDEX idx_offline (is_offline, offline_time);
```

#### 创建 `ip_location_history`（历史定位表）

```sql
CREATE TABLE ip_location_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL COMMENT 'IP 地址',
    mac_address VARCHAR(17) NOT NULL COMMENT 'MAC 地址',
    arp_source_device_id INT NOT NULL COMMENT 'ARP 来源设备 ID',
    arp_source_device_name VARCHAR(100) COMMENT 'ARP 来源设备名称',
    mac_hit_device_id INT COMMENT 'MAC 命中设备 ID',
    mac_hit_device_name VARCHAR(100) COMMENT 'MAC 命中设备名称',
    access_interface VARCHAR(100) COMMENT '接入接口',
    vlan_id INT COMMENT 'VLAN ID',
    confidence DECIMAL(5,2) DEFAULT 0.00 COMMENT '可信度',
    is_uplink TINYINT(1) DEFAULT 0 COMMENT '是否上联端口',
    is_core_switch TINYINT(1) DEFAULT 0 COMMENT '是否核心交换机',
    match_type VARCHAR(20) COMMENT '匹配类型',
    
    -- 下线信息
    offline_time DATETIME NOT NULL COMMENT '下线时间',
    offline_reason VARCHAR(50) COMMENT '下线原因 (heartbeat_timeout/manual_archive)',
    last_seen DATETIME NOT NULL COMMENT '最后可见时间',
    
    -- 批次信息
    calculate_batch_id VARCHAR(64) NOT NULL COMMENT '计算批次 ID',
    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '归档时间',
    archived_by VARCHAR(50) COMMENT '归档操作人',
    
    -- 冗余字段（便于查询）
    device_name VARCHAR(100) COMMENT '设备名称',
    device_ip VARCHAR(50) COMMENT '设备 IP',
    device_role VARCHAR(50) COMMENT '设备角色',
    location VARCHAR(200) COMMENT '位置信息',
    
    INDEX idx_ip_offline (ip_address, offline_time),
    INDEX idx_offline_time (offline_time),
    INDEX idx_batch (calculate_batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IP 定位历史表（下线归档）';
```

---

### 2.2 预计算触发机制

**定时任务**：每 10 分钟执行一次

```python
# 新增文件：app/services/ip_location_calculator.py
class IPLocationCalculator:
    """IP 定位预计算服务"""
    
    def calculate_batch(self) -> str:
        """
        批量计算所有 IP 的定位信息
        返回批次 ID
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 1. 批量预加载 ARP + MAC（2 次查询）
        arp_map = self._load_arp_entries()
        mac_map = self._load_mac_entries()
        device_map = self._load_devices()
        
        # 2. 内存 JOIN 计算（0 次查询）
        results = []
        for (ip, device_id), arp in arp_map.items():
            mac = mac_map.get((arp.mac_address, device_id))
            device = device_map.get(device_id)
            
            result = self._calculate_location(ip, arp, mac, device)
            results.append(result)
        
        # 3. 批量写入 ip_location_current（1 次 INSERT ... ON DUPLICATE KEY UPDATE）
        self._batch_upsert(results, batch_id)
        
        # 4. 检测下线 IP 并归档
        self._archive_offline_ips()
        
        return batch_id
```

**调度配置**（`app/services/latency_scheduler.py` 中新增）：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()

# 每 10 分钟执行一次 IP 定位预计算
scheduler.add_job(
    func=IPLocationCalculator().calculate_batch,
    trigger=IntervalTrigger(minutes=10),
    id='ip_location_calculate',
    replace_existing=True
)
```

---

### 2.3 IP 下线检测逻辑

```python
def _archive_offline_ips(self):
    """检测并归档下线 IP"""
    cutoff = datetime.now() - timedelta(minutes=30)  # 30 分钟无心跳视为下线
    
    # 1. 找出过期的 ARP 记录
    old_arp = self.db.query(ARPEntry).filter(
        ARPEntry.last_seen < cutoff
    ).all()
    
    offline_ips = set()
    for arp in old_arp:
        # 检查该 IP 是否有更新的 ARP 记录
        newer = self.db.query(ARPEntry).filter(
            ARPEntry.ip_address == arp.ip_address,
            ARPEntry.last_seen >= cutoff
        ).first()
        if not newer:
            offline_ips.add(arp.ip_address)
    
    # 2. 移动到历史表
    if offline_ips:
        current_records = self.db.query(IPLocationCurrent).filter(
            IPLocationCurrent.ip_address.in_(offline_ips),
            IPLocationCurrent.is_offline == 0
        ).all()
        
        for record in current_records:
            history = IPLocationHistory.from_current(record)
            history.offline_time = datetime.now()
            history.offline_reason = 'heartbeat_timeout'
            self.db.add(history)
            
            record.is_offline = 1
            record.offline_time = datetime.now()
        
        self.db.commit()
        logger.info(f"归档下线 IP: {len(offline_ips)} 个")
```

---

### 2.4 查询优化

#### 优化前（N+1）

```python
def locate_ip(self, ip_address: str) -> List[Dict]:
    arp_entries = self.db.query(ARPEntry).filter(...).all()  # 1 次
    
    results = []
    for arp in arp_entries:
        mac = self.db.query(MACAddress).filter(...).all()  # N 次
        device = self.db.query(Device).filter(...).first()  # N 次
        results.append(...)
    
    return results  # 总查询：1 + N×2
```

#### 优化后（O(1)）

```python
def locate_ip(self, ip_address: str) -> List[Dict]:
    # 直接查预计算表，零 JOIN
    results = self.db.query(IPLocationCurrent).filter(
        IPLocationCurrent.ip_address == ip_address,
        IPLocationCurrent.is_offline == 0
    ).all()  # 1 次查询
    
    return [r.to_dict() for r in results]  # 总查询：1
```

---

## 三、迁移计划

### 3.1 迁移脚本

**文件**: `scripts/migrate_ip_location_add_columns.py`

```python
"""
IP 定位表结构迁移 - 添加冗余字段
"""
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

def migrate():
    # 解析 DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    # ... 解析逻辑
    
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # 1. 添加新字段
        cursor.execute("""
            ALTER TABLE ip_location_current 
            ADD COLUMN device_name VARCHAR(100) ...
        """)
        # ... 其他字段
        
        # 2. 添加索引
        cursor.execute("CREATE INDEX idx_device_name ON ip_location_current(device_name)")
        # ... 其他索引
        
        # 3. 回填现有数据
        cursor.execute("""
            UPDATE ip_location_current cur
            JOIN devices d ON cur.mac_hit_device_id = d.id
            SET cur.device_name = d.name,
                cur.device_ip = d.ip_address,
                cur.device_role = d.role
        """)
        
        conn.commit()
        print("迁移完成")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
```

### 3.2 创建历史表

**文件**: `scripts/create_ip_location_history.py`

```python
"""
创建 IP 定位历史表
"""
# ... 类似上面的结构

CREATE_TABLE_SQL = """
CREATE TABLE ip_location_history (
    ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ...
"""

if __name__ == '__main__':
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("历史表创建完成")
```

### 3.3 迁移步骤

```bash
# 1. 备份当前数据库
mysqldump -h 10.21.65.20 -P 3307 -u root -p switch_manage > backup_20260325.sql

# 2. 执行迁移脚本
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
python scripts/migrate_ip_location_add_columns.py
python scripts/create_ip_location_history.py

# 3. 验证表结构
mysql -h 10.21.65.20 -P 3307 -u root -p -e "DESCRIBE switch_manage.ip_location_current"

# 4. 首次手动触发预计算
python -c "from app.services.ip_location_calculator import IPLocationCalculator; IPLocationCalculator(db).calculate_batch()"

# 5. 验证数据
mysql -h 10.21.65.20 -P 3307 -u root -p -e "SELECT COUNT(*) FROM switch_manage.ip_location_current WHERE device_name IS NOT NULL"

# 6. 重启应用（加载定时任务）
docker-compose restart app
```

---

## 四、回滚方案

如果迁移后出现问题，执行回滚：

```sql
-- 1. 删除新增字段
ALTER TABLE ip_location_current 
  DROP COLUMN device_name,
  DROP COLUMN device_ip,
  DROP COLUMN device_role,
  DROP COLUMN location,
  DROP COLUMN is_offline,
  DROP COLUMN offline_time,
  DROP COLUMN offline_reason;

-- 2. 删除索引
DROP INDEX idx_device_name ON ip_location_current;
DROP INDEX idx_location ON ip_location_current;
DROP INDEX idx_offline ON ip_location_current;

-- 3. 删除历史表（可选）
DROP TABLE IF EXISTS ip_location_history;

-- 4. 恢复代码（git 回退）
git checkout HEAD~1 -- app/services/ip_location_service.py
```

---

## 五、验证清单

### 迁移后验证

- [ ] `ip_location_current` 表新增字段存在
- [ ] 现有数据的 `device_name` 已回填
- [ ] `ip_location_history` 表创建成功
- [ ] 定时任务每 10 分钟执行
- [ ] 查询 `locate_ip` 返回结果包含设备名
- [ ] 下线 IP 被正确归档到历史表

### 性能对比

| 指标 | 迁移前 | 迁移后 | 改进 |
|------|--------|--------|------|
| `locate_ip` 查询延迟 | ~200ms (N+1) | ~10ms (O(1)) | **20x** |
| `get_ip_list` 查询延迟 | ~5000ms (N×2) | ~50ms (O(1)) | **100x** |
| 数据库查询次数/次请求 | 21 次 | 1 次 | **21x** |

---

## 六、后续优化

1. **缓存层**（可选）：引入 Redis 缓存热点 IP 查询
2. **分区表**：`ip_location_history` 按月分区
3. **监控告警**：预计算任务失败时通知

---

_此方案待祥哥确认后执行_
