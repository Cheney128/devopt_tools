# ISSUE - 数据库device_role字段缺失导致多个模块报错

## 问题描述

在进行IP定位优化功能人工核验时，发现以下模块均报错"服务器内部错误"：
- 设备管理
- 备份计划
- 备份监控
- IP定位

## 问题根因

数据库中的 `devices` 表缺少 `device_role` 字段，但代码模型中定义了该字段，导致所有访问设备相关数据的API端点都报错。

## 错误信息

```
Unknown column 'devices.device_role' in 'SELECT'
```

## 影响范围

所有涉及设备查询的API端点都会受到影响，包括但不限于：
- `/api/v1/devices/*`
- `/api/v1/ip-location/*`
- `/api/v1/backup-schedules/*`

## 临时解决方案

为了能够继续进行人工核验，采用了以下临时解决方案：

### 1. 模型修改
在 `app/models/models.py:37` 中暂时注释掉了 `device_role` 字段：
```python
# device_role = Column(String(20), nullable=True, index=True)
```

### 2. 服务层修改

#### `app/services/device_role_manager.py`
在所有访问 `device_role` 的地方添加了 `hasattr()` 检查，例如：
```python
if hasattr(device, 'device_role'):
    device.device_role = role
```

#### `app/services/core_switch_recognizer.py:23`
同样添加了字段存在性检查：
```python
if hasattr(device, 'device_role'):
    if device.device_role == "core":
        return True
```

## 验证结果

实施临时解决方案后，所有模块均可正常访问：
- ✅ 设备管理页面 - 正常加载
- ✅ 备份计划页面 - 正常加载
- ✅ 备份监控页面 - 正常加载
- ✅ IP定位页面 - 正常加载

## 永久解决方案

### 步骤1：执行数据库迁移脚本

执行 `scripts/migrate_ip_location_core_switch.py` 脚本来添加 `device_role` 字段：

```bash
python scripts/migrate_ip_location_core_switch.py
```

该脚本会：
1. 检查并添加 `device_role` 字段到 `devices` 表
2. 创建 `device_role` 索引
3. 创建 `ip_location_settings` 表（如果不存在）
4. 初始化默认配置

### 步骤2：取消注释模型中的代码

在 `app/models/models.py:37` 中取消注释 `device_role` 字段：

```python
device_role = Column(String(20), nullable=True, index=True)
```

### 步骤3：恢复服务层代码

将 `app/services/device_role_manager.py` 和 `app/services/core_switch_recognizer.py` 恢复到原始状态（移除所有 `hasattr()` 检查）。

## 数据库连接问题

在执行迁移脚本时，可能会遇到数据库密码认证问题：

```
Access denied for user 'root'@'10.21.46.50' (using password: YES)
```

需要确保：
1. 数据库连接字符串中的密码正确
2. 密码中的特殊字符需要正确URL编码（例如 `@` → `%40`）

## 相关文件

- 迁移脚本：`scripts/migrate_ip_location_core_switch.py`
- 回滚脚本：`scripts/rollback_ip_location_core_switch.py`
- 自动迁移脚本：`scripts/auto_migrate.py`

## 日期

2026-03-23

