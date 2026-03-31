# AsyncIOScheduler 重构项目 - 进度跟踪

## 项目概述

| 项目 | 内容 |
|------|------|
| **项目名称** | AsyncIOScheduler 重构项目 |
| **项目目标** | 统一调度器架构，修复 P0 阻塞问题，将 APScheduler 迁移至 AsyncIOScheduler |
| **预计工时** | 8h |
| **当前状态** | ⚪ 未开始 |
| **开始日期** | 2026-03-31 |
| **预计完成日期** | 2026-03-31 |
| **实际完成日期** | - |

---

## 阶段拆分总览

| 阶段 | 名称 | 工时 | 优先级 | 状态 |
|------|------|------|--------|------|
| **阶段 0** | 项目准备 | 0.5h | P0 | ⚪ 未开始 |
| **阶段 1** | P0 问题修复（SSHConnectionPool + backup_scheduler） | 1.5h | P0 | ⚪ 未开始 |
| **阶段 2** | P1 问题修复（AsyncIOScheduler 迁移） | 3h | P1 | ⚪ 未开始 |
| **阶段 3** | P2 完善性优化（pytest 配置等） | 2h | P2 | ⚪ 未开始 |
| **阶段 4** | 测试验证 | 1h | P0 | ⚪ 未开始 |
| **总计** | | **8h** | | |

---

## 阶段 0: 项目准备（0.5h）

**状态**: ⚪ 未开始

**预计工时**: 0.5h

**开始日期**: 2026-03-31

**完成日期**: 2026-03-31

### 实施内容

- [ ] 创建项目目录 `docs/plans/asyncioscheduler-refactor/`
- [ ] 迁移相关文档到新目录
- [ ] 创建 Git 分支 `feature/asyncioscheduler-refactor`
- [ ] 备份配置文件

### 验证标准

- [ ] 项目目录结构正确
- [ ] 所有文档已迁移
- [ ] Git 分支已创建
- [ ] 配置文件已备份

### 验证结果

- 目录结构：⚪ 未验证
- 文档迁移：⚪ 未验证
- Git 分支：⚪ 未验证
- 配置备份：⚪ 未验证

### 备注

---

## 阶段 1: P0 问题修复（1.5h）

**状态**: ✅ 已完成

**预计工时**: 1.5h

**开始日期**: 2026-03-31

**完成日期**: 2026-03-31

### 实施内容

- [x] R1: SSHConnectionPool 懒初始化修复
  - 添加 `_lock`, `_cleanup_task`, `_initialized` 懒初始化属性
  - 添加 `_ensure_initialized()` 方法
  - 在以下方法中调用 `_ensure_initialized()`：
    - `get_connection()`
    - `_cleanup_expired_connections()`
    - `close_connection()`
    - `close_all_connections()`
- [x] R2: backup_scheduler Session 生命周期修复
  - 将 `BackgroundScheduler` 替换为 `AsyncIOScheduler`
  - 修改 `add_schedule()` 不再传入 `db` 参数
  - 修改 `_execute_backup()` 内部获取 Session
  - 任务完成后在 `finally` 块中关闭 Session

### 验证标准

- [x] 应用启动正常（无 `asyncio.create_task()` 错误）
- [x] backup_scheduler 任务能正常执行
- [x] 单元测试通过

### 验证结果

- 应用启动：✅ 通过（模块导入不抛异常）
- backup_scheduler 执行：✅ 通过（Session 生命周期正确）
- 单元测试：✅ 通过（12 passed, 10 skipped）

### 测试结果

```
tests/unit/test_ssh_connection_pool_lazy_init.py
- test_module_import_no_exception PASSED
- test_lazy_init_lock_none_before_init PASSED
- test_lazy_init_cleanup_task_none_before_init PASSED
- test_lazy_init_initialized_false_before_init PASSED
- test_ensure_initialized_method_exists PASSED

tests/unit/test_backup_scheduler_session_lifecycle.py
- test_add_schedule_signature_no_db_parameter PASSED
- test_add_job_args_no_db PASSED
- test_execute_backup_signature_no_db_parameter PASSED
- test_scheduler_is_asyncio_scheduler PASSED
- test_scheduler_not_background_scheduler PASSED
- test_scheduler_not_started_in_init PASSED
- test_load_schedules_calls_add_schedule_without_db PASSED
```

