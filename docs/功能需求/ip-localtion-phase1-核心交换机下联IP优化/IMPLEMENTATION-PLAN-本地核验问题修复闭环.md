# IP定位优化本地核验问题修复闭环 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不影响现网可用性的前提下，闭环本地核验报告中的数据库迁移、模型同步与配置容错问题，恢复IP定位优化功能的完整能力。

**Architecture:** 采用“先稳定、后收敛、再治理”的三段式方案。先保留当前容错保障业务可用，再完成数据库结构与迁移链路修复，最后回收临时代码并补齐验证与治理机制。

**Tech Stack:** FastAPI, SQLAlchemy, MySQL, PyMySQL, Pytest

---

## 一、Brainstorming结论（细化报告）

### 1) 问题聚类

1. **连接层问题**：数据库URL中密码特殊字符未统一编码，导致连接与迁移失败。
2. **迁移层问题**：MigrationManager存在事务处理与兼容性细节问题，迁移历史记录不稳定。
3. **模型层问题**：`devices.device_role` 与 ORM 不一致，引发多模块联动报错。
4. **配置层问题**：`ip_location_settings` 缺失时，配置读取链路未完全降级。
5. **技术债务问题**：`hasattr()` 临时防护和注释字段需要在迁移完成后回收。

### 2) 备选路径

- **方案A（推荐）**：分阶段闭环（稳定优先）
  - 优点：风险最低，可随时回滚，便于验证每个阶段的增量收益。
  - 代价：阶段较多，文档与测试同步工作量较高。
- **方案B**：一次性全量修复
  - 优点：改动集中，周期短。
  - 代价：回归面大，问题定位困难。
- **方案C**：长期维持临时兜底
  - 优点：短期成本最低。
  - 代价：技术债务持续累积，后续维护风险上升。

### 3) 决策

采用**方案A（分阶段闭环）**，并在每阶段设置可验证的退出条件，不进入实现动作前先完成计划与文档对齐。

---

## 二、范围定义

### In Scope

- 数据库URL编码与迁移管理链路修复
- `device_role` 字段与 `ip_location_settings` 表结构落地
- `IPLocationConfigManager` 容错策略固化
- 临时防护代码回收计划
- Phase 子文档与进度文档统一

### Out of Scope

- 新增业务功能（仅处理稳定性、一致性与可维护性）
- 与本次IP定位优化无关的跨域重构

---

## 三、实施任务分解（仅计划，不执行）

### Task 1: 数据库连接与迁移入口统一

**Files:**
- Modify: `app/services/migration_manager.py`
- Modify: `app/config.py`（如需统一URL处理入口）
- Check: `.env`（仅配置核对）

**Steps:**
1. 固化数据库URL密码编码逻辑，确保 `@` 等特殊字符兼容。
2. 统一迁移引擎初始化流程，避免重复拼接与重复编码。
3. 修正事务提交方式，统一使用 `engine.begin()`。
4. 为异常分级（warning/error）建立一致策略。
5. 补充对应单元测试与失败场景测试。

**Exit Criteria:**
- 迁移入口可稳定连接数据库
- 迁移执行与记录链路无 `commit` 兼容性错误

### Task 2: 数据库结构补齐与幂等迁移验证

**Files:**
- Modify: `scripts/migrate_ip_location_core_switch.py`
- Modify: `scripts/auto_migrate.py`
- Modify: `app/models/models.py`

**Steps:**
1. 校验 `device_role` 字段迁移与索引创建语句幂等性。
2. 校验 `ip_location_settings` 建表与初始化幂等性。
3. 对启动自动迁移加入前后状态日志与失败降级策略。
4. 明确“迁移成功后恢复模型字段”的切换条件。
5. 补充迁移回滚与重复执行验证。

**Exit Criteria:**
- 重复执行迁移无副作用
- 启动自动迁移可见清晰状态日志

### Task 3: 服务层临时兜底回收计划

**Files:**
- Modify: `app/services/core_switch_recognizer.py`
- Modify: `app/services/device_role_manager.py`
- Modify: `app/services/ip_location_config_manager.py`

**Steps:**
1. 识别并标注 `hasattr()` 临时防护点。
2. 定义“迁移完成后”的回收顺序与回滚策略。
3. 保留 `ip_location_settings` 缺失时默认配置降级能力。
4. 统一异常日志语义，避免误报为系统级错误。
5. 补充容错与回收后的回归测试用例。

**Exit Criteria:**
- 临时防护具备明确退场条件
- 配置表缺失时系统仍可读默认配置

### Task 4: API与端到端回归核验

**Files:**
- Modify: `app/api/endpoints/ip_location.py`
- Modify: `app/api/endpoints/ip_location_config.py`
- Modify: `app/api/endpoints/devices.py`

**Steps:**
1. 覆盖 `/api/v1/ip-location/collection/status` 等关键端点回归。
2. 验证“IP定位页面、刷新、立即收集、IP列表”链路。
3. 验证未迁移与已迁移两种状态下的行为一致性。
4. 补齐认证、参数与异常返回一致性检查。
5. 输出人工核验脚本与结果模板。

**Exit Criteria:**
- 报告中提及的所有报错入口均恢复
- 关键API在两种数据库状态下均可预期运行

### Task 5: 文档与技术债务治理闭环

**Files:**
- Modify: `docs/debugs/2026-03-23-IP定位功能异常修复报告.md`
- Modify: `docs/debugs/2026-03-23-IP定位优化功能本地运行问题分析报告.md`
- Modify: `docs/功能需求/ip-localtion-phase1-核心交换机下联IP优化/PROGRESS.md`
- Modify: `docs/功能需求/ip-localtion-phase1-核心交换机下联IP优化/Phase-*.md`

**Steps:**
1. 将“已修复/待执行/风险/回滚”按模块同步到Phase文档。
2. 更新PROGRESS状态为“规划完成，待执行闭环”。
3. 统一文档中的时间线与状态描述，避免冲突。
4. 增补验收检查清单与完成判据。

**Exit Criteria:**
- 设计文档、Phase文档、进度文档状态一致
- 后续执行人员可直接按文档推进

---

## 四、验收清单（计划阶段）

- [ ] 报告问题完成模块映射（连接层/迁移层/模型层/配置层/技术债）
- [ ] 形成分阶段闭环方案并定义退出条件
- [ ] 明确“仅规划不执行”边界
- [ ] Phase子文档完成按模块对齐更新
- [ ] PROGRESS进度文档更新为可执行状态

---

## 五、执行边界说明

本计划文档仅用于下一阶段执行指导，当前不触发代码实现、不触发数据库迁移、不触发功能发布动作。
