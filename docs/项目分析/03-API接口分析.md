# 交换机批量管理与巡检系统 - API接口分析

> 分析日期：2026-02-09
> 分析工具：SKILL (dispatching-parallel-agents, brainstorming, writing-plans)
> 更新说明：基于批量配置备份功能(Phase1-3)和用户认证系统的实现进行全面更新

---

## 1. API概览

### 1.1 API架构

```
Base URL: http://localhost:8000/api/v1

API结构:
├── /auth                 # 认证管理 (新增)
├── /users                # 用户管理 (新增)
├── /devices              # 设备管理
├── /ports                # 端口管理
├── /vlans                # VLAN管理
├── /inspections          # 巡检管理
├── /configurations       # 配置管理 (扩展)
│   └── /monitoring       # 监控统计 (新增)
├── /device-collection    # 设备信息采集
├── /git-configs          # Git配置管理
├── /command-templates    # 命令模板管理
├── /command-history      # 命令执行历史
└── /ip-location          # IP 定位管理 (新增)
```

### 1.2 通用规范

**请求格式**：
- Content-Type: `application/json`
- 字符编码: `UTF-8`
- 认证头: `Authorization: Bearer {token}` (受保护接口)

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
- `401` - 未授权
- `403` - 禁止访问
- `404` - 资源不存在
- `409` - 资源冲突
- `422` - 验证错误
- `500` - 服务器内部错误

---

## 2. 认证API (/auth)

### 2.1 获取验证码

**请求信息**：
- **Method**: GET
- **Path**: `/auth/captcha`
- **说明**: 获取图形验证码，用于登录验证

**响应示例**：
```json
{
  "success": true,
  "message": "获取验证码成功",
  "data": {
    "captcha_id": "abc123...",
    "captcha_image": "data:image/png;base64,iVBORw0KGgo..."
  }
}
```

### 2.2 用户登录

**请求信息**：
- **Method**: POST
- **Path**: `/auth/login`

**请求体**：
```json
{
  "username": "admin",
  "password": "password123",
  "captcha_id": "abc123...",
  "captcha_code": "A3B7",
  "remember_me": true
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 604800,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "管理员",
      "role": "admin",
      "is_active": true
    }
  }
}
```

### 2.3 用户登出

**请求信息**：
- **Method**: POST
- **Path**: `/auth/logout`
- **认证**: 需要

**响应示例**：
```json
{
  "success": true,
  "message": "登出成功",
  "data": null
}
```

### 2.4 获取当前用户信息

**请求信息**：
- **Method**: GET
- **Path**: `/auth/me`
- **认证**: 需要

**响应示例**：
```json
{
  "success": true,
  "message": "获取用户信息成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "管理员",
    "role": "admin",
    "is_active": true,
    "last_login": "2026-02-09T10:30:00"
  }
}
```

---

## 3. 用户管理API (/users)

### 3.1 获取用户列表

**请求信息**：
- **Method**: GET
- **Path**: `/users`
- **认证**: 需要 (管理员权限)
- **Query参数**:
  - `skip` (int): 跳过记录数，默认0
  - `limit` (int): 返回记录数，默认100
  - `role` (string): 按角色筛选
  - `is_active` (bool): 按状态筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取用户列表成功",
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "管理员",
        "role": "admin",
        "is_active": true,
        "created_at": "2026-01-15T10:30:00"
      }
    ]
  }
}
```

### 3.2 创建用户

**请求信息**：
- **Method**: POST
- **Path**: `/users`
- **认证**: 需要 (管理员权限)

**请求体**：
```json
{
  "username": "operator1",
  "email": "operator1@example.com",
  "password": "password123",
  "full_name": "操作员1",
  "role": "user",
  "is_active": true
}
```

**字段验证**：
- `username`: 必填，3-50字符，唯一
- `email`: 必填，有效邮箱格式，唯一
- `password`: 必填，最少8字符
- `role`: 枚举值(admin/user)，默认user

### 3.3 获取用户详情

**请求信息**：
- **Method**: GET
- **Path**: `/users/{user_id}`
- **认证**: 需要 (管理员权限)

### 3.4 更新用户

**请求信息**：
- **Method**: PUT
- **Path**: `/users/{user_id}`
- **认证**: 需要 (管理员权限)

**请求体**：
```json
{
  "email": "newemail@example.com",
  "full_name": "新名称",
  "role": "user",
  "is_active": true
}
```

### 3.5 删除用户

**请求信息**：
- **Method**: DELETE
- **Path**: `/users/{user_id}`
- **认证**: 需要 (管理员权限)

### 3.6 重置密码

**请求信息**：
- **Method**: POST
- **Path**: `/users/{user_id}/reset-password`
- **认证**: 需要 (管理员权限)

**请求体**：
```json
{
  "new_password": "newpassword123"
}
```

---

## 4. 设备管理API (/devices)

### 4.1 获取设备列表

**请求信息**：
- **Method**: GET
- **Path**: `/devices`
- **Query参数**:
  - `skip` (int): 跳过记录数，默认0
  - `limit` (int): 返回记录数，默认100
  - `vendor` (string): 按厂商筛选
  - `status` (string): 按状态筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取设备列表成功",
  "data": {
    "total": 50,
    "items": [
      {
        "id": 1,
        "hostname": "SW-Core-01",
        "ip_address": "192.168.1.1",
        "vendor": "cisco",
        "model": "Catalyst 3750",
        "os_version": "15.0(2)SE11",
        "location": "机房A",
        "status": "active",
        "login_method": "ssh",
        "login_port": 22,
        "username": "admin",
        "sn": "FDO123456789",
        "created_at": "2026-01-15T10:30:00",
        "updated_at": "2026-01-20T14:20:00"
      }
    ],
    "page": 1,
    "size": 20,
    "pages": 3
  }
}
```

