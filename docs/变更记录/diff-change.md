# 代码变更记录

---

## 变更 1：前端页面频繁登出问题修复

- **变更的日期**：2026-02-09 20:50
- **变更的文件**：frontend/src/stores/authStore.js
- **变更的位置**：整个文件
- **变更的内容**：
  1. 添加 `isInitialized` 状态标记，用于控制初始化流程
  2. 修改 `init()` 方法，添加幂等性检查（避免重复初始化）
  3. 修改 `init()` 方法的错误处理，区分 401 错误和其他错误
  4. 修改 `fetchCurrentUser()` 方法，抛出错误让调用者处理
  5. 修改 `logout()` 方法，重置 `isInitialized` 状态
- **变更的原因**：解决页面刷新时频繁登出的问题，通过初始化状态标记确保路由守卫等待初始化完成后再进行路由判断

---

## 变更 2：路由守卫逻辑优化

- **变更的日期**：2026-02-09 20:50
- **变更的文件**：frontend/src/router/index.js
- **变更的位置**：router.beforeEach 路由守卫函数
- **变更的内容**：
  1. 使用 `isInitialized` 标记控制初始化流程
  2. 简化路由守卫逻辑，使用 `return next()` 提前返回
  3. 移除重复的用户信息获取逻辑
- **变更的原因**：配合 authStore 的初始化状态标记，确保路由判断在初始化完成后执行，避免竞态条件

---

## 变更 3：移除 App.vue 中的重复初始化

- **变更的日期**：2026-02-09 20:50
- **变更的文件**：frontend/src/App.vue
- **变更的位置**：script setup 部分
- **变更的内容**：
  1. 移除 `onMounted` 导入
  2. 移除 `onMounted` 中的 `authStore.init()` 调用
  3. 添加注释说明初始化逻辑已移至路由守卫
- **变更的原因**：避免与路由守卫中的初始化逻辑重复，由路由守卫统一管理初始化

---

## 变更 4：API 拦截器 401 处理优化

- **变更的日期**：2026-02-09 20:50
- **变更的文件**：frontend/src/api/index.js
- **变更的位置**：响应拦截器的 401 处理逻辑
- **变更的内容**：
  1. 使用 `window.location.href` 替代 `router.push()` 进行跳转
  2. 添加页面路径检查，避免重复跳转到登录页
- **变更的原因**：避免在 API 拦截器中引入 authStore 导致循环依赖，同时避免多次跳转

---

## 变更 5：修复登录后无法获取用户信息问题

- **变更的日期**：2026-02-09 21:05
- **变更的文件**：frontend/src/stores/authStore.js
- **变更的位置**：login() 方法
- **变更的内容**：
  1. 在登录成功后设置 `isInitialized.value = true`
- **变更的原因**：登录成功后，用户已经获取了完整的信息（token 和 user），应该标记为已初始化状态。否则路由守卫会再次调用 `init()` 方法，可能导致重复获取用户信息或竞态条件。

---

## 变更 6：修复 API 拦截器 401 处理导致的自动登出问题

- **变更的日期**：2026-02-09 21:15
- **变更的文件**：frontend/src/api/index.js, frontend/src/stores/authStore.js
- **变更的位置**：
  - api/index.js：响应拦截器的 401 处理逻辑
  - authStore.js：init() 方法的错误处理逻辑
- **变更的内容**：
  1. 在 API 拦截器中，对 `/auth/me` 请求的 401 错误不做处理（不清除 token、不跳转），让调用者决定如何处理
  2. 在 authStore.js 的 `init()` 方法中，处理 401 错误时显示错误消息并清除登录状态
  3. 在 authStore.js 中导入 ElMessage
- **变更的原因**：
  - **根本原因**：页面刷新时，`init()` 调用 `fetchCurrentUser()`，如果返回 401，API 拦截器会立即清除 localStorage 中的 token 并跳转，导致用户被强制登出。
  - **解决方案**：拦截器不再处理 `/auth/me` 的 401 错误，让 `init()` 方法统一处理，避免竞态条件。

---

## 变更 7：备份管理模块重构

- **变更的日期**：2026-02-14 15:30
- **变更的文件**：
  - 新增：frontend/src/views/BackupManagement.vue
  - 新增：frontend/src/views/backup/BackupOverview.vue
  - 新增：frontend/src/views/backup/BackupScheduleManagement.vue
  - 新增：frontend/src/views/backup/BackupMonitoring.vue
  - 新增：frontend/src/views/backup/GitConfigManagement.vue
  - 删除：frontend/src/views/ConfigurationManagement.vue
  - 删除：frontend/src/views/BackupScheduleManagement.vue（原位置）
  - 删除：frontend/src/views/BackupMonitoring.vue（原位置）
  - 删除：frontend/src/views/GitConfigManagement.vue（原位置）
  - 修改：frontend/src/router/index.js
  - 修改：frontend/src/App.vue
