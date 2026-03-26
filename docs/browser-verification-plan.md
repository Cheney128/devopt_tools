# switch_manage 前端功能验证脚本

**验证日期**: 2026-03-26  
**验证方式**: agent-browser 自动化验证  
**测试环境**: http://10.21.65.20:8080

---

## 验证步骤

### 1. 打开登录页面
- URL: http://10.21.65.20:8080/login
- 验证：页面加载成功，显示登录表单

### 2. 获取验证码
```bash
python .trae/skills/captcha-recognizer/get_captcha.py test
# 输出：UWCH (示例)
```

### 3. 登录
- 用户名：admin
- 密码：admin123
- 验证码：从数据库获取
- 验证：登录成功，跳转到首页

### 4. 验证功能模块

按以下顺序验证每个模块：

| 序号 | 模块 | 访问路径 | 验证点 |
|------|------|----------|--------|
| 1 | 首页 | /dashboard | 设备统计卡片、巡检概览 |
| 2 | 设备管理 | /devices | 设备列表（69 条）、新增/编辑按钮 |
| 3 | 端口管理 | /ports | 端口列表、筛选功能 |
| 4 | VLAN 管理 | /vlans | VLAN 列表 |
| 5 | 巡检管理 | /inspections | 巡检报告列表 |
| 6 | 配置管理 | /configurations | 配置版本列表 |
| 7 | 备份计划 | /backup-schedules | 备份任务列表 |
| 8 | 备份监控 | /backup-logs | 备份执行日志 |
| 9 | 设备采集 | /device-collection | 采集任务列表 |
| 10 | Git 配置 | /git-configs | Git 仓库配置 |
| 11 | IP 定位 | /ip-location | IP 定位查询（5519 条数据） |
| 12 | 用户管理 | /users | 用户列表 |

---

## 预期结果

- 所有 12 个模块都能正常打开
- 每个模块都有数据展示
- 无错误提示
- 页面加载时间 < 3 秒

---

## 验证码识别

使用 `.trae/skills/captcha-recognizer/get_captcha.py` 获取实时验证码。