### 4.2 获取所有设备（无分页）

**请求信息**：
- **Method**: GET
- **Path**: `/devices/all`
- **Query参数**:
  - `limit` (int): 限制返回数量，默认100，最大5000
  - `offset` (int): 偏移量
  - `status` (string): 按状态筛选
  - `vendor` (string): 按厂商筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取设备列表成功",
  "data": [
    {
      "id": 1,
      "hostname": "SW-Core-01",
      "ip_address": "192.168.1.1",
      "vendor": "cisco",
      "status": "active"
    }
  ]
}
```

### 4.3 创建设备

**请求信息**：
- **Method**: POST
- **Path**: `/devices`

**请求体**：
```json
{
  "hostname": "SW-Core-01",
  "ip_address": "192.168.1.1",
  "vendor": "cisco",
  "model": "Catalyst 3750",
  "os_version": "15.0(2)SE11",
  "location": "机房A",
  "contact": "张三",
  "status": "active",
  "login_method": "ssh",
  "login_port": 22,
  "username": "admin",
  "password": "password123",
  "sn": "FDO123456789"
}
```

**字段验证**：
- `hostname`: 必填，最大255字符
- `ip_address`: 必填，有效IP格式
- `vendor`: 必填，支持cisco/huawei/h3c/ruijie
- `model`: 必填，最大100字符
- `login_method`: 枚举值(ssh/telnet)，默认ssh
- `status`: 枚举值(active/inactive/maintenance/offline)，默认active

### 4.4 获取设备详情

**请求信息**：
- **Method**: GET
- **Path**: `/devices/{device_id}`

**响应示例**：
```json
{
  "success": true,
  "message": "获取设备详情成功",
  "data": {
    "id": 1,
    "hostname": "SW-Core-01",
    "ip_address": "192.168.1.1",
    "vendor": "cisco",
    "model": "Catalyst 3750",
    "ports": [...],
    "vlans": [...],
    "inspections": [...],
    "configurations": [...]
  }
}
```

### 4.5 更新设备

**请求信息**：
- **Method**: PUT
- **Path**: `/devices/{device_id}`

**请求体**：
```json
{
  "hostname": "SW-Core-01-New",
  "location": "机房B",
  "status": "maintenance"
}
```

### 4.6 删除设备

**请求信息**：
- **Method**: DELETE
- **Path**: `/devices/{device_id}`

### 4.7 批量删除设备

**请求信息**：
- **Method**: POST
- **Path**: `/devices/batch/delete`

**请求体**：
```json
{
  "ids": [1, 2, 3, 4, 5]
}
```

### 4.8 批量更新设备状态

**请求信息**：
- **Method**: POST
- **Path**: `/devices/batch/update-status`

**请求体**：
```json
{
  "ids": [1, 2, 3],
  "status": "maintenance"
}
```

### 4.9 批量导入设备

**请求信息**：
- **Method**: POST
- **Path**: `/devices/batch/import`
- **Content-Type**: `multipart/form-data`

**请求参数**：
- `file`: Excel文件

**响应示例**：
```json
{
  "success": true,
  "message": "批量导入完成",
  "data": {
    "total": 10,
    "success": 8,
    "failed": 2,
    "errors": [
      {
        "row": 3,
        "message": "IP地址格式错误"
      }
    ]
  }
}
```

### 4.10 下载导入模板

**请求信息**：
- **Method**: GET
- **Path**: `/devices/template`
- **响应**: Excel文件下载

### 4.11 测试设备连接

**请求信息**：
- **Method**: POST
- **Path**: `/devices/{device_id}/test-connectivity`

**响应示例**：
```json
{
  "success": true,
  "message": "连接测试成功",
  "data": {
    "device_id": 1,
    "reachable": true,
    "response_time": 45.2,
    "tested_at": "2026-02-09T10:30:00"
  }
}
```

### 4.12 执行设备命令

**请求信息**：
- **Method**: POST
- **Path**: `/devices/{device_id}/execute-command`

**请求体**：
```json
{
  "command": "show version",
  "timeout": 30
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "命令执行成功",
  "data": {
    "device_id": 1,
    "command": "show version",
    "output": "Cisco IOS Software...",
    "success": true,
    "execution_time": "2026-02-09T10:30:00",
    "duration": 2.5
  }
}
```

### 4.13 批量执行命令

**请求信息**：
- **Method**: POST
- **Path**: `/devices/batch/execute-command`

**请求体**：
```json
{
  "device_ids": [1, 2, 3],
  "command": "show version",
  "timeout": 30
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量命令执行完成",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "results": [
      {
        "device_id": 1,
        "device_name": "SW-Core-01",
        "command": "show version",
        "output": "Cisco IOS Software...",
        "success": true,
        "duration": 2.5
      }
    ]
  }
}
```

---

## 5. 端口管理API (/ports)

### 5.1 获取端口列表

**请求信息**：
- **Method**: GET
- **Path**: `/ports`
- **Query参数**:
  - `device_id` (int): 按设备ID筛选
  - `status` (string): 按状态筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取端口列表成功",
  "data": {
    "total": 48,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "port_name": "GigabitEthernet1/0/1",
        "status": "up",
        "speed": "1000 Mbps",
        "description": "Uplink to Core",
        "vlan_id": 10,
        "created_at": "2026-01-15T10:30:00",
        "updated_at": "2026-01-20T14:20:00"
      }
    ]
  }
}
```

