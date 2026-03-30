# 会话状态：switch_manage 服务启动 (2026-03-30)

**会话日期**: 2026-03-30  
**任务类型**: 服务运维  
**工作目录**: `/mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage/`

---

## 本次操作 (2026-03-30 09:12)

**任务**: 分别启动 switch_manage 项目的前后端服务

**启动结果**:
| 服务 | 地址 | 状态 | PID |
|------|------|------|-----|
| 后端 API | http://localhost:8000 | 🟢 运行中 | 3572 |
| 前端页面 | http://localhost:5173 | 🟢 运行中 | 3483 |
| 数据库 | 10.21.65.20:3307 | 🟢 已连接 | - |

**后端服务信息**:
- 备份调度器已启动
- IP 定位调度器已启动（间隔 10 分钟）
- 加载了 1 个备份任务（接入交换机 -01）

---

## 问题发现 (2026-03-30 09:44)

**任务**: 验证前端"IP 定位"模块异常问题

**问题现象**: 点击"IP 列表"标签页时报错"获取 IP 列表失败"

**根因分析**:
1. 后端 API `/api/v1/ip-location/list` 返回 500 错误
2. Pydantic 验证失败：`IPListEntry.device_hostname` 应为 string 但收到 None
3. 数据库 `ip_location_current` 表存在大量 `mac_device_hostname IS NULL` 的记录

**修复方案**（待确认）:
- 方案 A：修改 Schema，`device_hostname: Optional[str] = None`
- 方案 B：服务层兜底，`entry.mac_device_hostname or ""`
- 方案 C：修复数据采集逻辑

**状态**: ⏳ 等待祥哥确认修复方案
- 备份调度器已启动
- IP 定位调度器已启动（间隔 10 分钟）
- 加载了 1 个备份任务（接入交换机 -01）

---

## 历史修复汇总 (2026-03-26)

---

## 问题修复汇总

### 用户反馈的 7 个问题

| 编号 | 问题 | 根因 | 修复方案 | 状态 |
|------|------|------|----------|------|
| **1** | 备份计划加载不出来 | 路由顺序问题 | 重构 configurations.py 路由顺序 | ✅ 已修复 |
| **2** | 配置管理看不到 items | 路由顺序问题 | 同问题 1 | ✅ 已修复 |
| **3** | 备份监控看不到日志 | Response 模型不匹配 | 修改 response_model 为 Dict | ✅ 已修复 |
| **4** | Git 配置看不到 | 后端正常 | API 验证通过 | ✅ 已修复 |
| **5** | IP 定位打开空白 | 后端正常 | API 验证通过 | ✅ 已修复 |
| **6** | IP 定位 URL 跳转错误 | 路由重定向相对路径 | 改为绝对路径 `/ip-location/search` | ✅ 已修复 |
| **7** | 用户管理跳转首页 | JWT sub 字段类型错误 | sub 改为字符串类型 | ✅ 已修复 |

---

## 最新修复 (2026-03-26 13:07)

### 问题 7: 用户管理跳转首页 - JWT 类型错误 ✅

**根因分析** (深入调试):
1. 测试发现 `/api/v1/auth/me` 返回 401 Unauthorized
2. Token 解码失败，payload 返回 None
3. 发现 JWT 规范要求 `sub` 必须是字符串，但代码传递的是整数 `user.id`
4. `create_access_token(data={"sub": user.id})` → `user.id` 是整数
5. JWT 库拒绝解码 `sub` 为整数的 token

**修复**:
```python
# app/api/endpoints/auth.py
# 修改前
data={"sub": user.id}

# 修改后
data={"sub": str(user.id)}

# app/api/deps.py
# 添加兼容处理
if isinstance(user_id, str):
    user_id = int(user_id)
```

**影响**:
- 登录时创建的 token 现在符合 JWT 规范
- `/api/v1/auth/me` 能正确返回用户信息和 roles
- 前端 authStore.isAdmin 能正确判断
- 用户管理页面不再跳转首页

---

## Git 提交历史

```
d7963f7 fix: JWT token sub 字段类型错误
50e27b9 fix: get_current_user 预加载 roles 关系
c077c01 fix: 用户管理路由守卫竞态条件
26537b2 fix: 前端路由跳转问题 (IP 定位/用户管理)
b369079 fix: 用户管理权限检查 (R3)
ac73805 fix: 配置计划加载失败排查 (R2)
671fbb8 fix: 延迟检测列代码提交 (R4)
ea74521 fix: IP 定位模块前端代码提交 (R1)
```

---

## 服务状态

| 服务 | 状态 | 地址 |
|------|------|------|
| 后端 | ✅ 运行中 | http://localhost:8000 |
| 前端 | ✅ 运行中 | http://localhost:5173 |

---

## 验证步骤

**请强制刷新浏览器 (Ctrl+Shift+R 或 Ctrl+F5)**:

1. **重新登录** (重要！旧的 token 无效了)
2. **IP 定位**: 点击菜单 → URL 应该是 `/ip-location/search`，页面正常显示
3. **用户管理**: 点击菜单 → 应该能正常访问 `/users` 页面

---

**最后更新**: 2026-03-26 13:10  
**状态**: 7 个问题全部修复完成，需要重新登录
