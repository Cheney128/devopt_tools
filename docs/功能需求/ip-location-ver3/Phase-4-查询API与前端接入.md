# Phase-4-查询API与前端接入

## 1. 目标

将前端“IP定位”查询路径切换到 `ip_location_current`，实现低延迟读取，并保留实时重算诊断能力。

## 2. API策略

- 默认接口：读取快照表
- 诊断接口：管理员可选择实时重算单IP
- 返回字段增加：
  - `match_type`
  - `arp_source_device`
  - `mac_hit_device`
  - `calculated_at`
  - `calculate_batch_id`

## 3. 查询能力

- 支持分页与搜索
- 支持筛选：
  - 位置
  - 上联过滤
  - 核心设备过滤
  - 可信度阈值
- 默认排序：`confidence DESC, last_seen DESC`

## 4. 前端改造点

- 列表页与搜索页改读快照接口
- 增加“数据时间”与“匹配类型”展示
- 增加“实时重算”按钮（仅管理员可见）
- 保持现有筛选交互不破坏

## 5. 兼容策略

- API路径保持兼容，内部改读逻辑
- 预留参数 `mode=snapshot|realtime`
- 默认 `snapshot`，避免前端大改

## 6. 验收标准

- 默认查询不再触发重型动态关联
- 前端交互与既有体验兼容
- 管理员可用实时模式定位疑难个案