### 5.2 创建端口

**请求信息**：
- **Method**: POST
- **Path**: `/ports`

**请求体**：
```json
{
  "device_id": 1,
  "port_name": "GigabitEthernet1/0/1",
  "status": "up",
  "speed": "1000 Mbps",
  "description": "Uplink to Core",
  "vlan_id": 10
}
```

### 5.3 更新端口

**请求信息**：
- **Method**: PUT
- **Path**: `/ports/{port_id}`

### 5.4 删除端口

**请求信息**：
- **Method**: DELETE
- **Path**: `/ports/{port_id}`

### 5.5 批量删除端口

**请求信息**：
- **Method**: POST
- **Path**: `/ports/batch/delete`

---

## 6. VLAN管理API (/vlans)

### 6.1 获取VLAN列表

**请求信息**：
- **Method**: GET
- **Path**: `/vlans`
- **Query参数**:
  - `device_id` (int): 按设备ID筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取VLAN列表成功",
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "vlan_name": "VLAN10",
        "vlan_description": "管理VLAN",
        "created_at": "2026-01-15T10:30:00",
        "updated_at": "2026-01-20T14:20:00"
      }
    ]
  }
}
```

### 6.2 创建VLAN

**请求信息**：
- **Method**: POST
- **Path**: `/vlans`

**请求体**：
```json
{
  "device_id": 1,
  "vlan_name": "VLAN10",
  "vlan_description": "管理VLAN"
}
```

### 6.3 更新VLAN

**请求信息**：
- **Method**: PUT
- **Path**: `/vlans/{vlan_id}`

### 6.4 删除VLAN

**请求信息**：
- **Method**: DELETE
- **Path**: `/vlans/{vlan_id}`

---

## 7. 巡检管理API (/inspections)

### 7.1 获取巡检结果列表

**请求信息**：
- **Method**: GET
- **Path**: `/inspections`
- **Query参数**:
  - `device_id` (int): 按设备ID筛选
  - `start_time` (datetime): 开始时间
  - `end_time` (datetime): 结束时间

**响应示例**：
```json
{
  "success": true,
  "message": "获取巡检结果列表成功",
  "data": {
    "total": 100,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "device_name": "SW-Core-01",
        "inspection_time": "2026-02-01T10:00:00",
        "cpu_usage": 45.5,
        "memory_usage": 60.2,
        "interface_status": {
          "total": 48,
          "up": 45,
          "down": 3
        },
        "error_logs": null,
        "status": "completed"
      }
    ]
  }
}
```

### 7.2 执行设备巡检

**请求信息**：
- **Method**: POST
- **Path**: `/inspections/run/{device_id}`

**响应示例**：
```json
{
  "success": true,
  "message": "巡检执行成功",
  "data": {
    "device_id": 1,
    "device_name": "SW-Core-01",
    "cpu_usage": 45.5,
    "memory_usage": 60.2,
    "interface_status": {
      "total": 48,
      "up": 45,
      "down": 3
    },
    "inspection_time": "2026-02-01T10:00:00"
  }
}
```

### 7.3 批量执行巡检

**请求信息**：
- **Method**: POST
- **Path**: `/inspections/batch/run`

**请求体**：
```json
{
  "device_ids": [1, 2, 3, 4, 5]
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量巡检完成",
  "data": {
    "total": 5,
    "success": 4,
    "failed": 1,
    "results": [
      {
        "device_id": 1,
        "success": true,
        "message": "巡检成功"
      },
      {
        "device_id": 2,
        "success": false,
        "message": "连接超时"
      }
    ]
  }
}
```

---

## 8. 配置管理API (/configurations)

### 8.1 获取配置列表

**请求信息**：
- **Method**: GET
- **Path**: `/configurations`
- **Query参数**:
  - `device_id` (int): 按设备ID筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取配置列表成功",
  "data": {
    "total": 20,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "device_name": "SW-Core-01",
        "config_content": "!\nversion 15.0\n...",
        "config_time": "2026-02-01T10:00:00",
        "version": "1.0",
        "change_description": "初始配置",
        "git_commit_id": "abc123...",
        "created_at": "2026-02-01T10:00:00"
      }
    ]
  }
}
```

