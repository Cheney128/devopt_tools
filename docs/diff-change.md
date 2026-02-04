# 代码变更记录

## 变更记录格式

每次代码变更请按照以下格式记录：

### YYYY-MM-DD HH:MM:SS

**变更文件**：文件路径
**变更位置**：行号范围
**变更内容**：具体变更的代码内容
**变更原因**：变更的目的和原因

---

## 变更记录

### 2026-01-26 16:00:00

**变更文件**：docs/frontend-analysis.md
**变更位置**：1-326
**变更内容**：创建了前端页面深度调研文档，包含前端技术栈分析、项目结构与组织、核心页面设计与功能分析、组件设计与复用、API调用与数据交互、状态管理、性能考虑、代码质量与可维护性、改进建议等内容。
**变更原因**：根据用户需求，对前端页面进行深度调研并输出结果到docs目录下。

### 2026-01-27 10:00:00

**变更文件**：app/api/endpoints/command_templates.py
**变更位置**：74-191
**变更内容**：
- 统一了所有API端点的响应格式，包含success、message和data字段
- 添加了数据库模型到Pydantic模型的转换，使用CommandTemplate.model_validate()
- 修复了create_command_template、get_command_template、update_command_template、get_templates_by_vendor、get_templates_by_device_type函数
**变更原因**：修复命令模板创建时的序列化错误，确保所有API返回统一格式的响应

### 2026-01-27 10:00:00

**变更文件**：frontend/src/views/DeviceManagement.vue
**变更位置**：311-452
**变更内容**：
- 添加了templateFormLoading变量定义
- 完善了handleSubmitTemplateForm函数的错误处理逻辑
- 添加了加载状态管理，在表单提交过程中显示加载状态
- 为API错误添加了用户友好的错误提示
**变更原因**：修复命令模板创建时的错误处理问题，提高用户体验

### 2026-01-27 12:20:00

**变更文件**：frontend/src/views/DeviceManagement.vue
**变更位置**：509-519
**变更内容**：
- 修改了loadCommandTemplates函数，将数据解析逻辑从result.templates改为result.data.items
**变更原因**：修复数据结构不匹配问题，正确解析后端返回的数据格式

### 2026-01-27 12:20:00

**变更文件**：app/api/endpoints/command_templates.py
**变更位置**：9-231
**变更内容**：
- 为数据库模型添加了别名CommandTemplateModel以避免命名冲突
- 在get_command_templates函数中添加了数据库模型到Pydantic模型的转换
- 更新了所有函数中的CommandTemplate引用为CommandTemplateModel
**变更原因**：修复后端序列化错误，确保所有API返回正确的Pydantic模型格式

### 2026-02-03 15:00:00

**变更文件**：docker-compose.yml
**变更位置**：14-70
**变更内容**：
- 移除了OXIDIZED_URL环境变量
- 移除了oxidized服务依赖
- 删除了整个oxidized服务定义（包含镜像、端口、卷、环境变量等配置）
- 移除了oxidized_config和oxidized_data数据卷定义
**变更原因**：将oxidized从系统中解耦，网络设备备份由本系统结合Git完成，实现网络设备备份+版本管理功能

### 2026-02-03 15:00:00

**变更文件**：README.md
**变更位置**：39-470
**变更内容**：
- 移除了"5. 与Oxidized集成"功能模块描述
- 从基础设施表格中移除了Oxidized条目
- 更新了系统架构图，移除了Oxidized相关组件
- 更新了数据流图，移除了Oxidized平台相关流程
- 从项目结构中移除了oxidized_service.py
- 更新了部署架构图，移除了Oxidized服务
- 更新了服务依赖关系图
- 从环境配置示例中移除了OXIDIZED_URL
**变更原因**：配合oxidized解耦，更新项目文档以反映新的系统架构

### 2026-02-03 15:00:00

**变更文件**：app/config.py
**变更位置**：24-26
**变更内容**：
- 移除了OXIDIZED_URL配置项及其默认值
**变更原因**：移除oxidized相关配置，系统不再依赖oxidized服务

### 2026-02-03 15:00:00

