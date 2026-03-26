# Phase-2-定位计算引擎

## 1. 目标

实现离线定位计算引擎，基于 `arp_current + mac_current` 产出 `ip_location_current`，替代查询时实时重关联。

## 2. 计算流程

### Step 1：读取输入
- 读取当前ARP表全部有效记录
- 读取当前MAC表并按 `mac_address` 建立候选映射

### Step 2：构建候选
- 对每条ARP按MAC查找候选接口
- 支持三类命中：
  - `same_device`
  - `cross_device`
  - `arp_only`

### Step 3：候选打分
- 接口类型分：接入口高于上联口
- 数据完整性分：ARP+MAC > ARP-only
- 时间新鲜度分：近时间优先
- VLAN一致性分：一致加分

### Step 4：写入快照
- 同一IP保留TopN候选（建议N=3）
- 结果落表到 `ip_location_current`
- 写入 `calculate_batch_id` 与 `calculated_at`

## 3. 增量与全量

- 增量计算：仅处理本批发生变化的 `ip/mac`
- 全量计算：按计划任务重建所有IP定位记录
- 增量失败时允许回退到全量重建

## 4. 并发与事务

- 单批次计算采用事务提交
- 快照切换采用版本号控制
- 计算失败时不污染当前有效快照

## 5. 观测指标

- `input_arp_count`
- `input_mac_count`
- `output_location_count`
- `cross_device_match_ratio`
- `arp_only_ratio`
- `duration_ms`

## 6. 验收标准

- 同批次重复执行结果稳定
- 支持跨设备MAC匹配并产出可解释证据
- 大批量计算时无部分覆盖和脏写
