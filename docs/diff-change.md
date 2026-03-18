# 代码变更记录

## 变更记录格式

每次代码变更请按照以下格式记录：

### YYYY-MM-DD HH:MM:SS

**变更文件**：文件路径
**变更位置**：行号范围
**变更内容**：具体变更的代码内容
**变更的原因**：变更的目的和原因

---

## 变更记录

### 2026-02-09 12:00:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：487-540
**变更内容**：
- 修改 `@router.get("/backup-schedules")` 的 response_model 从 `List[BackupScheduleSchema]` 改为 `Dict[str, Any]`
- 添加分页参数：`page: int = Query(1, ge=1, description="页码")` 和 `page_size: int = Query(10, ge=1, le=100, description="每页数量")`
- 添加总数查询：`total = query.count()`
- 添加分页查询逻辑：使用 `offset((page - 1) * page_size).limit(page_size)` 实现真正的分页
- 修改返回值格式：从直接返回数组 `return schedules` 改为返回对象 `return {"schedules": schedules, "total": total}`

**变更原因**：修复备份计划API返回格式与前端期望不匹配的问题。后端原直接返回数组，但前端期望 `{schedules: [], total: N}` 格式，导致数据无法正确显示并触发 setAttribute 错误。同时添加分页支持，提高大数据量查询性能。

### 2026-02-23 15:30:00

**变更文件**：app/models/models.py
**变更位置**：153行
**变更内容**：
- 在 BackupSchedule 类中添加字段：`last_run_time = Column(DateTime, nullable=True, index=True)`

**变更原因**：第二阶段数据库优化，为 backup_schedules 表添加 last_run_time 字段，用于直接存储上次执行时间，避免关联查询，提升查询性能。

### 2026-02-23 15:35:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：145-175行 (get_backup_schedules函数)
**变更内容**：
- 移除批量查询最后执行时间的关联查询代码（schedule_ids查询、last_executions查询、last_run_dict构建）
- 修改 last_run_time 的获取方式：从 `last_run_dict.get(schedule.id)` 改为 `schedule.last_run_time`
- 添加注释说明：直接从表字段读取 last_run_time

**变更原因**：配合第二阶段数据库优化，查询时直接从 backup_schedules 表的 last_run_time 字段读取，不再关联查询 backup_execution_logs 表，提升查询性能。

### 2026-02-23 15:40:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：189-220行 (get_backup_schedule函数)
**变更内容**：
- 移除查询最后执行时间的关联查询代码（last_execution查询）
- 修改 last_run_time 的获取方式：从 `last_execution` 改为 `schedule.last_run_time`
- 添加注释说明：直接从表字段读取

**变更原因**：配合第二阶段数据库优化，获取单个备份计划时直接从表字段读取 last_run_time。

### 2026-02-23 15:45:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：64-100行 (create_backup_schedule函数)
**变更内容**：
- 在记录执行日志后，添加更新 last_run_time 的逻辑：
  ```python
  # 更新备份计划的last_run_time
  if backup_result.get("success"):
      db_schedule.last_run_time = datetime.now()
  ```

**变更原因**：创建备份计划时立即执行备份成功后，需要更新 backup_schedules 表的 last_run_time 字段，保持数据一致性。

### 2026-02-23 15:50:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：680-700行 (backup_now函数)
**变更内容**：
- 在创建执行日志后，添加更新 last_run_time 的逻辑：
  ```python
  # 更新备份计划的last_run_time
  if schedule and result.get("success"):
      schedule.last_run_time = datetime.now()
  ```

**变更原因**：立即备份成功后，需要更新对应备份计划的 last_run_time 字段，保持数据一致性。

### 2026-02-23 15:55:00

**变更文件**：app/services/backup_scheduler.py
**变更位置**：185-205行 (_execute_backup函数)
**变更内容**：
- 在创建执行日志后，添加更新 last_run_time 的逻辑：
  ```python
  # 更新备份计划的last_run_time
  if schedule:
      schedule.last_run_time = datetime.now()
  ```

**变更原因**：定时备份任务执行成功后，需要更新对应备份计划的 last_run_time 字段，保持数据一致性。

### 2026-02-23 16:00:00

**变更文件**：scripts/update_backup_schedules_add_last_run_time.py
**变更位置**：新增文件
**变更内容**：
- 创建数据库更新脚本，用于：
  1. 检查并添加 last_run_time 字段到 backup_schedules 表
  2. 创建索引 ix_backup_schedules_last_run_time
  3. 从 backup_execution_logs 表同步现有数据的最后执行时间

**变更原因**：第二阶段数据库优化的数据库迁移脚本，用于在生产环境执行数据库结构变更。

### 2026-02-23 17:00:00