**变更文件**：app/services/__init__.py
**变更位置**：2-13
**变更内容**：
- 移除了oxidized_service的导入语句
- 从__all__列表中移除了OxidizedService和get_oxidized_service
**变更原因**：移除oxidized服务模块的导出

### 2026-02-03 15:00:00

**变更文件**：app/services/oxidized_service.py
**变更位置**：1-128
**变更内容**：
- 删除了整个oxidized_service.py文件
**变更原因**：oxidized服务已不再需要，系统直接使用Git进行配置版本管理

### 2026-02-03 15:00:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：16-274
**变更内容**：
- 移除了oxidized_service的导入
- 删除了/get/oxidized/status端点
- 删除了/post/oxidized/sync端点
- 删除了/get/oxidized/{device_id}端点
**变更原因**：移除所有与oxidized相关的API接口

### 2026-02-03 15:00:00

**变更文件**：app/schemas/schemas.py
**变更位置**：462-474
**变更内容**：
- 删除了OxidizedStatus模型
- 删除了OxidizedSyncResult模型
**变更原因**：移除oxidized相关的数据模型

### 2026-02-03 15:00:00

**变更文件**：tests/unit/test_configurations.py
**变更位置**：1-86
**变更内容**：
- 移除了oxidized_service的导入
- 删除了test_get_oxidized_status测试函数
- 删除了test_sync_with_oxidized测试函数
- 删除了test_get_config_from_oxidized测试函数
**变更原因**：移除与oxidized相关的单元测试

### 2026-02-03 15:00:00

**变更文件**：docs/project_analysis.md
**变更位置**：13-495
**变更内容**：
- 将"与现有系统（如Oxidized）集成"改为"通过Git实现配置版本管理"
- 从技术栈表格中将Oxidized替换为Git
- 更新配置管理模块描述，将"与Oxidized集成获取配置备份"改为"Git集成实现配置版本控制"
- 从架构图中移除了Oxidized平台
- 从配置备份流程图中移除了Oxidized平台
- 更新项目优势描述
**变更原因**：更新项目分析文档，反映系统不再依赖oxidized的新架构

### 2026-02-03 15:00:00

**变更文件**：docs/项目分析/06-部署架构分析.md
**变更位置**：38-462
**变更内容**：
- 从整体架构图中移除了Oxidized服务
- 从服务依赖关系图中移除了Oxidized
- 从Backend服务配置中移除了OXIDIZED_URL环境变量和oxidized依赖
- 删除了整个2.1.4 Oxidized服务章节
- 从网络和卷配置中移除了oxidized_config和oxidized_data
- 从环境变量示例中移除了OXIDIZED_URL
- 从配置加载机制中移除了OXIDIZED_URL
- 从备份策略中移除了Oxidized配置和数据备份
- 将微服务架构从4个服务改为3个服务
**变更原因**：更新部署架构文档，反映移除oxidized后的新部署架构

### 2026-02-03 15:00:00

**变更文件**：docs/项目分析/01-项目架构分析.md
**变更位置**：58-126
**变更内容**：
- 从整体架构图中移除了Oxidized组件
- 从集成层描述中移除了"配置备份：Oxidized (可选)"
- 从后端模块结构中移除了oxidized_service.py
**变更原因**：更新项目架构文档，反映移除oxidized后的新架构

### 2026-02-03 15:00:00

**变更文件**：docs/项目分析/02-技术栈分析.md
**变更位置**：28-32
**变更内容**：
- 从技术栈总览图中将Oxidized替换为Git
**变更原因**：更新技术栈分析文档，反映使用Git替代Oxidized进行配置版本管理

### 2026-02-03 16:30:00

**变更文件**：docker-compose.yml
**变更位置**：91
**变更内容**：
- 将 MySQL 初始化脚本从 `./scripts/init_db.py` 改为 `./scripts/init_db.sql`
**变更原因**：MySQL 官方镜像的 `/docker-entrypoint-initdb.d/` 目录只支持 `.sh`、`.sql`、`.sql.gz` 格式，Python 脚本无法被执行

### 2026-02-03 16:30:00