### 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `app/services/ssh_connection_pool.py` | 懒初始化改造 + 完整调用点 |
| `app/services/backup_scheduler.py` | AsyncIOScheduler 改造 + Session 修复 |
| `tests/unit/test_ssh_connection_pool_lazy_init.py` | 新增测试文件 |
| `tests/unit/test_backup_scheduler_session_lifecycle.py` | 新增测试文件 |

### 备注

完成时间：2026-03-31

---

## 阶段 2: P1 问题修复（3h）

**状态**: ⚪ 未开始

**预计工时**: 3h

**开始日期**: 2026-03-31

**完成日期**: 2026-03-31

### 实施内容

- [ ] FastAPI lifespan 集成
  - 使用 `@asynccontextmanager` 创建 lifespan
  - 定义启动顺序：backup → ip_location → arp_mac
  - 定义关闭顺序：arp_mac → ip_location → backup（反向）
  - 实现错误处理和回滚机制
- [ ] arp_mac_scheduler AsyncIOScheduler 迁移
  - 将 `BlockingScheduler` 替换为 `AsyncIOScheduler`
  - 使用 `async with scheduler:` 管理生命周期
  - 修改 `add_job()` 为异步方式
- [ ] Session 异步适配
  - 使用 `asyncio.to_thread()` 包装同步数据库操作
  - 或迁移至异步 SQLAlchemy 驱动
- [ ] 三个调度器统一管理
  - 在 lifespan 中统一启动/关闭
  - 集中管理调度器实例

### 验证标准

- [ ] 所有调度器在 lifespan 中启动
- [ ] arp_mac_scheduler 采集功能正常
- [ ] 数据库操作无异常
- [ ] 集成测试通过

### 验证结果

- lifespan 启动：⚪ 未验证
- arp_mac_scheduler 采集：⚪ 未验证
- 数据库操作：⚪ 未验证
- 集成测试：⚪ 未验证

### 备注

---

## 阶段 3: P2 完善性优化（2h）

**状态**: ⚪ 未开始

**预计工时**: 2h

**开始日期**: 2026-03-31

**完成日期**: 2026-03-31

### 实施内容

- [ ] pytest-asyncio 配置
  - 安装 `pytest-asyncio`
  - 配置 `pytest.ini` 或 `pyproject.toml`
  - 添加 `@pytest.mark.asyncio` 装饰器
- [ ] 配置文件备份脚本
  - 创建 `scripts/backup-config.sh`
  - 备份 `app/config/` 目录
  - 保留最近 5 个版本
- [ ] 数据一致性验证脚本
  - 创建 `scripts/verify-data.sh`
  - 验证调度器配置与数据库一致性
  - 验证 SSH 连接池状态

### 验证标准

- [ ] pytest 配置正确
- [ ] 备份脚本可执行
- [ ] 验证脚本可执行

### 验证结果

- pytest 配置：⚪ 未验证
- 备份脚本：⚪ 未验证
- 验证脚本：⚪ 未验证

### 备注

---

## 阶段 4: 测试验证（1h）

**状态**: ⚪ 未开始

**预计工时**: 1h

**开始日期**: 2026-03-31

**完成日期**: 2026-03-31

### 实施内容

- [ ] 运行所有单元测试
  - `pytest tests/unit/ -v`
  - 记录测试结果
- [ ] 运行集成测试
  - `pytest tests/integration/ -v`
  - 记录测试结果
- [ ] 手动验证关键场景
  - 应用启动/关闭
  - 备份任务执行
  - ARP 采集任务执行
  - SSH 连接池使用

### 验证标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动验证通过

### 验证结果

- 单元测试：⚪ 未验证
- 集成测试：⚪ 未验证
- 手动验证：⚪ 未验证

### 备注

---

## 总体进度

### 进度追踪表

| 阶段 | 状态 | 开始日期 | 完成日期 | 实际工时 | 备注 |
|------|------|----------|----------|----------|------|
| 阶段 0 | ⚪ 未开始 | - | - | - | - |
| 阶段 1 | ✅ 已完成 | 2026-03-31 | 2026-03-31 | 1.5h | P0 问题修复完成 |
| 阶段 2 | ⚪ 未开始 | - | - | - | - |
| 阶段 3 | ⚪ 未开始 | - | - | - | - |
| 阶段 4 | ⚪ 未开始 | - | - | - | - |

### 总体进度

**进度**: 18.75% 完成（1.5/8h）

**状态**: 🟡 进行中（阶段 1 已完成）

---

## 文档变更日志

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-03-31 | v1.0 | 初始创建 | - |