### 8.2 从设备采集配置

**请求信息**：
- **Method**: POST
- **Path**: `/configurations/device/{device_id}/collect`

**请求体**：
```json
{
  "change_description": "定期备份"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "配置采集成功",
  "data": {
    "id": 2,
    "device_id": 1,
    "config_content": "!\nversion 15.0\n...",
    "version": "1.1",
    "change_description": "定期备份",
    "git_commit_id": "def456..."
  }
}
```

### 8.3 获取配置差异

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/diff/{config_id1}/{config_id2}`

**响应示例**：
```json
{
  "success": true,
  "message": "获取配置差异成功",
  "data": {
    "device_name": "SW-Core-01",
    "version1": "1.0",
    "version2": "1.1",
    "diff": [
      {
        "type": "removed",
        "line": "no ip http server"
      },
      {
        "type": "added",
        "line": "ip http server"
      }
    ]
  }
}
```

### 8.4 删除配置记录

**请求信息**：
- **Method**: DELETE
- **Path**: `/configurations/{config_id}`

### 8.5 批量备份所有设备

**请求信息**：
- **Method**: POST
- **Path**: `/configurations/backup-all`

**请求体**：
```json
{
  "filter_status": "online",
  "filter_vendor": "Huawei",
  "async_execute": true,
  "notify_on_complete": false,
  "priority": "normal",
  "max_concurrent": 3,
  "timeout": 300,
  "retry_count": 2
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量备份任务已创建",
  "data": {
    "task_id": "task-uuid-123",
    "status": "pending",
    "total": 10,
    "message": "任务已提交，正在异步执行"
  }
}
```

### 8.6 获取备份任务列表

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/backup-tasks`
- **Query参数**:
  - `status` (string): 按状态筛选
  - `limit` (int): 返回数量

**响应示例**：
```json
{
  "success": true,
  "message": "获取备份任务列表成功",
  "data": {
    "total": 20,
    "items": [
      {
        "task_id": "task-uuid-123",
        "status": "completed",
        "total": 10,
        "completed": 10,
        "success_count": 9,
        "failed_count": 1,
        "created_at": "2026-02-09T10:00:00",
        "started_at": "2026-02-09T10:00:05",
        "completed_at": "2026-02-09T10:05:30"
      }
    ]
  }
}
```