- **变更的位置**：
  - 新增 frontend/src/views/backup/ 目录
  - 路由配置全部重写
  - 侧边栏菜单精简
- **变更的内容**：
  1. 创建 BackupManagement.vue 主页面，使用 el-tabs 实现 Tab 切换
  2. 创建 BackupOverview.vue 概览页面，包含统计卡片、快捷操作、趋势图表
  3. 将原有的备份计划、备份监控、Git配置组件移动到 backup/ 子目录
  4. 更新路由配置：
     - 新增 /backup-management 路由
     - 添加旧路由重定向（/configurations、/backup-schedules、/monitoring、/git-configs）
  5. 更新 App.vue 侧边栏菜单：
     - 将"配置管理"更名为"备份管理"
     - 移除独立的"备份计划"、"备份监控"、"Git配置"菜单项
- **变更的原因**：根据前端页面设计文档，将备份相关功能整合到一个模块中，简化菜单结构，提升用户体验

---

## 变更 8：更新数据库模型分析文档

- **变更的日期**：2026-02-14 10:30
- **变更的文件**：docs/项目分析/04-数据库模型分析.md
- **变更的位置**：文档末尾（第6节之后）
- **变更的内容**：
  1. 新增第7节"数据库模型更新记录"
  2. 新增8个数据表的详细说明：
     - users（用户表）
     - roles（角色表）
     - permissions（权限表）
     - user_roles（用户角色关联表）
     - role_permissions（角色权限关联表）
     - captcha_records（验证码记录表）
     - backup_tasks（批量备份任务表）
     - backup_execution_logs（备份执行日志表）
  3. 更新数据库关系图，包含新增的用户认证和备份任务相关表
  4. 更新表统计信息，从11个表增加到19个表
  5. 新增SQLAlchemy模型文件结构说明
  6. 新增模型关联关系代码示例
- **变更的原因**：代码更新后新增了用户认证、权限管理、批量备份任务等模块的数据模型，需要同步更新文档以保持文档与代码的一致性

---

## 变更 9：修复备份管理模块子路由问题

- **变更的日期**：2026-02-15 16:45
- **变更的文件**：frontend/src/router/index.js
- **变更的位置**：/backup-management 路由配置
- **变更的内容**：
  1. 为 /backup-management 路由添加 children 子路由配置
  2. 添加子路由：
     - ''（空路径，对应概览页）
     - 'schedules'（备份计划）
     - 'monitoring'（备份监控）
     - 'git-configs'（Git配置）
  3. 所有子路由都指向 BackupManagement.vue 组件
- **变更的原因**：
  - **问题**：直接访问 /backup-management/git-configs 等子路径时，Vue Router 报错 "No match found for location"
  - **原因**：虽然 BackupManagement.vue 使用 el-tabs 实现了标签页切换，但 Vue Router 没有配置对应的子路由
  - **解决方案**：添加子路由配置，使直接访问子路径时能正确渲染 BackupManagement 组件

---

## 变更 10：测试验证登录验证代码恢复

- **变更的日期**：2026-02-15 16:50
- **变更的文件**：
  - frontend/src/router/index.js
  - frontend/src/App.vue
- **变更的位置**：
  - router/index.js：router.beforeEach 路由守卫函数
  - App.vue：计算属性定义部分
- **变更的内容**：
  1. 恢复 router.beforeEach 中的登录验证逻辑（从测试模式的直接放行恢复为正常验证）
  2. 恢复 App.vue 中的登录状态计算属性（从模拟登录状态恢复为使用 authStore）
- **变更的原因**：测试完成后恢复正常的登录验证机制，确保系统安全性

---

## 变更 11：修复配置管理页面丢失问题

- **变更的日期**：2026-02-19 19:45
- **变更的文件**：
  - 新增：frontend/src/views/backup/ConfigList.vue
  - 修改：frontend/src/views/BackupManagement.vue
  - 修改：frontend/src/router/index.js
  - 修改：docs/功能需求/前端/备份管理/配置管理/配置管理页面丢失.md
- **变更的位置**：
  - 新增 frontend/src/views/backup/ConfigList.vue 配置列表组件
  - BackupManagement.vue：导入和添加配置列表Tab
  - router/index.js：添加 /backup-management/configs 子路由
  - 问题分析文档：添加详细的问题分析和解决方案
- **变更的内容**：
  1. 从Git历史中恢复 ConfigurationManagement.vue 文件（commit: 503c331）
  2. 重命名为 ConfigList.vue 并移动到 views/backup/ 目录
  3. 更新API导入路径（从 ../api/index 改为 ../../api/index）
  4. 修改 BackupManagement.vue：
     - 导入 Document 图标和 ConfigList 组件
     - 在Tabs数组中添加配置列表项
     - 在模板中添加对应的Tab-pane
  5. 更新 router/index.js：
     - 为 /backup-management 路由添加 children 子路由配置
     - 添加 configs 子路由
  6. 更新问题分析文档：添加问题根因分析、解决方案和实施结果
