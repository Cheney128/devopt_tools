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
- 将后端接口约定明确为"沿用现有接口风格"：成功直接返回业务数据；失败使用HTTP状态码+detail
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

### 2026-02-04 11:20:00

**变更文件**：frontend/src/api/index.js
**变更位置**：1-13
**变更内容**：
- 新增 resolveApiBaseUrl(env) 方法：优先使用 VITE_API_BASE_URL，默认回退到 /api/v1
- Axios 实例 baseURL 从硬编码 localhost 改为 resolveApiBaseUrl()
**变更原因**：兼容本地开发与 Docker 生产部署，避免浏览器/容器内 localhost 指向错误导致验证码与 API 异常

### 2026-02-04 11:20:00

**变更文件**：frontend/vite.config.js
**变更位置**：1-26
**变更内容**：
- 增加 dev server 代理：/api → VITE_DEV_PROXY_TARGET（默认 http://localhost:8000）
**变更原因**：在开发环境使用相对路径 /api/v1 时，通过 Vite 代理把请求转发到本地后端，恢复验证码与登录联调

### 2026-02-04 11:20:00

**变更文件**：frontend/test/apiBaseUrl.test.js
**变更位置**：1-13
**变更内容**：
- 新增 resolveApiBaseUrl 的回归测试（环境变量优先、默认回退）
**变更原因**：防止后续改动再次引入硬编码 baseURL 或默认值错误

### 2026-02-04 11:20:00

**变更文件**：frontend/test/DeviceManagement.test.js
**变更位置**：124-182
**变更内容**：
- 更新 executeCommand / batchExecuteCommand 的断言入参，匹配当前 API 额外参数（variables/templateId）
**变更原因**：修复前端测试与实际函数签名不一致导致的用例失败，确保测试套件可稳定运行

### 2026-02-04 11:20:00

**变更文件**：frontend/src/views/InspectionManagement.vue
**变更位置**：1-5，121，195
**变更内容**：
- 将未导出的 PlayCircle 图标替换为 VideoPlay
**变更原因**：修复生产构建阶段 Rollup 报错，确保 npm run build 可通过

### 2026-02-04 14:30:00

**变更文件**：docker/.dockerignore
**变更位置**：1-70
**变更内容**：
- 新增docker/.dockerignore文件
- 排除所有.env文件，防止进入镜像
- 排除Python虚拟环境、IDE目录、缓存目录等
- 排除Git相关文件和Docker相关文件
**变更原因**：防止.env文件被复制到Docker镜像中，避免配置覆盖问题

### 2026-02-04 14:30:00

**变更文件**：docker/nginx.conf
**变更位置**：1-61
**变更内容**：
- 新增Nginx配置文件
- 配置前端静态资源服务（/unified-app/frontend/dist）
- 配置API反向代理到后端（127.0.0.1:8000）
- 配置健康检查端点（/health）
**变更原因**：为前后端合一部署提供Nginx网关配置

### 2026-02-04 14:30:00

**变更文件**：docker/supervisord.conf
**变更位置**：1-32
**变更内容**：
- 新增Supervisor配置文件
- 配置backend服务：uvicorn启动，绑定127.0.0.1:8000，2个worker
- 配置nginx服务：Nginx前台运行
- 配置进程组管理
**变更原因**：使用Supervisor管理合一容器内的多个进程

### 2026-02-04 14:30:00

**变更文件**：docker/entrypoint.sh
**变更位置**：1-28
**变更内容**：
- 新增容器入口脚本
- 创建日志目录并设置权限
- 打印环境信息（DEPLOY_MODE、DATABASE_URL等）
- 启动Supervisor
**变更原因**：提供容器启动时的初始化和日志输出

### 2026-02-04 14:30:00

**变更文件**：docker/mysql-init.sql
**变更位置**：1-16
**变更内容**：
- 新增MySQL初始化脚本
- 创建switch_manage数据库
- 授予应用用户权限
**变更原因**：DB容器首次启动时自动初始化数据库

### 2026-02-04 14:30:00

**变更文件**：docker/Dockerfile.unified
**变更位置**：1-95
**变更内容**：
- 新增合一部署Dockerfile
- 阶段1：前端构建（Node.js）
- 阶段2：基础镜像准备（Python + Nginx + Supervisor）
- 阶段3：Python依赖安装
- 阶段4：最终镜像组装
- 暴露80端口，配置健康检查
**变更原因**：构建前后端合一的Docker镜像

### 2026-02-04 14:30:00