### 8.7 获取备份任务详情

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/backup-tasks/{task_id}`

**响应示例**：
```json
{
  "success": true,
  "message": "获取任务详情成功",
  "data": {
    "task_id": "task-uuid-123",
    "status": "completed",
    "total": 10,
    "completed": 10,
    "success_count": 9,
    "failed_count": 1,
    "results": [
      {
        "device_id": 1,
        "device_name": "SW-Core-01",
        "status": "success",
        "execution_time": 2.5,
        "config_id": 123
      }
    ]
  }
}
```

### 8.8 取消备份任务

**请求信息**：
- **Method**: POST
- **Path**: `/configurations/backup-tasks/{task_id}/cancel`

**响应示例**：
```json
{
  "success": true,
  "message": "任务已取消",
  "data": {
    "task_id": "task-uuid-123",
    "status": "cancelled"
  }
}
```

---

## 9. 监控统计API (/configurations/monitoring)

### 9.1 获取备份统计

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/monitoring/statistics`
- **Query参数**:
  - `days` (int): 统计天数，默认7

**响应示例**：
```json
{
  "success": true,
  "message": "获取备份统计成功",
  "data": {
    "total_backups": 150,
    "successful_backups": 142,
    "failed_backups": 8,
    "success_rate": 94.67,
    "average_execution_time": 45.2,
    "period": {
      "start": "2026-02-02T00:00:00",
      "end": "2026-02-09T23:59:59"
    }
  }
}
```

### 9.2 获取仪表盘摘要

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/monitoring/dashboard`

**响应示例**：
```json
{
  "success": true,
  "message": "获取仪表盘数据成功",
  "data": {
    "total_devices": 50,
    "online_devices": 45,
    "total_schedules": 30,
    "active_schedules": 28,
    "today_backups": 10,
    "today_success": 9,
    "recent_failures": [
      {
        "device_id": 1,
        "device_name": "SW-Core-01",
        "error": "连接超时",
        "time": "2026-02-09T09:30:00"
      }
    ]
  }
}
```

### 9.3 获取执行日志

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/monitoring/execution-logs`
- **Query参数**:
  - `device_id` (int): 按设备筛选
  - `status` (string): 按状态筛选
  - `limit` (int): 返回数量，默认50

**响应示例**：
```json
{
  "success": true,
  "message": "获取执行日志成功",
  "data": {
    "total": 200,
    "items": [
      {
        "id": 1,
        "task_id": "task-uuid-123",
        "device_id": 1,
        "device_name": "SW-Core-01",
        "status": "success",
        "execution_time": 2.5,
        "trigger_type": "manual",
        "started_at": "2026-02-09T10:00:00",
        "completed_at": "2026-02-09T10:00:02"
      }
    ]
  }
}
```

