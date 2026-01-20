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

### 2. 批量巡检交换机
- 获取交换机运行状态
- 采集性能指标（CPU、内存使用率等）
- 检查端口状态
- 生成巡检报告
- 异常告警通知

### 3. 与Oxidized集成
- 与Oxidized配置备份平台共用MySQL数据库
- 获取交换机配置信息
- 配置版本管理

## 技术栈

### 后端
- Python 3.8+
- FastAPI（高性能异步Web框架）
- SQLAlchemy ORM
- Netmiko（网络设备连接库）
- Pydantic（数据验证）
- python-dotenv（环境变量管理）

### 前端
- Vue.js 3
- Element Plus（UI组件库）
- Axios（HTTP客户端）
- Vue Router（路由管理）
- Pinia（状态管理）

### 数据库
- MySQL 5.7+

### 其他
- Oxidized 0.28+（配置备份平台）
- Docker（容器化部署）

## 项目结构

```
switch_manage/
├── app/
│   ├── api/           # API路由
│   ├── services/      # 业务逻辑
│   ├── models/        # 数据模型
│   ├── schemas/       # 数据验证
│   ├── utils/         # 工具函数
│   └── config.py      # 配置文件
├── frontend/          # 前端代码
├── scripts/           # 脚本文件
├── .env               # 环境变量
├── requirements.txt   # 依赖文件
├── Dockerfile         # Docker配置
└── README.md          # 项目文档
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

```
# 数据库连接信息
DATABASE_URL=mysql://username:password@localhost:3306/switch_manage

# 应用配置
APP_NAME=Switch Manage System
APP_VERSION=1.0.0
DEBUG=True

# Oxidized配置
OXIDIZED_URL=http://localhost:8888
```

### 3. 数据库初始化

运行数据库迁移脚本：

```bash
python scripts/init_db.py
```

### 4. 启动服务

#### 后端服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端服务
```bash
cd frontend
npm run dev
```

### 5. Docker部署

使用Docker Compose部署：

```bash
docker-compose up -d
```

## 使用说明

1. **登录系统**：访问前端界面，使用默认账号密码登录（admin/admin）
2. **添加设备**：在设备管理页面添加交换机设备信息
3. **执行巡检**：在巡检管理页面创建巡检任务，批量检查设备状态
4. **管理配置**：在配置管理页面查看和管理设备配置
5. **查看报告**：在报告中心查看历史巡检报告

## 系统架构

### 数据流图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Frontend as 前端界面
    participant Backend as 后端API
    participant DB as MySQL数据库
    participant Oxidized as Oxidized平台
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

    Backend->>Oxidized: 获取配置备份
    Oxidized->>DB: 读取设备信息
    DB-->>Oxidized: 返回设备数据
    Oxidized-->>Backend: 返回配置文件
```

### 程序架构图

```mermaid
flowchart TD
    subgraph 前端层
        A[Vue.js应用]
        B[Element Plus组件]
        C[Axios请求]
    end

    subgraph 后端层
        D[FastAPI]
        E[API路由]
        F[业务逻辑层]
        G[设备交互模块]
        H[数据库操作模块]
        I[配置管理模块]
    end

    subgraph 数据层
        J[MySQL数据库]
        K[设备信息表]
        L[配置信息表]
        M[巡检结果表]
    end

    subgraph 集成层
        N[Oxidized平台]
        O[配置备份服务]
    end

    A --> B
    A --> C
    C --> E
    E --> F
    F --> G
    F --> H
    F --> I
    G --> 交换机设备
    H --> J
    I --> N
    J --> K
    J --> L
    J --> M
    N --> O
    O --> J
```

## 开发指南

### 后端开发

1. **API开发**：在`app/api/`目录下创建路由文件
2. **业务逻辑**：在`app/services/`目录下实现业务逻辑
3. **数据模型**：在`app/models/`目录下定义数据模型
4. **数据验证**：在`app/schemas/`目录下定义数据验证模型

### 前端开发

1. **组件开发**：在`frontend/src/components/`目录下创建组件
2. **页面开发**：在`frontend/src/views/`目录下创建页面
3. **API调用**：在`frontend/src/api/`目录下定义API调用
4. **状态管理**：使用Pinia进行状态管理

## 测试

### 单元测试

```bash
python -m pytest tests/unit/
```

### 集成测试

```bash
python -m pytest tests/integration/
```

## 版本历史

- v1.0.0（初始版本）：实现基本的设备管理和巡检功能

## 贡献指南

欢迎提交Issue和Pull Request，帮助改进本项目。

## 许可证

本项目采用MIT许可证。