**变更文件**：docker-compose.unified.yml
**变更位置**：1-79
**变更内容**：
- 新增合一部署Docker Compose配置
- app服务：合一容器，仅暴露80端口，连接DB容器
- db服务：MySQL 5.7，不对外映射端口
- 配置健康检查、资源限制、网络隔离
**变更原因**：实现前后端合一 + 独立DB容器的部署架构

### 2026-02-04 14:30:00

**变更文件**：app/config.py
**变更位置**：1-37
**变更内容**：
- 修改load_dotenv()调用逻辑
- 合一部署模式（DEPLOY_MODE=unified）：不加载.env文件
- 非合一部署模式：使用override=False避免覆盖环境变量
**变更原因**：修复配置优先级问题，确保环境变量优先于.env文件

### 2026-02-04 14:30:00

**变更文件**：app/main.py
**变更位置**：1-90
**变更内容**：
- 添加import os
- 根据DEPLOY_MODE调整CORS配置
- 在startup_event中打印DATABASE_URL和DEPLOY_MODE
- 隐藏密码部分的安全处理
**变更原因**：支持合一部署模式，便于排查配置来源问题

### 2026-02-04 16:00:00

**变更文件**：docker-compose.unified.yml
**变更位置**：44-67
**变更内容**：
- 修复db服务健康检查密码不匹配问题：将`-p${MYSQL_ROOT_PASSWORD:-rootpassword}`改为`-p[OylKbYLJf*Hx((4dEIf]`
- 统一环境变量语法格式：将`key: "value"`格式改为`key=value`格式
- 添加MARIADB_DATABASE环境变量：支持自动创建数据库
- 添加TZ时区配置：设置Asia/Shanghai时区
**变更原因**：修复从MySQL 5.7迁移到MariaDB 11后的配置问题，确保健康检查正常工作，统一配置格式

### 2026-02-04 17:30:00

**变更文件**：docker/Dockerfile.unified
**变更位置**：34-36
**变更内容**：
- 在apt-get install中添加字体包：`fonts-dejavu-core`
- 修改前：`nginx supervisor net-tools curl git`
- 修改后：`nginx supervisor net-tools curl git fonts-dejavu-core`
**变更原因**：修复Docker环境前端验证码显示异常问题。验证码生成依赖PIL库加载字体文件，Docker容器缺少字体导致验证码图片生成失败。

### 2026-02-04 17:30:00