### 9.4 获取备份趋势

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/monitoring/trends`
- **Query参数**:
  - `days` (int): 天数，默认30

**响应示例**：
```json
{
  "success": true,
  "message": "获取备份趋势成功",
  "data": {
    "labels": ["2026-01-10", "2026-01-11", "..."],
    "successful": [10, 12, "..."],
    "failed": [1, 0, "..."],
    "total": [11, 12, "..."]
  }
}
```

### 9.5 获取设备备份统计

**请求信息**：
- **Method**: GET
- **Path**: `/configurations/monitoring/devices/statistics`

**响应示例**：
```json
{
  "success": true,
  "message": "获取设备备份统计成功",
  "data": {
    "total": 50,
    "items": [
      {
        "device_id": 1,
        "device_name": "SW-Core-01",
        "total_backups": 30,
        "successful_backups": 28,
        "failed_backups": 2,
        "success_rate": 93.33,
        "last_backup": "2026-02-09T10:00:00"
      }
    ]
  }
}
```

---

## 10. 设备信息采集API (/device-collection)

### 10.1 采集设备版本信息

**请求信息**：
- **Method**: POST
- **Path**: `/device-collection/devices/{device_id}/version`

**响应示例**：
```json
{
  "success": true,
  "message": "版本信息采集成功",
  "data": {
    "device_id": 1,
    "software_version": "15.0(2)SE11",
    "hardware_version": "WS-C3750G-24TS",
    "boot_version": "12.2(44)SE6",
    "system_image": "flash:/c3750-ipservicesk9-mz.150-2.SE11.bin",
    "uptime": "10 weeks, 3 days, 2 hours",
    "collected_at": "2026-02-01T10:00:00"
  }
}
```

### 10.2 采集设备序列号

**请求信息**：
- **Method**: POST
- **Path**: `/device-collection/devices/{device_id}/serial`

**响应示例**：
```json
{
  "success": true,
  "message": "序列号采集成功",
  "data": {
    "device_id": 1,
    "serial": "FDO123456789"
  }
}
```

### 10.3 采集接口信息

**请求信息**：
- **Method**: POST
- **Path**: `/device-collection/devices/{device_id}/interfaces`

**响应示例**：
```json
{
  "success": true,
  "message": "接口信息采集成功",
  "data": {
    "device_id": 1,
    "interfaces": [
      {
        "port_name": "GigabitEthernet1/0/1",
        "status": "up",
        "description": "Uplink to Core",
        "speed": "1000 Mbps"
      }
    ],
    "collected_count": 48
  }
}
```

### 10.4 采集MAC地址表

**请求信息**：
- **Method**: POST
- **Path**: `/device-collection/devices/{device_id}/mac-table`

**响应示例**：
```json
{
  "success": true,
  "message": "MAC地址表采集成功",
  "data": {
    "device_id": 1,
    "mac_entries": [
      {
        "mac_address": "00:11:22:33:44:55",
        "vlan_id": 10,
        "interface": "Gi1/0/1",
        "address_type": "dynamic"
      }
    ],
    "collected_count": 150
  }
}
```

### 10.5 批量采集设备信息

**请求信息**：
- **Method**: POST
- **Path**: `/device-collection/batch/collect`

**请求体**：
```json
{
  "device_ids": [1, 2, 3],
  "collect_types": ["version", "serial", "interfaces", "mac_table"]
}
```

**collect_types可选值**：
- `version` - 版本信息
- `serial` - 序列号
- `interfaces` - 接口信息
- `mac_table` - MAC地址表
- `running_config` - 运行配置

**响应示例**：
```json
{
  "success": true,
  "message": "批量采集完成",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "details": [
      {
        "device_id": 1,
        "hostname": "SW-Core-01",
        "success": true,
        "data": {
          "version": {...},
          "serial": "FDO123456789",
          "interfaces": [...]
        }
      }
    ]
  }
}
```

---

## 11. Git配置管理API (/git-configs)

### 11.1 获取Git配置列表

**请求信息**：
- **Method**: GET
- **Path**: `/git-configs`

**响应示例**：
```json
{
  "success": true,
  "message": "获取Git配置列表成功",
  "data": {
    "total": 2,
    "items": [
      {
        "id": 1,
        "repo_url": "https://github.com/example/configs.git",
        "username": "admin",
        "branch": "main",
        "is_active": true,
        "created_at": "2026-01-15T10:30:00",
        "updated_at": "2026-01-20T14:20:00"
      }
    ]
  }
}
```

### 11.2 创建Git配置

**请求信息**：
- **Method**: POST
- **Path**: `/git-configs`

**请求体**：
```json
{
  "repo_url": "https://github.com/example/configs.git",
  "username": "admin",
  "password": "ghp_xxxxxxxxxxxx",
  "branch": "main",
  "ssh_key_path": null,
  "is_active": true
}
```

### 11.3 测试Git连接

**请求信息**：
- **Method**: POST
- **Path**: `/git-configs/{git_config_id}/test`

**响应示例**：
```json
{
  "success": true,
  "message": "Git连接测试成功",
  "data": {
    "reachable": true,
    "branch_exists": true,
    "permissions": ["pull", "push"]
  }
}
```

### 11.4 设置活跃Git配置

**请求信息**：
- **Method**: POST
- **Path**: `/git-configs/active/{git_config_id}`

---

## 12. 命令模板管理API (/command-templates)

### 12.1 获取命令模板列表

**请求信息**：
- **Method**: GET
- **Path**: `/command-templates`
- **Query参数**:
  - `vendor` (string): 按厂商筛选
  - `device_type` (string): 按设备类型筛选

**响应示例**：
```json
{
  "success": true,
  "message": "获取命令模板列表成功",
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "name": "查看版本",
        "description": "查看设备版本信息",
        "command": "show version",
        "vendor": "cisco",
        "device_type": "switch",
        "variables": null,
        "tags": ["基本信息"],
        "is_public": true,
        "created_by": "admin",
        "created_at": "2026-01-15T10:30:00"
      }
    ]
  }
}
```

### 12.2 创建命令模板

**请求信息**：
- **Method**: POST
- **Path**: `/command-templates`

**请求体**：
```json
{
  "name": "查看接口状态",
  "description": "查看所有接口状态",
  "command": "show interfaces status",
  "vendor": "cisco",
  "device_type": "switch",
  "variables": null,
  "tags": ["接口", "状态"],
  "is_public": true
}
```

### 12.3 更新命令模板

**请求信息**：
- **Method**: PUT
- **Path**: `/command-templates/{template_id}`

### 12.4 删除命令模板

**请求信息**：
- **Method**: DELETE
- **Path**: `/command-templates/{template_id}`

---

## 13. 命令执行历史API (/command-history)

### 13.1 获取命令执行历史

**请求信息**：
- **Method**: GET
- **Path**: `/command-history`
- **Query参数**:
  - `device_id` (int): 按设备ID筛选
  - `limit` (int): 返回记录数

**响应示例**：
```json
{
  "success": true,
  "message": "获取命令执行历史成功",
  "data": {
    "total": 100,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "device_name": "SW-Core-01",
        "command": "show version",
        "output": "Cisco IOS Software...",
        "success": true,
        "executed_by": "admin",
        "execution_time": "2026-02-01T10:00:00",
        "duration": 2.5
      }
    ]
  }
}
```

### 13.2 执行命令

**请求信息**：
- **Method**: POST
- **Path**: `/command-history/devices/{device_id}/execute`

**请求体**：
```json
{
  "command": "show version",
  "variables": null,
  "template_id": null
}
```

### 13.3 批量执行命令

**请求信息**：
- **Method**: POST
- **Path**: `/command-history/batch/execute`

**请求体**：
```json
{
  "device_ids": [1, 2, 3],
  "command": "show version",
  "variables": null,
  "template_id": null
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量命令执行完成",
  "data": {
    "total": 3,
    "success": 3,
    "failed": 0,
    "results": [
      {
        "device_id": 1,
        "device_name": "SW-Core-01",
        "command": "show version",
        "output": "Cisco IOS Software...",
        "success": true,
        "duration": 2.5
      }
    ]
  }
}
```

---

## 14. IP 定位管理API (/ip-location) (新增)

> 更新日期：2026-03-27
> 功能说明：基于 ARP/MAC 表的 IP 地址定位功能

### 14.1 搜索 IP 地址定位

**请求信息**：
- **Method**: GET
- **Path**: `/ip-location/search/{ip_address}`

**路径参数**：
- `ip_address` (string): 要搜索的 IP 地址

**响应示例**：
```json
{
  "success": true,
  "ip_address": "192.168.1.100",
  "locations": [
    {
      "ip_address": "192.168.1.100",
      "mac_address": "00:11:22:33:44:55",
      "device_id": 5,
      "device_hostname": "SW-Access-01",
      "device_ip": "192.168.1.2",
      "device_location": "机房A-1楼",
      "interface": "GigabitEthernet1/0/10",
      "vlan_id": 100,
      "last_seen": "2026-03-27T10:00:00",
      "confidence": 0.95,
      "is_uplink": false,
      "is_core_switch": false,
      "match_type": "exact"
    }
  ],
  "message": "找到 1 条记录"
}
```

**字段说明**：
- `confidence`: 定位置信度（0.00-1.00），越高越可信
- `is_uplink`: 是否为上行链路（上行链路定位可信度较低）
- `is_core_switch`: 是否来自核心交换机
- `match_type`: 匹配类型（exact-精确匹配/fuzzy-模糊匹配/none-未匹配）

### 14.2 获取 IP 列表

**请求信息**：
- **Method**: GET
- **Path**: `/ip-location/list`
- **Query参数**:
  - `page` (int): 页码，默认1
  - `page_size` (int): 每页数量，默认50，最大200
  - `search` (string): 搜索关键词（IP/MAC/主机名）

**响应示例**：
```json
{
  "total": 500,
  "items": [
    {
      "ip_address": "192.168.1.100",
      "mac_address": "00:11:22:33:44:55",
      "mac_device_hostname": "SW-Access-01",
      "mac_device_ip": "192.168.1.2",
      "mac_device_location": "机房A-1楼",
      "access_interface": "GigabitEthernet1/0/10",
      "vlan_id": 100,
      "confidence": 0.95,
      "last_seen": "2026-03-27T10:00:00"
    }
  ],
  "page": 1,
  "page_size": 50
}
```

### 14.3 获取数据收集状态

**请求信息**：
- **Method**: GET
- **Path**: `/ip-location/collection/status`

**响应示例**：
```json
{
  "is_running": false,
  "last_run_at": "2026-03-27T10:00:00",
  "last_run_success": true,
  "last_run_message": "收集完成",
  "devices_total": 50,
  "devices_completed": 48,
  "devices_failed": 2,
  "arp_entries_collected": 1500,
  "mac_entries_collected": 3000
}
```

### 14.4 触发数据收集任务

**请求信息**：
- **Method**: POST
- **Path**: `/ip-location/collection/trigger`

**响应示例**：
```json
{
  "success": true,
  "message": "收集任务已触发",
  "status": {
    "is_running": true,
    "devices_total": 50,
    "devices_completed": 0,
    "devices_failed": 0
  }
}
```

### 14.5 IP 定位工作原理

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IP 定位预计算流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 数据收集阶段                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│  │  设备采集    │───▶│  ARP 表采集  │───▶│ arp_current │            │
│  │  (Netmiko)  │    │             │    │   (数据库)   │            │
│  └─────────────┘    └─────────────┘    └─────────────┘            │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐                                                    │
│  │ MAC 地址采集 │───▶ mac_current (数据库)                           │
│  └─────────────┘                                                    │
│                                                                     │
│  2. 预计算阶段 (每 10 分钟自动执行)                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    IPLocationCalculator                      │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │   │
│  │  │ 加载 ARP    │    │ 加载 MAC    │    │ 加载设备信息 │     │   │
│  │  │ 批量数据    │    │ 批量数据    │    │ (冗余字段)  │     │   │
│  │  └──────┬──────┘    └──────┬──────┘    └─────────────┘     │   │
│  │         │                  │                                  │   │
│  │         └────────┬─────────┘                                  │   │
│  │                  ▼                                            │   │
│  │         ┌─────────────┐                                       │   │
│  │         │  IP-MAC 匹配 │                                       │   │
│  │         │  置信度计算  │                                       │   │
│  │         └──────┬──────┘                                       │   │
│  │                │                                              │   │
│  │                ▼                                              │   │
│  │         ┌───────────────────┐                                 │   │
│  │         │ip_location_current│                                 │   │
│  │         │   (预计算结果)     │                                 │   │
│  │         └───────────────────┘                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  3. 归档阶段 (两级验证)                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  验证1: calculated_at > 阈值时间（默认30分钟）                  │   │
│  │  验证2: IP 不在当前 ARP 表中                                   │   │
│  │  ─────────────────────────────────────────────────────────────│   │
│  │  符合条件 ──▶ ip_location_history (历史记录)                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 15. API路由聚合

### 15.1 路由注册 (app/api/__init__.py)

```python
from fastapi import APIRouter
from app.api.endpoints import (
    auth, users, devices, ports, vlans, inspections,
    configurations, device_collection,
    git_configs, command_templates, command_history,
    ip_location  # 新增
)

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(ports.router, prefix="/ports", tags=["ports"])
api_router.include_router(vlans.router, prefix="/vlans", tags=["vlans"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["inspections"])
api_router.include_router(configurations.router, prefix="/configurations", tags=["configurations"])
api_router.include_router(device_collection.router, prefix="/device-collection", tags=["device-collection"])
api_router.include_router(git_configs.router, prefix="/git-configs", tags=["git-configs"])
api_router.include_router(command_templates.router, prefix="/command-templates", tags=["command-templates"])
api_router.include_router(command_history.router, prefix="/command-history", tags=["command-history"])
api_router.include_router(ip_location.router, prefix="/ip-location", tags=["ip-location"])  # 新增
```

### 15.2 API统计

| 模块 | 端点数量 | 主要功能 |
|------|----------|----------|
| auth | 4 | 用户认证、验证码、登录登出 |
| users | 6 | 用户CRUD、密码重置 |
| devices | 13 | 设备CRUD、批量操作、导入导出、命令执行 |
| ports | 5 | 端口CRUD、批量操作 |
| vlans | 4 | VLAN CRUD |
| inspections | 3 | 巡检执行、批量巡检 |
| configurations | 9 | 配置采集、差异比较、批量备份、任务管理 |
| monitoring | 5 | 备份统计、仪表盘、趋势分析 |
| device-collection | 5 | 设备信息采集 |
| git-configs | 5 | Git配置管理 |
| command-templates | 4 | 命令模板管理 |
| command-history | 3 | 命令执行、历史记录 |
| ip-location | 4 | IP 定位查询、列表、收集状态、触发收集 (新增) |
| **总计** | **70+** | - |

---

## 16. 总结

本项目API设计遵循RESTful规范，具有以下特点：

1. **模块化设计**：按功能模块划分API，结构清晰
2. **统一响应格式**：所有API返回统一的响应结构
3. **完善的错误处理**：包含详细的错误信息和状态码
4. **批量操作支持**：支持批量删除、批量更新、批量执行等操作
5. **异步处理**：设备操作采用异步方式，避免阻塞
6. **数据验证**：使用Pydantic进行严格的请求数据验证
7. **认证授权**：JWT Token认证，RBAC权限控制
8. **监控统计**：完善的备份监控和统计API
9. **IP 定位功能**：基于预计算的快速 IP 定位查询（新增）

API文档可通过Swagger UI访问：`http://localhost:8000/docs`