**变更文件**：scripts/init_db.sql
**变更位置**：1-145
**变更内容**：
- 创建了新的 SQL 初始化脚本，包含所有数据库表的创建语句
- 包括 devices、ports、vlans、inspections、configurations、mac_addresses、device_versions、backup_schedules、command_templates、command_history、git_configs 等表
**变更原因**：替代原有的 Python 初始化脚本，使 MySQL 容器启动时能自动创建数据库表结构

### 2026-02-03 16:30:00

**变更文件**：frontend/Dockerfile.frontend
**变更位置**：12-15
**变更内容**：
- 移除了 `package-lock.json` 的复制
- 将 `npm ci --only=production` 改为 `npm install`
**变更原因**：项目没有 package-lock.json 文件，使用 npm install 更兼容

### 2026-02-03 16:30:00

**变更文件**：frontend/Dockerfile.frontend
**变更位置**：37-48
**变更内容**：
- 移除了创建非 root 用户的相关代码
- 移除了 `USER nginxuser` 指令
- 简化为只创建必要的目录
**变更原因**：Nginx 使用非 root 用户可能导致权限问题，简化配置以提高兼容性

### 2026-02-04 09:43:26

**变更文件**：docs/功能需求/前端/登录与用户管理模块实施方案-gpt-5.2.md
**变更位置**：1-443
**变更内容**：
- 新增《登录功能模块与用户管理功能模块实施方案（gpt-5.2）》
- 将后端接口约定明确为“沿用现有接口风格”：成功直接返回业务数据；失败使用HTTP状态码+detail
- 对前端鉴权闭环（Axios拦截器+路由守卫+菜单渲染）与接口形状进行对齐说明
**变更原因**：在不重构现有后端响应结构的前提下，给出可落地、与现有代码一致的登录与用户管理实施方案，降低集成成本与风格割裂风险

### 2026-02-04 10:00:00

**变更文件**：requirements.txt
**变更位置**：17-20
**变更内容**：
- 新增认证相关依赖：python-jose[cryptography]==3.3.0、passlib[bcrypt]==1.7.4、pillow==10.1.0
**变更原因**：支持JWT Token生成验证、密码哈希加密、验证码图片生成

### 2026-02-04 10:00:00

**变更文件**：app/models/user_models.py
**变更位置**：1-106
**变更内容**：
- 新增User模型：包含用户名、密码哈希、昵称、邮箱、手机号、状态、登录安全字段等
- 新增Role模型：角色管理
- 新增Permission模型：权限管理
- 新增CaptchaRecord模型：验证码记录
- 新增user_roles和role_permissions关联表
**变更原因**：建立用户认证与权限管理的数据模型基础

### 2026-02-04 10:00:00

**变更文件**：app/models/__init__.py
**变更位置**：8-43
**变更内容**：
- 导入User、Role、Permission、CaptchaRecord等用户相关模型
- 添加__all__导出列表
**变更原因**：使外部模块可以方便地导入用户相关模型

### 2026-02-04 10:00:00

**变更文件**：app/core/security.py
**变更位置**：1-133
**变更内容**：
- 实现密码哈希生成和验证（bcrypt）
- 实现JWT Token创建和解码
- 实现验证码生成和图片创建功能
**变更原因**：提供认证相关的安全工具函数

### 2026-02-04 10:00:00

**变更文件**：app/schemas/user_schemas.py
**变更位置**：1-143
**变更内容**：
- 定义Role相关Schema
- 定义User相关Schema（创建、更新、响应）
- 定义认证相关Schema（登录请求/响应、验证码响应、密码修改）
**变更原因**：定义用户认证和管理模块的数据验证和序列化格式

### 2026-02-04 10:00:00

**变更文件**：app/api/deps.py
**变更位置**：1-108
**变更内容**：
- 实现get_current_user依赖：从JWT Token获取当前用户
- 实现check_admin_permission依赖：检查管理员权限
- 实现require_roles依赖工厂：角色权限检查
**变更原因**：提供可复用的认证和授权依赖项

### 2026-02-04 10:00:00

**变更文件**：app/api/endpoints/auth.py
**变更位置**：1-195
**变更内容**：
- 实现GET /auth/captcha：获取验证码
- 实现POST /auth/login：用户登录（含验证码验证、登录失败锁定）
- 实现POST /auth/logout：用户登出
- 实现GET /auth/me：获取当前用户信息
**变更原因**：提供用户认证相关的API端点

