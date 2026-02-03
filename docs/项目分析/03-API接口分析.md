# 交换机批量管理与巡检系统 - API接口分析

> 分析日期：2026-02-02
> 分析工具：SKILL (brainstorming, writing-plans, development-documentation-archiving)

---

## 1. API概览

### 1.1 API架构

```
Base URL: http://localhost:8000/api/v1

API结构:
├── /devices              # 设备管理
├── /ports                # 端口管理
├── /vlans                # VLAN管理
├── /inspections          # 巡检管理
├── /configurations       # 配置管理
├── /device-collection    # 设备信息采集
├── /git-configs          # Git配置管理
├── /command-templates    # 命令模板管理
└── /command-history      # 命令执行历史
```

### 1.2 通用规范

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

---

## 2. 设备管理API (/devices)

### 2.1 获取设备列表

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

### 2.2 创建设备

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

### 2.3 获取设备详情

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

### 2.4 更新设备

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

### 2.5 删除设备

**请求信息**：
- **Method**: DELETE
- **Path**: `/devices/{device_id}`

### 2.6 批量删除设备

**请求信息**：
- **Method**: POST
- **Path**: `/devices/batch/delete`

**请求体**：
```json
{
  "ids": [1, 2, 3, 4, 5]
}
```

### 2.7 批量更新设备状态

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

---

## 3. 端口管理API (/ports)

### 3.1 获取端口列表

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

### 3.2 创建端口

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

### 3.3 更新端口

**请求信息**：
- **Method**: PUT
- **Path**: `/ports/{port_id}`

### 3.4 删除端口

**请求信息**：
- **Method**: DELETE
- **Path**: `/ports/{port_id}`

### 3.5 批量删除端口

**请求信息**：
- **Method**: POST
- **Path**: `/ports/batch/delete`

---

## 4. VLAN管理API (/vlans)

### 4.1 获取VLAN列表

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

### 4.2 创建VLAN

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

### 4.3 更新VLAN

**请求信息**：
- **Method**: PUT
- **Path**: `/vlans/{vlan_id}`

### 4.4 删除VLAN

**请求信息**：
- **Method**: DELETE
- **Path**: `/vlans/{vlan_id}`

---

## 5. 巡检管理API (/inspections)

### 5.1 获取巡检结果列表

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

### 5.2 执行设备巡检

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

### 5.3 批量执行巡检

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

## 6. 配置管理API (/configurations)

### 6.1 获取配置列表

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

### 6.2 从设备采集配置

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

### 6.3 获取配置差异

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

### 6.4 删除配置记录

**请求信息**：
- **Method**: DELETE
- **Path**: `/configurations/{config_id}`

---

## 7. 设备信息采集API (/device-collection)

### 7.1 采集设备版本信息

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

### 7.2 采集设备序列号

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

### 7.3 采集接口信息

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

### 7.4 采集MAC地址表

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

### 7.5 批量采集设备信息

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

## 8. Git配置管理API (/git-configs)

### 8.1 获取Git配置列表

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

### 8.2 创建Git配置

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

### 8.3 测试Git连接

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

### 8.4 设置活跃Git配置

**请求信息**：
- **Method**: POST
- **Path**: `/git-configs/active/{git_config_id}`

---

## 9. 命令模板管理API (/command-templates)

### 9.1 获取命令模板列表

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

### 9.2 创建命令模板

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

### 9.3 更新命令模板

**请求信息**：
- **Method**: PUT
- **Path**: `/command-templates/{template_id}`

### 9.4 删除命令模板

**请求信息**：
- **Method**: DELETE
- **Path**: `/command-templates/{template_id}`

---

## 10. 命令执行历史API (/command-history)

### 10.1 获取命令执行历史

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

### 10.2 执行命令

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

### 10.3 批量执行命令

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

## 11. API路由聚合

### 11.1 路由注册 (app/api/__init__.py)

```python
from fastapi import APIRouter
from app.api.endpoints import (
    devices, ports, vlans, inspections, 
    configurations, device_collection, 
    git_configs, command_templates, command_history
)

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(ports.router, prefix="/ports", tags=["ports"])
api_router.include_router(vlans.router, prefix="/vlans", tags=["vlans"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["inspections"])
api_router.include_router(configurations.router, prefix="/configurations", tags=["configurations"])
api_router.include_router(device_collection.router, prefix="/device-collection", tags=["device-collection"])
api_router.include_router(git_configs.router, prefix="/git-configs", tags=["git-configs"])
api_router.include_router(command_templates.router, prefix="/command-templates", tags=["command-templates"])
api_router.include_router(command_history.router, prefix="/command-history", tags=["command-history"])
```

### 11.2 API统计

| 模块 | 端点数量 | 主要功能 |
|------|----------|----------|
| devices | 7 | 设备CRUD、批量操作 |
| ports | 5 | 端口CRUD、批量操作 |
| vlans | 4 | VLAN CRUD |
| inspections | 3 | 巡检执行、批量巡检 |
| configurations | 4 | 配置采集、差异比较 |
| device-collection | 5 | 设备信息采集 |
| git-configs | 5 | Git配置管理 |
| command-templates | 4 | 命令模板管理 |
| command-history | 3 | 命令执行、历史记录 |
| **总计** | **40+** | - |

---

## 12. 总结

本项目API设计遵循RESTful规范，具有以下特点：

1. **模块化设计**：按功能模块划分API，结构清晰
2. **统一响应格式**：所有API返回统一的响应结构
3. **完善的错误处理**：包含详细的错误信息和状态码
4. **批量操作支持**：支持批量删除、批量更新等操作
5. **异步处理**：设备操作采用异步方式，避免阻塞
6. **数据验证**：使用Pydantic进行严格的请求数据验证

API文档可通过Swagger UI访问：`http://localhost:8000/docs`