**变更文件**：app/core/security.py
**变更位置**：102-120
**变更内容**：
- 优化字体加载逻辑，添加多个字体路径尝试
- 修改前：仅尝试`arial.ttf`和`/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- 修改后：按顺序尝试多个字体路径：DejaVuSans、LiberationSans、Arial，最后使用默认字体
**变更原因**：提高字体加载的兼容性，确保即使某个字体包安装失败，也能尝试其他字体路径，避免验证码生成完全失败。

### 2026-02-04 18:00:00

**变更文件**：docs/功能需求/前后端合一部署/前后端合一部署方案-评审文档.md
**变更位置**：1-130
**变更内容**：
- 新增《前后端合一部署方案-评审文档》，对合一部署方案的可执行性、安全性与可运维性进行评审
- 给出阻断项（配置优先级、DB 同容器初始化机制不匹配、Compose 资源限制不生效等）与可落地的修改建议
- 建议优先落地"单容器合并前后端、DB 外置/独立"的变体，满足仅暴露前端端口的目标
**变更原因**：响应"前后端合一部署"需求，输出可执行的评审意见与风险控制建议，降低实施返工与线上风险

### 2026-02-04 19:00:00

**变更文件**：docs/功能需求/前后端合一部署/前后端合一部署方案.md
**变更位置**：1-1070
**变更内容**：
- 根据评审意见全面修订方案文档
- 将方案拆分为两个可选落地形态：
  - 形态1（推荐）：Nginx + Backend（单容器），DB 外置/独立容器
  - 形态2（备选）：Nginx + Backend + DB（单容器），仅适用于演示/边缘设备
- 修正配置优先级问题：
  - 新增 `.dockerignore` 排除所有 `.env` 文件
  - 修改 `config.py` 使用 `load_dotenv(override=False)` 并添加 `DEPLOY_MODE` 判断
- 修正 Docker Compose 资源限制：使用 `mem_limit` 和 `cpus` 替代 `deploy.resources`
- 修正后端启动模式：禁用 `--reload`，使用 `--workers 2` 生产参数
- 修正前端API路径章节：确认现状已满足，无需修改
- 更新验证清单：增加配置优先级验证、安全验证、性能验证
- 新增风险清单与验收标准表格
**变更原因**：按照评审意见修订方案，确保配置优先级修复、资源限制生效、生产参数正确，优先落地形态1（前后端合一+独立DB容器）

### 2026-02-04 19:30:00

**变更文件**：docs/功能需求/前后端合一部署/前后端合一部署方案.md
**变更位置**：1-889
**变更内容**：
- 移除方案中的形态2（前后端DB合一单容器）相关内容
- 简化方案为单一架构：前后端合一 + 独立DB容器
- 删除形态2的架构图、Supervisor配置、入口脚本等内容
- 更新章节编号和文件结构说明
- 简化部署实施步骤，移除形态2相关文件创建说明
**变更原因**：根据要求，仅保留推荐的单一架构方案，移除备选的形态2，使方案更加简洁明确

### 2026-02-05 10:00:00

**变更文件**：app/models/__init__.py
**变更位置**：16-30
**变更内容**：
- 恢复了MySQL连接池参数配置，移除了SQLite条件判断
- 将数据库引擎配置改回统一使用连接池参数的配置
**变更原因**：根据用户要求，使用原始环境变量文件中的MySQL数据库连接信息，需要恢复MySQL连接池参数配置

### 2026-02-05 10:00:00

**变更文件**：frontend/.env
**变更位置**：1
**变更内容**：
- 创建了前端环境配置文件，设置了正确的API基础URL
- 配置内容：VITE_API_BASE_URL=http://localhost:8000/api/v1
**变更原因**：配置前端正确的后端API地址，确保前端能够正确连接到后端服务

### 2026-02-05 09:25:00

**变更文件**：app/config.py
**变更位置**：31-36
**变更内容**：
- 修改CORS配置，将 `BACKEND_CORS_ORIGINS` 从 `["*"]` 改为明确指定前端地址 `["http://localhost:5173", "http://localhost:3000"]`
- 修改前：`self.BACKEND_CORS_ORIGINS = ["*"]`
- 修改后：
```python
self.BACKEND_CORS_ORIGINS = [
    "http://localhost:5173",  # Vite开发服务器
    "http://localhost:3000",  # 备用开发端口
]
```
**变更原因**：修复CORS配置违规问题。当 `allow_credentials=True` 时，`Access-Control-Allow-Origin` 不能使用通配符 `*`，必须明确指定允许的源。这是导致前端登录时报错 `net::ERR_FAILED` 的根本原因。

### 2026-02-05 11:26

**变更文件**：frontend/.env
**变更位置**：VITE_API_BASE_URL
**变更内容**：从 "http://localhost:8000/api/v1" 修改为 "/api/v1"
**变更原因**：修复前端登录报错问题，使请求通过Vite代理转发，避免跨域

### 2026-02-05 14:20

**变更文件**：frontend/.env
**变更位置**：新建文件
**变更内容**：创建前端环境配置文件，内容：VITE_API_BASE_URL=/api/v1
**变更原因**：修复前端登录报错问题，原.env文件缺失，只有.env.bak备份文件

### 2026-02-05 14:25

**变更文件**：系统环境变量
**变更位置**：NO_PROXY/no_proxy
**变更内容**：设置 NO_PROXY=localhost,127.0.0.1,::1 和 no_proxy=localhost,127.0.0.1,::1
**变更原因**：修复前端登录报错问题。系统存在http_proxy代理设置，导致请求被Squid代理拦截返回503错误，需要设置NO_PROXY排除本地地址

### 2026-02-05 15:40

**变更文件**：app/core/security.py
**变更位置**：19-26
**变更内容**：
- 修改前：`pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")`
- 修改后：
```python
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
    default="pbkdf2_sha256"
)
```
**变更原因**：修复登录失败问题。数据库中存储的密码哈希可能是使用bcrypt方案生成的，但当前代码只配置了pbkdf2_sha256方案，导致passlib无法识别旧密码哈希，抛出UnknownHashError错误。修改后同时支持两种方案，保持向后兼容性。

### 2026-02-05 16:00:00

**变更文件**：app/services/excel_service.py
**变更位置**：1-516（完整重构）
**变更内容**：
根据《批量上传失效-优化修复方案-v3.md》对excel_service.py进行全面重构，主要变更包括：

1. **validate_device_data函数重构**（v3优化1：端口验证位置调整）
   - 返回值从`List[Dict]`改为`Tuple[List, List]`，返回验证通过设备和错误列表
   - 新增IP地址格式验证（使用标准库ipaddress）
   - 端口范围验证移至验证阶段，超出范围时记录警告并自动修正为22
   - Telnet端口自动修正时记录警告信息
   - 新增状态值映射（中文->英文：活跃->active等）
   - 新增厂商值映射（中文->英文：华为->Huawei等）
   - 改进必填字段验证，精确到行号并记录具体缺失字段

