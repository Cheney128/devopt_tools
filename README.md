# 交换机批量管理与巡检系统

## 项目简介

本项目是一个用于批量管理和巡检交换机的Web应用，旨在简化网络设备的管理流程，提高网络运维效率。系统支持批量配置交换机基本信息、端口信息、VLAN信息等，同时提供批量巡检功能，实时获取交换机的运行状态和性能指标。

## 核心功能

### 1. 批量管理交换机
- 配置交换机基本信息（主机名、IP地址、厂商、型号等）
- 管理端口信息（状态、速率、描述等）
- 配置VLAN信息
- 批量导入/导出设备信息
- 设备分组管理
- 单个/批量命令执行
- 命令模板管理

### 2. 批量巡检交换机
- 获取交换机运行状态
- 采集性能指标（CPU、内存使用率等）
- 检查端口状态
- 生成巡检报告
- 异常告警通知

### 3. 配置管理
- 直接设备配置采集（通过Netmiko）
- 配置版本管理（自动版本递增）
- 配置差异比较
- Git集成（自动推送到GitHub/GitLab）
- 定时备份任务

### 4. 设备信息采集
- 版本信息采集
- 序列号采集
- 接口信息采集
- MAC地址表采集
- 批量信息采集

## 技术栈

### 后端技术栈

| 技术/框架 | 版本 | 用途 | 优势 |
|----------|------|------|------|
| Python | 3.9+ | 开发语言 | 简洁、易读、丰富的库支持 |
| FastAPI | 0.104.1 | Web框架 | 高性能、异步支持、自动生成API文档 |
| Uvicorn | 0.24.0 | ASGI服务器 | 基于uvloop的高性能异步服务器 |
| SQLAlchemy | 1.4.51 | ORM框架 | 强大的数据库抽象、支持多种数据库 |
| PyMySQL | 1.1.0 | MySQL驱动 | 纯Python实现，跨平台兼容 |
| Netmiko | 4.1.0 | 网络设备连接 | 支持多种网络设备厂商、简化SSH连接 |
| Paramiko | 3.4.0 | SSH协议库 | 完整的SSHv2协议实现 |
| Pydantic | 2.5.2 | 数据验证 | 强大的数据验证、类型提示支持 |
| GitPython | 3.1.43 | Git操作 | 成熟的Git仓库操作库 |
| python-dotenv | 1.0.0 | 环境变量管理 | 简化配置管理、支持不同环境配置 |

### 前端技术栈

| 技术/框架 | 版本 | 用途 | 优势 |
|----------|------|------|------|
| Vue.js | 3.5.24 | 前端框架 | 响应式设计、组件化开发、性能优良 |
| Element Plus | 2.13.1 | UI组件库 | 丰富的组件、美观的设计、良好的文档 |
| Axios | 1.13.2 | HTTP客户端 | 简洁的API、支持拦截器、并发请求 |
| Vue Router | 4.6.4 | 路由管理 | 灵活的路由配置、支持嵌套路由 |
| Pinia | 3.0.4 | 状态管理 | 简洁的API、TypeScript支持、模块化设计 |
| Vite | 7.2.4 | 构建工具 | 快速的冷启动、即时的热模块替换 |
| Vitest | 4.0.18 | 测试框架 | 极速的单元测试框架 |
| highlight.js | 11.11.1 | 代码高亮 | 支持多种语言、易于集成 |

### 基础设施