**变更文件**：scripts/db_migrate_docker.py
**变更位置**：新增文件
**变更内容**：
- 创建Docker生产环境数据库迁移脚本，包含以下功能：
  1. Docker环境检测
  2. 迁移前自动备份数据库（使用mysqldump）
  3. 幂等性迁移：检查字段和索引是否存在，避免重复添加
  4. 数据同步：从 backup_execution_logs 表同步 last_run_time
  5. 迁移结果验证：检查字段、索引、数据同步情况
  6. 迁移状态标记：创建 .db_migration_completed 文件

**变更原因**：为Docker生产环境提供安全、可靠的数据库迁移方案，支持自动备份和回滚。

### 2026-02-23 17:10:00

**变更文件**：scripts/auto_migrate.py
**变更位置**：新增文件
**变更内容**：
- 创建自动数据库迁移脚本，用于容器启动时自动执行迁移检查
- 功能：
  1. 检查是否需要迁移（检测 last_run_time 字段是否存在）
  2. 调用 db_migrate_docker.py 执行实际迁移
  3. 失败时记录日志但不阻止应用启动

**变更原因**：实现零停机时间的自动数据库迁移，在应用启动时自动完成数据库结构更新。

### 2026-02-23 17:15:00

**变更文件**：scripts/db_rollback.py
**变更位置**：新增文件
**变更内容**：
- 创建数据库回滚脚本，用于在迁移失败时恢复数据库
- 功能：
  1. 列出所有可用的备份文件
  2. 回滚前自动备份当前数据库
  3. 支持回滚到最新备份或指定备份
  4. 恢复后验证数据库状态
  5. 命令行参数支持：--list, --latest, --backup, --force

**变更原因**：提供数据库迁移的安全保障机制，确保在迁移失败时可以快速恢复。

### 2026-02-23 17:20:00

**变更文件**：docker/entrypoint.sh
**变更位置**：68-80行
**变更内容**：
- 在数据库初始化后，添加自动迁移检查：
  ```bash
  # 执行数据库迁移（自动检查并执行）
  echo "=========================================="
  echo "Checking Database Migration..."
  echo "=========================================="
  
  python3 /unified-app/scripts/auto_migrate.py
  
  if [ $? -eq 0 ]; then
      echo "✓ Database migration check completed!"
  else
      echo "⚠ Database migration check failed, but continuing..."
  fi
  ```

**变更原因**：将自动数据库迁移集成到容器启动流程中，实现应用启动时的自动迁移。

### 2026-02-23 17:30:00

**变更文件**：docs/Docker生产环境数据库迁移指南.md
**变更位置**：新增文件
**变更内容**：
- 创建完整的Docker生产环境数据库迁移文档，包括：
  1. 迁移方案概述（自动迁移、手动迁移、回滚机制）
  2. 迁移前准备（备份、检查数据库状态）
  3. 两种迁移方式的详细步骤
  4. 迁移验证方法（SQL检查、API验证）
  5. 回滚操作指南
  6. 故障排除（常见问题及解决方案）
  7. 最佳实践（部署流程、监控告警、定期备份）

**变更原因**：为运维人员提供完整的数据库迁移操作指南，确保生产环境迁移的安全性和可靠性。

### 2026-03-10 17:15:00

**变更文件**：frontend/src/style.css
**变更位置**：1-67行
**变更内容**：
- 移除 `body` 的 `display: flex; place-items: center;` 样式，避免页面居中
- 移除 `#app` 的 `max-width: 1280px; text-align: center;` 限制
- 添加全局重置样式 `* { margin: 0; padding: 0; box-sizing: border-box; }`
- 修改 `#app` 为 `width: 100%; height: 100vh;` 支持全屏布局

**变更原因**：修复前端布局与文档预期不符的问题。原 style.css 中的全局样式与 App.vue 的布局样式冲突，导致页面无法正确显示侧边栏和顶部导航栏的完整布局。

### 2026-03-10 17:20:00

**变更文件**：frontend/src/router/index.js
**变更位置**：114-149行
**变更内容**：
- 恢复路由守卫的登录验证功能
- 移除临时禁用登录验证的代码（`return next()` 直接跳过验证）
- 恢复完整的路由守卫逻辑：
  1. 检查用户初始化状态
  2. 已登录用户访问登录页重定向到首页
  3. 公开页面直接访问
  4. 需要登录的页面检查登录状态
  5. 管理员权限检查

**变更原因**：路由守卫被临时禁用导致用户可以未登录访问页面，但 App.vue 中 `isLoggedIn` 为 false 时显示简化布局（无侧边栏），与文档预期的完整布局不符。恢复登录验证后，未登录用户会被重定向到登录页面，登录后才能看到完整布局。

### 2026-03-11 00:15:00

**变更文件**：requirements.txt
**变更位置**：22-26行
**变更内容**：
- 在认证相关依赖部分添加 `bcrypt==4.0.1` 版本锁定
- 修改前：
  ```
  # 认证相关依赖
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  pillow==10.1.0
  ```
