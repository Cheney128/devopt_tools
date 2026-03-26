# IP定位 Ver3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将IP定位默认查询路径切换为“离线快照读取”，并建立可校验、可回滚的批次化计算机制。  
**Architecture:** 复用现有ARP/MAC采集链路，新增当前/历史分层表与定位快照表；通过增量计算任务生成 `ip_location_current`，API层默认读快照，保留实时模式用于诊断；通过批次状态与一致性校验实现安全发布。  
**Tech Stack:** FastAPI, SQLAlchemy, APScheduler, Vue3, Pinia, Pytest

---

### Task 1: 建立数据模型与迁移

**Files:**
- Modify: `app/models/models.py`
- Modify: `scripts/migrate_ip_location_core_switch.py`
- Test: `tests/unit/test_migration_script.py`

**Step 1: 写失败测试**
- 为新表存在性、索引和幂等性补测试断言

**Step 2: 运行失败测试**
- Run: `pytest tests/unit/test_migration_script.py -q`
- Expected: 出现新表缺失或字段缺失失败

**Step 3: 实现最小迁移代码**
- 新增当前/历史/快照表结构与必要索引
- 将 Ver3 迁移注册到自动迁移管理器启动链路，仅启用 MySQL 方言

**Step 4: 回归迁移测试**
- Run: `pytest tests/unit/test_migration_script.py -q`
- Expected: 通过

**Step 5: 验证启动自动迁移**
- Run: `pytest tests/unit/test_migration_manager.py -q`
- Expected: 通过并可验证重复执行幂等

### Task 2: 实现快照计算引擎

**Files:**
- Modify: `app/services/ip_location_service.py`
- Create: `app/services/ip_location_snapshot_service.py`
- Test: `tests/unit/test_ip_location_service.py`

**Step 1: 写失败测试**
- 覆盖 `same_device/cross_device/arp_only` 三种匹配类型

**Step 2: 运行失败测试**
- Run: `pytest tests/unit/test_ip_location_service.py -q`
- Expected: 新逻辑断言失败

**Step 3: 实现最小代码**
- 从当前ARP和当前MAC生成快照并写入批次字段

**Step 4: 回归测试**
- Run: `pytest tests/unit/test_ip_location_service.py -q`
- Expected: 通过

### Task 3: 打通采集触发增量刷新

**Files:**
- Modify: `app/services/ip_location_scheduler.py`
- Modify: `app/services/ip_location_service.py`
- Test: `tests/unit/test_ip_location_scheduler.py`

**Step 1: 写失败测试**
- 验证采集完成后触发增量计算任务

**Step 2: 运行失败测试**
- Run: `pytest tests/unit/test_ip_location_scheduler.py -q`
- Expected: 触发逻辑断言失败

**Step 3: 实现最小代码**
- 注入增量计算入口，失败时保持旧快照

**Step 4: 回归测试**
- Run: `pytest tests/unit/test_ip_location_scheduler.py -q`
- Expected: 通过

### Task 4: 切换API默认快照读取

**Files:**
- Modify: `app/api/endpoints/ip_location.py`
- Modify: `app/schemas/ip_location_schemas.py`
- Test: `tests/unit/test_ip_location_api.py`

**Step 1: 写失败测试**
- 断言默认模式读取快照并返回批次证据字段

**Step 2: 运行失败测试**
- Run: `pytest tests/unit/test_ip_location_api.py -q`
- Expected: 字段或模式断言失败

**Step 3: 实现最小代码**
- 增加 `mode=snapshot|realtime`，默认 `snapshot`

**Step 4: 回归测试**
- Run: `pytest tests/unit/test_ip_location_api.py -q`
- Expected: 通过

### Task 5: 前端接入快照与诊断模式

**Files:**
- Modify: `frontend/src/views/ip-location/IPLocationSearch.vue`
- Modify: `frontend/src/views/ip-location/IPLocationList.vue`
- Modify: `frontend/src/api/index.js`
- Test: `frontend/test/IPLocation*.test.js`

**Step 1: 写失败测试**
- 断言页面默认走快照接口并展示计算时间/匹配类型

**Step 2: 运行失败测试**
- Run: `npm test -- IPLocation`
- Expected: 断言失败

**Step 3: 实现最小代码**
- 加入模式切换参数和字段展示

**Step 4: 回归测试**
- Run: `npm test -- IPLocation`
- Expected: 通过

### Task 6: 增加一致性校验与回滚

**Files:**
- Create: `app/services/ip_location_validation_service.py`
- Modify: `app/services/ip_location_snapshot_service.py`
- Test: `tests/unit/test_ip_location_validation_service.py`

**Step 1: 写失败测试**
- 覆盖差异率超阈值不切换批次场景

**Step 2: 运行失败测试**
- Run: `pytest tests/unit/test_ip_location_validation_service.py -q`
- Expected: 断言失败

**Step 3: 实现最小代码**
- 新增批次状态与回滚逻辑

**Step 4: 回归测试**
- Run: `pytest tests/unit/test_ip_location_validation_service.py -q`
- Expected: 通过

### Task 7: 做端到端验证与文档回填

**Files:**
- Test: `tests/integration/test_ip_location_snapshot_flow.py`
- Modify: `docs/功能需求/ip-location-ver3/PROGRESS.MD`
- Modify: `docs/变更记录/diff-change.md`
- Modify: `docs/decision-log.md`

**Step 1: 写集成测试**
- 覆盖采集→计算→快照查询→回滚主链路

**Step 2: 运行集成测试**
- Run: `pytest tests/integration/test_ip_location_snapshot_flow.py -q`
- Expected: 通过

**Step 3: 更新文档**
- 回填进度、变更、决策记录

**Step 4: 全量回归抽样**
- Run: `pytest tests/unit/test_ip_location*.py tests/unit/test_ip_location_api.py -q`
- Expected: 通过