| 技术 | 版本 | 用途 | 优势 |
|------|------|------|------|
| MySQL | 5.7+ | 数据库 | 稳定可靠、广泛使用、支持事务 |
| Docker | - | 容器化部署 | 简化部署、环境一致性、易于扩展 |
| Nginx | - | Web服务器 | 高并发、低内存消耗、反向代理 |

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户层 (User Layer)                             │
│                         浏览器 / Web Client                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端层 (Frontend Layer)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Vue.js 3   │  │ Element Plus │  │  Vue Router  │  │    Pinia     │     │
│  │   (框架)     │  │  (UI组件)    │  │   (路由)     │  │  (状态管理)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │ HTTP/REST API
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              后端层 (Backend Layer)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI (Web框架)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────┐  │
│  │   API路由    │   业务逻辑   │   数据模型   │   数据验证   │  服务层   │  │
│  │  (endpoints) │  (services)  │   (models)   │  (schemas)   │          │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┴──────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    数据层 (Data)      │  │   设备层 (Devices)    │  │   集成层 (Integration) │
│  ┌────────────────┐  │  │  ┌────────────────┐  │  │  ┌────────────────┐  │
│  │    MySQL 5.7   │  │  │  │   Netmiko      │  │  │  │    Git仓库      │  │
│  │   (数据库)      │  │  │  │  (SSH/Telnet)  │  │  │  │(GitHub/GitLab) │  │
│  └────────────────┘  │  │  └────────────────┘  │  │  └────────────────┘  │
│  ┌────────────────┐  │  │  ┌────────────────┐  │  │                      │
│  │   SQLAlchemy   │  │  │  │   Paramiko     │  │  │                      │
│  │    (ORM)       │  │  │  │   (SSH协议)     │  │  │                      │
│  └────────────────┘  │  │  └────────────────┘  │  │                      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### 数据流图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端界面
    participant Backend as 后端API
    participant DB as MySQL数据库
    participant Switch as 交换机设备

    User->>Frontend: 访问管理界面
    Frontend->>Backend: 请求设备列表
    Backend->>DB: 查询设备信息
    DB-->>Backend: 返回设备数据
    Backend-->>Frontend: 展示设备列表

    User->>Frontend: 执行批量操作
    Frontend->>Backend: 发送操作请求
    Backend->>Switch: 执行设备操作
    Switch-->>Backend: 返回操作结果
    Backend->>DB: 更新设备状态
    Backend-->>Frontend: 展示操作结果

    User->>Frontend: 执行巡检任务
    Frontend->>Backend: 发送巡检请求
    Backend->>Switch: 采集设备信息
    Switch-->>Backend: 返回设备状态
    Backend->>DB: 存储巡检结果
    Backend-->>Frontend: 展示巡检报告