### 2026-02-04 10:00:00

**变更文件**：app/api/endpoints/users.py
**变更位置**：1-287
**变更内容**：
- 实现GET /users：获取用户列表（分页、搜索、筛选）
- 实现POST /users：创建用户
- 实现GET /users/me：获取当前用户个人信息
- 实现PUT /users/me：更新个人信息
- 实现PUT /users/me/password：修改密码
- 实现GET /users/{id}：获取指定用户
- 实现PUT /users/{id}：更新用户信息
- 实现POST /users/{id}/reset-password：重置密码
- 实现DELETE /users/{id}：删除用户
**变更原因**：提供用户管理相关的API端点

### 2026-02-04 10:00:00

**变更文件**：app/api/__init__.py
**变更位置**：6-22
**变更内容**：
- 导入auth和users路由模块
- 注册/auth和/users路由
**变更原因**：将认证和用户管理API注册到主路由

### 2026-02-04 10:00:00

**变更文件**：scripts/init_auth_data.py
**变更位置**：1-132
**变更内容**：
- 创建初始化脚本，用于创建用户认证相关表
- 初始化admin和user角色
- 创建默认管理员账号（admin/admin123）
**变更原因**：提供一键初始化认证数据的脚本

### 2026-02-04 10:00:00

**变更文件**：frontend/src/stores/authStore.js
**变更位置**：1-128
**变更内容**：
- 创建Pinia Store管理认证状态
- 实现token存储、用户信息管理
- 实现登录、登出、获取验证码等操作
**变更原因**：前端状态管理，统一管理用户认证状态

### 2026-02-04 10:00:00

**变更文件**：frontend/src/api/auth.js
**变更位置**：1-45
**变更内容**：
- 定义authApi：登录、登出、获取验证码、获取当前用户
- 定义userApi：用户列表、创建、更新、删除、重置密码、个人中心相关接口
**变更原因**：封装认证和用户管理相关的API调用

### 2026-02-04 10:00:00

**变更文件**：frontend/src/api/index.js
**变更位置**：1-209
**变更内容**：
- 添加请求拦截器：自动附加Authorization Bearer Token
- 添加响应拦截器：统一处理401/403/404/409/422/500错误，自动跳转登录页
**变更原因**：实现全局API请求和响应处理，支持认证和错误处理

### 2026-02-04 10:00:00

**变更文件**：frontend/src/views/LoginView.vue
**变更位置**：1-256
**变更内容**：
- 创建登录页面，包含用户名、密码、验证码输入
- 实现验证码刷新功能
- 实现表单验证和登录逻辑
**变更原因**：提供用户登录界面

### 2026-02-04 10:00:00

**变更文件**：frontend/src/views/UserManagement.vue
**变更位置**：1-495
**变更内容**：
- 创建用户管理页面
- 实现用户列表展示（分页、搜索、筛选）
- 实现新增、编辑、删除用户功能
- 实现重置密码功能
**变更原因**：管理员管理用户的界面

### 2026-02-04 10:00:00

**变更文件**：frontend/src/views/ProfileView.vue
**变更位置**：1-303
**变更内容**：
- 创建个人中心页面
- 实现个人信息查看和修改
- 实现密码修改功能
**变更原因**：用户管理个人信息的界面

### 2026-02-04 10:00:00

**变更文件**：frontend/src/router/index.js
**变更位置**：1-128
**变更内容**：
- 添加/login路由
- 添加/users路由（需要管理员权限）
- 添加/profile路由
- 实现路由守卫：未登录跳转登录页、已登录访问登录页跳转首页、权限检查
**变更原因**：实现前端路由鉴权

### 2026-02-04 10:00:00

**变更文件**：frontend/src/App.vue
**变更位置**：1-240
**变更内容**：
- 集成Auth Store
- 添加用户信息显示（昵称、角色）
- 添加退出登录功能
- 根据角色动态显示菜单（管理员显示用户管理）
- 未登录时隐藏侧边栏和顶部导航
**变更原因**：集成用户认证状态到主应用布局