- 修改后：
  ```
  # 认证相关依赖
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  bcrypt==4.0.1
  pillow==10.1.0
  ```

**变更原因**：修复 Docker 部署后登录失败的问题。`passlib==1.7.4` 与新版 `bcrypt` (4.1+) 不兼容，新版 `bcrypt` 移除了 `__about__` 属性导致 `passlib` 初始化失败。固定 `bcrypt==4.0.1` 版本后问题解决。

---

### 2026-03-18 00:00:00

**变更文件**：app/services/backup_service.py
**变更位置**：新增文件
**变更内容**：
- 新增 BackupService 类，封装备份核心逻辑
- 添加 __init__() 方法，初始化 netmiko_service 和 git_service
- 添加 collect_config() 方法，实现从设备采集配置的核心逻辑
- 添加 execute_scheduled_backup() 方法，执行定时备份并记录日志
- 添加详细的日志记录（使用 [BackupService] 前缀）
- 添加完善的错误处理

**变更原因**：架构优化，将备份核心逻辑从 API 端点中提取出来，提高代码可复用性、可测试性和可维护性。

---

### 2026-03-18 00:05:00

**变更文件**：app/services/backup_scheduler.py
**变更位置**：第 91 行、第 144-190 行
**变更内容**：
- 修改 add_job 调用：args=[schedule.device_id, db] → args=[schedule.device_id]，不再传递数据库会话
- 修改 _execute_backup：移除 async 关键字，从异步函数改为同步函数
- 修改 _execute_backup 签名：仅接受 device_id 参数
- _execute_backup 内部创建 SessionLocal() 会话，不依赖外部传入
- 使用 asyncio.run() 调用 BackupService.execute_scheduled_backup()
- 添加 1 次重试机制（间隔 5 秒）
- 添加详细的日志记录（使用 [ScheduledBackup] 前缀）
- 使用 try/finally 确保数据库会话关闭

**变更原因**：
1. 修复异步函数与 APScheduler 不兼容的问题 - APScheduler 是同步调度器，无法正确处理 async 函数
2. 修复数据库会话传递问题 - 不再传递 HTTP 请求中的 db 会话，避免会话过期问题
3. 添加重试机制 - 提高网络抖动等临时性故障的成功率

---

### 2026-03-18 00:10:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：第 29 行、第 37-105 行、第 277-342 行、第 639-697 行、第 1190-1283 行
**变更内容**：
- 添加导入：from app.services.backup_service import BackupService
- 修改 create_backup_schedule：移除 netmiko_service 和 git_service 参数
- 修改 batch_create_backup_schedules：移除 netmiko_service 和 git_service 参数
- 修改 backup_now：移除 netmiko_service 和 git_service 参数
- 修改 collect_config_from_device：简化实现，直接调用 BackupService.collect_config()

**变更原因**：架构优化，API 端点不再包含业务逻辑，只负责 HTTP 层处理，所有备份逻辑委托给 BackupService。

---

### 2026-03-18 00:15:00

**变更文件**：app/main.py
**变更位置**：第 4-13 行、第 61-82 行
**变更内容**：
- 添加导入：import logging
- 添加 logger 初始化：logger = logging.getLogger(__name__)
- 修改 startup_event：使用 logger.info() 替代 print()
- 增强启动日志：添加 "[Startup] Loading backup schedules..." 等日志
- 增强异常日志：使用 logger.error() 替代 print()

**变更原因**：增强启动日志，便于排查调度器初始化和任务加载问题，使用标准的 logging 模块替代 print。

---

### 2026-03-18 00:20:00

**变更文件**：tests/unit/test_backup_service.py
**变更位置**：新增文件
**变更内容**：
- 新增 BackupService 单元测试文件
- 添加测试用例：
  - TC-BS-001: collect_config - 设备不存在
  - TC-BS-002: collect_config - 配置采集失败
  - TC-BS-003: collect_config - 配置无变化
  - TC-BS-004: collect_config - 配置有变化
  - TC-BS-006: execute_scheduled_backup - 成功
  - TC-BS-007: execute_scheduled_backup - 失败
- 使用 pytest fixture 创建 mock 对象

**变更原因**：为 BackupService 添加单元测试，确保代码质量和功能正确性。

---

### 2026-03-18 00:25:00

**变更文件**：tests/unit/test_backup_scheduler.py
**变更位置**：新增文件
**变更内容**：
- 新增 BackupSchedulerService 单元测试文件
- 添加测试用例：
  - TC-BSCH-001: _execute_backup - 同步函数调用
  - TC-BSCH-002: _execute_backup - 创建新的数据库会话
  - TC-BSCH-003: _execute_backup - 调用 asyncio.run()
  - TC-BSCH-006: add_schedule - 参数传递
  - TC-BSCH-007: load_schedules - 日志记录
- 使用 patch 进行依赖注入

**变更原因**：为 BackupSchedulerService 添加单元测试，验证修复方案的正确性。
