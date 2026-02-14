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
