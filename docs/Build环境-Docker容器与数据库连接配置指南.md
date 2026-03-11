# Docker容器与数据库连接配置指南

## 概述

本文档总结了 Switch Manage 项目在 Docker **构建环境（Build Environment）**中容器与数据库的连接方式，包括网络配置、连接字符串格式以及常见问题的解决方案。

> **注意**：本文档描述的是**构建测试环境**，主要用于代码变更后的镜像构建验证和功能测试。生产环境部署请参考 `docker-compose.unified.yml` 配置。

## 环境信息

| 项目 | 值 |
|------|-----|
| 应用容器名 | `switch-manage-test` |
| 数据库容器名 | `netdev-test` |
| 数据库镜像 | `mariadb:11` |
| 数据库端口 | `3306` (容器内部) / `3307` (宿主机映射) |
| 数据库名 | `switch_manage` |

## 网络架构

```
┌─────────────────────────────────────────────────────────────┐
│                      宿主机 (10.21.65.20)                    │
│                                                              │
│  ┌─────────────────────┐     ┌─────────────────────────┐   │
│  │   switch-manage-test │     │      netdev-test        │   │
│  │   (应用容器)          │     │   (数据库容器)           │   │
│  │                      │     │                         │   │
│  │   Nginx :80          │     │   MariaDB :3306         │   │
│  │   Uvicorn :8000      │     │                         │   │
│  │                      │     │                         │   │
│  └──────────┬───────────┘     └───────────┬─────────────┘   │
│             │                              │                  │
│             │   Docker Network:            │                  │
│             │   netdevdb-test_netdev-test  │                  │
│             └──────────────────────────────┘                  │
│                                                              │
│  端口映射:                                                   │
│  - 8081 → switch-manage-test:80                             │
│  - 3307 → netdev-test:3306                                  │
└─────────────────────────────────────────────────────────────┘
```

## 连接方式

### 方式一：Docker 网络互联（推荐）

**适用场景**：应用容器和数据库容器在同一 Docker 网络中

**配置步骤**：

1. **查看数据库容器所属网络**
```bash
docker inspect netdev-test | grep NetworkMode
# 输出: "NetworkMode": "netdevdb-test_netdev-test"
```

2. **查看数据库容器 IP**
```bash
docker inspect netdev-test | grep -i IPAddress | head -3
# 输出: "IPAddress": "172.26.0.2"
```

3. **启动应用容器并加入同一网络**
```bash
docker run -d \
  --name switch-manage-test \
  -p 8081:80 \
  --network netdevdb-test_netdev-test \
  -e DATABASE_URL="mysql+pymysql://root:1qaz%40WSX@netdev-test:3306/switch_manage" \
  switch-manage:20260310-10
```

**关键点**：
- 使用 `--network` 参数将容器加入数据库所在网络
- 连接字符串中使用**容器名**作为主机名（`netdev-test`）
- 使用容器内部端口（`3306`），而非宿主机映射端口

### 方式二：Host 网络模式

**适用场景**：需要直接访问宿主机网络

**配置方式**：
```bash
docker run -d \
  --name switch-manage-test \
  --network host \
  -e DATABASE_URL="mysql+pymysql://root:1qaz%40WSX@10.21.65.20:3307/switch_manage" \
  switch-manage:20260310-10
```

**关键点**：
- 使用 `--network host` 模式
- 连接字符串中使用**宿主机 IP** 和**映射端口**
- 注意：此模式下端口映射参数 `-p` 无效

### 方式三：Docker Bridge 网关

**适用场景**：容器使用默认 bridge 网络，需要访问宿主机服务

**配置方式**：
```bash
docker run -d \
  --name switch-manage-test \
  -p 8081:80 \
  -e DATABASE_URL="mysql+pymysql://root:1qaz%40WSX@172.17.0.1:3307/switch_manage" \
  switch-manage:20260310-10
```

**关键点**：
- `172.17.0.1` 是 Docker 默认 bridge 网络的网关地址
- 使用宿主机映射端口

**注意**：此方式可能因防火墙或网络配置导致连接失败，不推荐使用。

## 连接字符串格式

### 格式说明

```
mysql+pymysql://用户名:密码@主机:端口/数据库名
```

### 密码特殊字符编码

密码中的特殊字符需要进行 URL 编码：

| 特殊字符 | URL 编码 |
|---------|---------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `/` | `%2F` |
| `:` | `%3A` |
| `?` | `%3F` |

**示例**：
- 原密码：`1qaz@WSX`
- 编码后：`1qaz%40WSX`
- 完整连接字符串：`mysql+pymysql://root:1qaz%40WSX@netdev-test:3306/switch_manage`

## 常见问题排查

### 问题1：连接超时

**错误信息**：
```
Can't connect to MySQL server on 'xxx' (timed out)
```

**排查步骤**：

1. **检查容器是否在同一网络**
```bash
docker inspect switch-manage-test | grep NetworkMode
docker inspect netdev-test | grep NetworkMode
```

2. **测试网络连通性**
```bash
docker exec switch-manage-test ping netdev-test
```

3. **检查数据库容器状态**
```bash
docker ps | grep netdev-test
```

### 问题2：密码认证失败

**错误信息**：
```
Access denied for user 'root'@'xxx'
```

**排查步骤**：

1. **检查密码是否正确编码**
2. **检查数据库用户权限**
```bash
docker exec netdev-test mariadb -uroot -p'1qaz@WSX' -e "SELECT user, host FROM mysql.user;"
```

### 问题3：数据库不存在

**错误信息**：
```
Unknown database 'switch_manage'
```

**解决方案**：
```bash
docker exec netdev-test mariadb -uroot -p'1qaz@WSX' -e "CREATE DATABASE switch_manage;"
```

## 网络配置对比

| 方式 | 主机名 | 端口 | 优点 | 缺点 |
|------|--------|------|------|------|
| Docker 网络互联 | 容器名 | 容器端口 | 性能好、安全 | 需在同一网络 |
| Host 网络模式 | 宿主机IP | 映射端口 | 配置简单 | 端口冲突风险 |
| Bridge 网关 | 网关IP | 映射端口 | 通用性强 | 可能被防火墙阻止 |

## 推荐配置

### 生产环境推荐

```bash
# 使用 Docker Compose 定义网络
docker-compose -f docker-compose.unified.yml up -d
```

### 测试环境推荐

```bash
# 手动加入现有网络
docker run -d \
  --name switch-manage-test \
  -p 8081:80 \
  --network netdevdb-test_netdev-test \
  -e DATABASE_URL="mysql+pymysql://root:1qaz%40WSX@netdev-test:3306/switch_manage" \
  switch-manage:latest
```

## 快速验证命令

```bash
# 验证数据库连接
docker exec switch-manage-test curl -s http://localhost/api/v1/auth/captcha

# 查看后端日志
docker exec switch-manage-test cat /var/log/supervisor/backend.log

# 测试数据库连接
docker exec switch-manage-test python -c "
from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://root:1qaz%40WSX@netdev-test:3306/switch_manage')
with engine.connect() as conn:
    print('Database connection successful!')
"
```

## 相关文档

- [Docker生产环境数据库迁移指南](./Docker生产环境数据库迁移指南.md)
- [docker环境 前端页面登录验证码显示异常](./debugs/docker环境 前端页面登录验证码显示异常.md)

---
**文档创建时间**：2026-03-11
**环境类型**：构建测试环境（Build Environment）
**适用版本**：switch-manage:20260310-10 及以上
**用途**：代码变更后的镜像构建验证和功能测试
