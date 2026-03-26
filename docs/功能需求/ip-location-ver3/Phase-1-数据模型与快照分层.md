# Phase-1-数据模型与快照分层

## 1. 目标

建立 Ver3 的数据承载基础，完成“当前表 + 历史表 + 定位快照表”模型定义与迁移方案，保证后续计算与查询有稳定输入输出。

## 2. 设计范围

- 新增或扩展数据表：
  - `arp_current`
  - `arp_history`
  - `mac_current`
  - `mac_history`
  - `ip_location_current`
- 统一字段规范：
  - `collection_batch_id`
  - `calculate_batch_id`
  - `last_seen`
  - `calculated_at`
  - `source_type`

## 3. 关键字段建议

### 3.1 当前ARP表
- `ip_address`
- `mac_address`
- `arp_device_id`
- `vlan_id`
- `arp_interface`
- `last_seen`
- `collection_batch_id`

唯一约束建议：`(ip_address, arp_device_id)`

### 3.2 当前MAC表
- `mac_address`
- `mac_device_id`
- `mac_interface`
- `vlan_id`
- `is_trunk`
- `interface_description`
- `last_seen`
- `collection_batch_id`

索引建议：`(mac_address, last_seen desc)`

### 3.3 当前IP定位表
- `ip_address`
- `mac_address`
- `arp_source_device_id`
- `mac_hit_device_id`
- `access_interface`
- `vlan_id`
- `confidence`
- `is_uplink`
- `is_core_switch`
- `match_type`
- `last_seen`
- `calculated_at`
- `calculate_batch_id`

唯一约束建议：`(ip_address, calculate_batch_id, mac_hit_device_id, access_interface)`

## 4. 历史归档策略

- 每次采集后，将原当前表快照复制到历史表（带批次号）
- 历史表按保留周期清理
- 历史表不可作为前端在线查询主路径

## 5. 迁移策略

- 迁移脚本分两段：
  1. 建表与索引
  2. 初始化配置与兼容视图
- 迁移接入应用启动自动执行链路，由迁移管理器统一调度
- 本期迁移数据库限定为 MySQL（`mysql+pymysql`）
- 首次上线允许“空快照”启动，待首次计算后生效
- 回滚策略：仅回滚新表与相关索引，不影响旧定位能力

## 6. 验收标准

- 所有新表建表成功，索引与约束生效
- 迁移可重复执行且幂等
- 当前/历史写入链路通过单元测试