- **变更的原因**：
  - **问题**：在备份管理模块重构时，原有的 ConfigurationManagement.vue 文件被误删，导致用户无法在备份管理页面查看已备份的网络设备配置信息
  - **根因**：重构设计文档（docs/项目分析/前端页面设计.md）中没有明确说明要保留配置列表功能，导致重构时遗漏了该功能
  - **解决方案**：恢复配置列表功能并集成到备份管理页面的Tab中

---

## 变更 12：更新项目分析文档（反映配置管理页面丢失修复）

- **变更的日期**：2026-02-19 20:30
- **变更的文件**：
  - docs/项目分析/05-前端架构分析.md
  - docs/项目分析/前端页面设计.md
- **变更的位置**：
  - 05-前端架构分析.md：
    - 分析日期更新为2026-02-19（更新）
    - 添加文档修订记录
    - 更新目录结构（views目录）
    - 更新路由配置（添加备份管理相关）
    - 更新路由说明表格
    - 更新侧边栏菜单
    - 更新页面组件列表
  - 前端页面设计.md：
    - 设计日期更新为2026-02-19（更新）
    - 添加文档修订记录
    - 更新需求概述（添加配置列表）
    - 更新备份管理页面布局（添加配置列表Tab）
    - 更新Tab页签设计（添加配置列表页签）
    - 添加配置列表子页面设计说明
    - 更新路由设计（添加configs子路由）
    - 更新URL与Tab对应关系
    - 更新组件结构设计（添加ConfigList.vue）
    - 更新组件关系（添加配置列表Tab-pane）
    - 更新总结
    - 新增实施回顾（2026-02-19）
- **变更的内容**：
  1. 更新 05-前端架构分析.md：
     - 添加文档修订记录：2026-02-19的更新记录
     - 更新目录结构，反映当前的views目录结构（包含BackupManagement.vue和backup/子目录）
     - 更新路由配置，更新为当前的备份管理子路由结构
     - 更新路由说明表格，添加新的备份管理相关路由
     - 更新侧边栏菜单，从配置管理改为备份管理
     - 更新页面组件列表，添加备份管理和配置列表组件
  2. 更新 前端页面设计.md：
     - 添加文档修订记录：2026-02-14初始版本和2026-02-19更新版本
     - 更新设计目标，添加配置列表
     - 更新需求概述，添加配置列表说明
     - 更新备份管理页面布局，添加配置列表Tab
     - 更新Tab页签设计表格，添加配置列表页签
     - 新增4.6配置列表子页面设计说明
     - 更新路由设计，添加configs子路由
     - 更新URL与Tab对应关系，添加configs对应关系
     - 更新组件结构设计，添加ConfigList.vue
     - 更新组件关系，添加配置列表Tab-pane
     - 更新总结，添加配置列表
     - 新增13.实施回顾（2026-02-19），记录配置管理页面丢失问题的修复过程
- **变更的原因**：代码完成配置管理页面丢失问题修复后，需要同步更新项目分析文档，保持文档与代码的一致性，添加历史记录的修订，在文档中观测到项目演化的记录

---

## 变更 13：修复备份计划"上次执行"显示问题

- **变更的日期**：2026-02-20
- **变更的文件**：
  - `app/api/endpoints/configurations.py`
  - `app/services/backup_scheduler.py`
  - `docs/功能需求/前端/备份管理/备份计划/备份计划前端显示从未执行问题分析.md`
- **变更的位置**：
  - configurations.py：get_backup_schedules、get_backup_schedule、backup_now 函数
  - backup_scheduler.py：_execute_backup 函数
- **变更的内容**：
  1. 修改 get_backup_schedules 函数：
     - 添加 BackupExecutionLog 和 func 导入
     - 批量查询每个备份计划的最后执行时间（从 backup_execution_logs 表）
     - 填充 last_run_time 字段而不是硬编码为 None
  2. 修改 get_backup_schedule 函数：
     - 添加对单个计划的最后执行时间查询
  3. 修复 backup_now 函数：
     - 添加完整的执行日志记录
     - 生成唯一 task_id
     - 查找设备对应的备份计划
     - 记录执行开始和结束时间
     - 记录配置变化信息
     - 成功和失败都记录到 backup_execution_logs 表
     - 关联 schedule_id
  4. 修复 backup_scheduler.py：
     - 移除对不存在字段 last_run_time 的引用
- **变更的原因**：
  - **问题1**：备份计划列表中所有计划的"上次执行"字段都显示"从未执行"
    - **根因**：后端API返回的 last_run_time 被硬编码为 None
  - **问题2**：点击"立即备份"后，"上次执行"字段不会更新
    - **根因**：backup_now 函数没有记录执行日志到 backup_execution_logs 表，也没有关联 schedule_id
  - **问题3**：调度器执行备份时出现错误
    - **根因**：尝试更新不存在的 schedule.last_run_time 字段

---
