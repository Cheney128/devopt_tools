---
ontology:
  id: DOC-2026-03-009-PLAN
  type: plan
  problem: 安全/路由修复
  problem_id: P009
  status: active
  created: 2026-03-26
  updated: 2026-03-26
  author: Claude
  tags:
    - documentation
---
# 修复计划：配置 API 路由顺序问题

**创建日期**: 2026-03-26  
**优先级**: P0  
**问题**: 路由顺序导致 `/backup-schedules` 等路径被 `/{config_id}` 匹配

---

## 问题分析

FastAPI 路由按定义顺序匹配，当前配置：
1. `GET /` - 配置列表 ✅
2. `GET /{config_id}` - 配置详情 (第 80 行) ❌ 太早定义
3. ...其他路由
4. `POST /backup-schedules` (第 443 行)
5. `GET /backup-schedules` (第 487 行)

**问题**：`/{config_id}` 在 `/backup-schedules` 之前定义，导致 `backup-schedules` 被当作 `config_id` 参数解析

---

## 修复方案

将所有具体路由移到参数路由之前：

**正确顺序**:
1. `GET /` - 配置列表
2. `POST /` - 创建配置
3. `GET /backup-schedules` - 备份计划列表
4. `POST /backup-schedules` - 创建备份计划
5. `GET /backup-schedules/{schedule_id}` - 备份计划详情
6. `PUT /backup-schedules/{schedule_id}` - 更新备份计划
7. `DELETE /backup-schedules/{schedule_id}` - 删除备份计划
8. `POST /backup-schedules/batch` - 批量创建
9. `GET /backup-tasks` - 备份任务列表
10. `GET /backup-tasks/{task_id}` - 备份任务详情
11. `POST /backup-tasks/{task_id}/cancel` - 取消任务
12. `GET /monitoring/*` - 监控相关
13. `GET /device/{device_id}/*` - 设备相关
14. `GET /diff/{config_id1}/{config_id2}` - 配置对比
15. `POST /{config_id}/commit-git` - 提交到 Git
16. `DELETE /{config_id}` - 删除配置
17. `GET /{config_id}` - 配置详情 (移到最后)

---

## 执行步骤

1. 备份原文件
2. 重构路由顺序
3. 重启后端服务
4. 测试 API

---

## 测试用例

```bash
# 测试备份计划 API
curl http://localhost:8000/api/v1/configurations/backup-schedules

# 测试配置列表 API
curl http://localhost:8000/api/v1/configurations/

# 测试监控 API
curl http://localhost:8000/api/v1/configurations/monitoring/execution-logs
```