```

## 项目结构

### 整体目录结构

```
switch_manage/
├── app/                    # 后端应用代码
│   ├── api/                # API路由定义
│   │   ├── __init__.py     # 路由聚合
│   │   └── endpoints/      # 具体API端点实现
│   │       ├── devices.py           # 设备管理API
│   │       ├── ports.py             # 端口管理API
│   │       ├── vlans.py             # VLAN管理API
│   │       ├── inspections.py       # 巡检管理API
│   │       ├── configurations.py    # 配置管理API
│   │       ├── device_collection.py # 设备采集API
│   │       ├── git_configs.py       # Git配置API
│   │       ├── command_templates.py # 命令模板API
│   │       └── command_history.py   # 命令历史API
│   ├── services/           # 业务逻辑层
│   │   ├── netmiko_service.py       # 设备连接服务
│   │   ├── git_service.py           # Git操作服务
│   │   ├── backup_scheduler.py      # 备份调度服务
│   │   ├── excel_service.py         # Excel处理服务
│   │   └── ssh_connection_pool.py   # SSH连接池
│   ├── models/             # 数据模型层
│   │   ├── __init__.py
│   │   └── models.py       # SQLAlchemy模型定义
│   ├── schemas/            # 数据验证层
│   │   └── schemas.py      # Pydantic模型定义
│   ├── config.py           # 应用配置
│   ├── main.py             # 应用入口
│   └── db_update.py        # 数据库更新脚本
├── frontend/               # 前端应用代码
│   ├── public/             # 静态资源
│   ├── src/                # 源代码
│   │   ├── api/            # API服务层
│   │   │   ├── index.js    # Axios配置和拦截器
│   │   │   └── deviceCollection.js # 设备采集API
│   │   ├── assets/         # 资源文件
│   │   ├── components/     # 公共组件
│   │   ├── router/         # 路由配置
│   │   │   └── index.js    # 路由定义和导航守卫
│   │   ├── stores/         # 状态管理 (Pinia)
│   │   │   ├── deviceStore.js       # 设备状态管理
│   │   │   └── deviceCollectionStore.js # 设备采集状态管理
│   │   ├── views/          # 页面视图
│   │   │   ├── HomeView.vue              # 首页
│   │   │   ├── DeviceManagement.vue      # 设备管理
│   │   │   ├── PortManagement.vue        # 端口管理
│   │   │   ├── VLANManagement.vue        # VLAN管理
│   │   │   ├── InspectionManagement.vue  # 巡检管理
│   │   │   ├── ConfigurationManagement.vue # 配置管理
│   │   │   ├── DeviceCollection.vue      # 设备采集
│   │   │   └── GitConfigManagement.vue   # Git配置管理
│   │   ├── App.vue         # 根组件
│   │   ├── main.js         # 入口文件
│   │   └── style.css       # 全局样式
│   ├── test/               # 测试文件
│   ├── Dockerfile.frontend # 前端Dockerfile
│   ├── nginx.conf          # Nginx配置
│   ├── package.json        # 依赖配置
│   ├── vite.config.js      # Vite配置
│   └── vitest.config.js    # Vitest配置
├── data/                   # 数据文件目录
├── scripts/                # 辅助脚本
├── tests/                  # 后端测试代码
├── docs/                   # 项目文档
│   ├── 项目分析/           # 项目分析文档
│   │   ├── 01-项目架构分析.md
│   │   ├── 02-技术栈分析.md
│   │   ├── 03-API接口分析.md
│   │   ├── 04-数据库模型分析.md
│   │   ├── 05-前端架构分析.md
│   │   └── 06-部署架构分析.md
│   └── debugs/             # 调试记录
├── .env.example            # 环境变量示例
├── .gitignore              # Git忽略文件
├── Dockerfile              # 后端Dockerfile
├── docker-compose.yml      # Docker Compose配置
├── pytest.ini              # pytest配置
├── requirements.txt        # 后端依赖
└── README.md               # 项目说明文档
```

## API接口设计

### API路由结构

```
Base URL: http://localhost:8000/api/v1

API结构:
├── /devices              # 设备管理 (7个端点)
├── /ports                # 端口管理 (5个端点)
├── /vlans                # VLAN管理 (4个端点)
├── /inspections          # 巡检管理 (3个端点)
├── /configurations       # 配置管理 (4个端点)
├── /device-collection    # 设备信息采集 (5个端点)
├── /git-configs          # Git配置管理 (5个端点)
├── /command-templates    # 命令模板管理 (4个端点)
└── /command-history      # 命令执行历史 (3个端点)
```

### 通用规范

**请求格式**：
- Content-Type: `application/json`
- 字符编码: `UTF-8`

**响应格式**：
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

**HTTP状态码**：
- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

### 核心API端点

#### 设备管理
- `GET /api/v1/devices` - 获取设备列表（支持分页、筛选）
- `POST /api/v1/devices` - 创建新设备
- `GET /api/v1/devices/{id}` - 获取设备详情
- `PUT /api/v1/devices/{id}` - 更新设备信息
- `DELETE /api/v1/devices/{id}` - 删除设备
- `POST /api/v1/devices/batch/delete` - 批量删除设备
- `POST /api/v1/devices/batch/update-status` - 批量更新设备状态
- `POST /api/v1/devices/{id}/execute-command` - 执行设备命令
- `POST /api/v1/devices/batch/execute-command` - 批量执行命令

#### 巡检管理
- `POST /api/v1/inspections/run/{device_id}` - 执行设备巡检
- `POST /api/v1/inspections/batch/run` - 批量执行巡检
- `GET /api/v1/inspections` - 获取巡检记录列表

#### 配置管理
- `POST /api/v1/configurations/device/{device_id}/collect` - 从设备采集配置
- `GET /api/v1/configurations/diff/{config_id1}/{config_id2}` - 获取配置差异
- `GET /api/v1/configurations` - 获取配置列表
- `DELETE /api/v1/configurations/{config_id}` - 删除配置记录

#### 设备信息采集
- `POST /api/v1/device-collection/devices/{device_id}/version` - 采集版本信息
- `POST /api/v1/device-collection/devices/{device_id}/serial` - 采集序列号
- `POST /api/v1/device-collection/devices/{device_id}/interfaces` - 采集接口信息
- `POST /api/v1/device-collection/devices/{device_id}/mac-table` - 采集MAC地址表
- `POST /api/v1/device-collection/batch/collect` - 批量采集设备信息

**完整API文档可通过Swagger UI访问**：`http://localhost:8000/docs`