2. **import_devices_from_excel函数重构**（v3优化2和3）
   - 批量查询已存在设备，优化N+1问题
   - 新增分批插入策略（每批50条），批量插入失败时回退到逐条插入定位问题
   - 批量更新事务边界细化，记录更新的字段列表和原始值
   - 区分"已更新"和"无变化跳过"两种情况
   - 统一事务提交策略，确保数据一致性

3. **generate_device_template函数增强**（v3优化4：密码安全提示）
   - 表头改为中文（主机名*、IP地址*、厂商*等）
   - 新增2条示例数据（华为和思科设备）
   - 新增"填写说明"工作表，包含字段说明和示例
   - 新增安全提示列和独立安全提示区域
   - 密码示例改为临时密码（TempPass123!）并添加安全警告

**变更原因**：修复"批量导入完成:0成功,0跳过,0失败"核心问题，实现详细的错误报告机制，支持中英文字段值映射，保证大数据量导入性能，提升系统安全性和用户体验。基于评审文档v3（评分9.5/10）实施。

### 2026-02-05 16:30:00

**变更文件**：.env
**变更位置**：10
**变更内容**：
- 修改 DEBUG=True
**变更原因**：开启调试模式，便于开发和排查问题

### 2026-02-05 16:30:00

**变更文件**：app/config.py
**变更位置**：1-37
**变更内容**：
- 配置文件修改，支持DEBUG模式
**变更原因**：配合环境变量的DEBUG设置，调整应用配置

### 2026-02-05 16:30:00

**变更文件**：docs/decision-log.md
**变更位置**：1-100
**变更内容**：
- 更新决策日志，记录最近的系统配置和功能变更
**变更原因**：按照决策逻辑要求，记录所有重要决策

### 2026-02-05 16:30:00

**变更文件**：docs/diff-change.md
**变更位置**：739-780
**变更内容**：
- 添加最新的变更记录，包括.env、app/config.py等文件的修改
**变更原因**：按照代码变更记录要求，记录每一次代码变更的详细信息

### 2026-02-05 17:00:00

**变更文件**：app/services/excel_service.py
**变更位置**：1-516
**变更内容**：
- 重构validate_device_data函数：返回验证通过设备和错误列表，新增IP地址格式验证，端口范围验证移至验证阶段，Telnet端口自动修正，新增状态和厂商值映射，改进必填字段验证
- 重构import_devices_from_excel函数：批量查询已存在设备，新增分批插入策略，批量更新事务边界细化，区分"已更新"和"无变化跳过"，统一事务提交策略
- 增强generate_device_template函数：表头改为中文，新增示例数据，新增"填写说明"工作表，新增安全提示列和安全提示区域，密码示例改为临时密码
**变更原因**：修复"批量导入完成:0成功,0跳过,0失败"核心问题，实现详细的错误报告机制，支持中英文字段值映射，保证大数据量导入性能，提升系统安全性和用户体验

### 2026-02-05 17:00:00

**变更文件**：frontend/Dockerfile.frontend
**变更位置**：1-41
**变更内容**：
- 更新Node.js版本从16到20
- 添加npm镜像源设置（可通过构建参数覆盖）
- 移除package-lock.json的复制
- 修改npm install命令
- 添加构建参数VITE_API_BASE_URL
- 更新Nginx版本到1.25
- 添加curl用于健康检查
- 确保Nginx可以正常运行的目录权限设置
- 将暴露端口从80改为8080
- 添加健康检查配置
**变更原因**：优化前端Docker构建流程，支持构建参数配置，提高容器健康检查能力，适应新的端口配置

### 2026-02-05 17:00:00

**变更文件**：tests/test_excel_import_v3.py
**变更位置**：1-297
**变更内容**：
- 创建了新的测试文件，包含validate_device_data、generate_device_template和import_devices_from_excel函数的详细测试
- 测试了正常数据验证、缺少必填字段验证、IP地址格式验证、端口范围验证、Telnet端口自动修正、中文列名映射等场景
- 测试了模板生成功能，包括工作表验证、表头验证、示例数据验证、安全提示验证等
- 测试了导入设备功能的Mock测试，验证批量导入逻辑
**变更原因**：为重构后的Excel导入功能提供完整的测试覆盖，确保功能正确性和稳定性