## 数据库设计

### 数据库架构

- **数据库**: MySQL 5.7
- **ORM**: SQLAlchemy 1.4.51
- **驱动**: PyMySQL 1.1.0
- **字符集**: UTF-8

### 数据模型关系

```mermaid
erDiagram
    DEVICE ||--o{ PORT : has
    DEVICE ||--o{ VLAN : has
    DEVICE ||--o{ INSPECTION : has
    DEVICE ||--o{ CONFIGURATION : has
    DEVICE ||--o{ MAC_ADDRESS : has
    DEVICE ||--o{ DEVICE_VERSION : has
    DEVICE ||--o{ BACKUP_SCHEDULE : has
    DEVICE ||--o{ COMMAND_HISTORY : has
    GIT_CONFIG ||--o{ CONFIGURATION : uses
    COMMAND_TEMPLATE ||--o{ COMMAND_HISTORY : uses
```

### 核心数据表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| devices | 设备信息表 | id, hostname, ip_address, vendor, model, status |
| ports | 端口信息表 | id, device_id, port_name, status, speed, description |
| vlans | VLAN信息表 | id, device_id, vlan_name, vlan_description |
| inspections | 巡检结果表 | id, device_id, cpu_usage, memory_usage, interface_status |
| configurations | 配置信息表 | id, device_id, config_content, version, git_commit_id |
| mac_addresses | MAC地址表 | id, device_id, mac_address, vlan_id, interface |
| device_versions | 设备版本信息表 | id, device_id, software_version, hardware_version |
| git_configs | Git配置表 | id, repo_url, username, branch, is_active |
| backup_schedules | 备份任务表 | id, device_id, schedule_type, time, is_active |
| command_templates | 命令模板表 | id, name, command, vendor, device_type, variables |
| command_history | 命令历史表 | id, device_id, command, output, success, execution_time |

## 部署架构

### Docker Compose 部署架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose 部署架构                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐                                                           │
│  │   外部用户访问    │                                                           │
│  └────────┬─────────┘                                                           │
│           │ HTTP 80                                                             │
│           ▼                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐       │
│  │                        Frontend 服务 (Nginx)                          │       │
│  │  - 静态资源服务 (Vue.js 构建产物)                                       │       │
│  │  - API 请求反向代理到后端                                               │       │
│  │  - 端口映射: 80:80                                                     │       │
│  └───────────────────────────────┬──────────────────────────────────────┘       │
│                                  │ /api/*                                        │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐       │
│  │                        Backend 服务 (FastAPI)                         │       │
│  │  - Python 3.9 + FastAPI 应用                                           │       │
│  │  - RESTful API 服务                                                    │       │
│  │  - 端口映射: 8000:8000                                                 │       │
│  └──────┬───────────────────────┬──────────────────────────────────────┘       │
│         │                       │                                                │
│         │ MySQL                 │ Oxidized API                                   │
│         ▼                                                                        │
│  ┌──────────────────┐                                                           │
│  │   DB 服务         │                                                           │
│  │  (MySQL 5.7)      │                                                           │
│  │  - 端口: 3306     │                                                           │
│  │  - 数据持久化     │                                                           │
│  └──────────────────┘                                                           │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           Docker 网络 (bridge)                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           数据卷                                        │    │
│  │  - mysql_data: MySQL 数据库持久化存储                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 服务依赖关系

```
                    ┌─────────────────┐
                    │   Frontend      │
                    │   (Nginx 80)    │
                    └────────┬────────┘
                             │ depends_on
                             ▼
                    ┌─────────────────┐
                    │    Backend      │
                    │  (FastAPI 8000) │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                                 │
            ▼                                 ▼
    ┌───────────────┐               ┌──────────────┐
    │      DB       │               │ 外部网络设备  │
    │  (MySQL 3306) │               │   (SSH)      │
    └───────────────┘               └──────────────┘
```

## 安装与部署

### 1. 环境准备

#### 后端依赖
```bash
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 2. 配置文件

创建`.env`文件并配置以下内容：

```bash
# 数据库连接信息
DATABASE_URL=mysql://username:password@localhost:3306/switch_manage

# 应用配置
APP_NAME=Switch Manage System
APP_VERSION=1.0.0
DEBUG=True
```

### 3. 数据库初始化

运行数据库迁移脚本：

```bash
python scripts/init_db.py
```

### 4. 启动服务

#### 后端服务
```bash
# 开发模式（带热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 前端服务
```bash
cd frontend
npm run dev
```

### 5. Docker部署

使用Docker Compose一键部署：

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

### 6. 常用运维命令

```bash
# 查看所有容器状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart [service_name]

# 进入容器
docker-compose exec backend bash

# 数据库备份
docker-compose exec db mysqldump -u admin -p switch_manage > backup.sql

# 查看资源使用
docker stats
```

## 使用说明

1. **登录系统**：访问前端界面（默认 http://localhost）
2. **添加设备**：在设备管理页面添加交换机设备信息
3. **执行巡检**：在巡检管理页面创建巡检任务，批量检查设备状态
4. **管理配置**：在配置管理页面查看和管理设备配置
5. **查看报告**：在报告中心查看历史巡检报告
6. **命令执行**：在设备管理页面执行单个或批量命令
7. **设备采集**：在设备采集页面采集设备详细信息

## 开发指南

### 后端开发

1. **API开发**：在`app/api/endpoints/`目录下创建路由文件
2. **业务逻辑**：在`app/services/`目录下实现业务逻辑
3. **数据模型**：在`app/models/`目录下定义数据模型
4. **数据验证**：在`app/schemas/`目录下定义数据验证模型

### 前端开发

1. **组件开发**：在`frontend/src/components/`目录下创建组件
2. **页面开发**：在`frontend/src/views/`目录下创建页面
3. **API调用**：在`frontend/src/api/`目录下定义API调用
4. **状态管理**：使用Pinia进行状态管理

## 测试

### 后端测试

```bash
# 单元测试
python -m pytest tests/unit/

# 集成测试
python -m pytest tests/integration/
```

### 前端测试

```bash
cd frontend
npm run test
```

## 项目文档

项目详细文档位于 `docs/` 目录：

- [项目架构分析](docs/项目分析/01-项目架构分析.md)
- [技术栈分析](docs/项目分析/02-技术栈分析.md)
- [API接口分析](docs/项目分析/03-API接口分析.md)
- [数据库模型分析](docs/项目分析/04-数据库模型分析.md)
- [前端架构分析](docs/项目分析/05-前端架构分析.md)
- [部署架构分析](docs/项目分析/06-部署架构分析.md)

## 版本历史

- v1.0.0（初始版本）：实现基本的设备管理、巡检、配置管理功能

## 贡献指南

欢迎提交Issue和Pull Request，帮助改进本项目。

## 许可证

本项目采用MIT许可证。
