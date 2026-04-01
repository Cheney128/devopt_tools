---
ontology:
  id: DOC-2026-03-013-VER
  type: verification
  problem: ARP/MAC 调度器修复
  problem_id: P001
  status: active
  created: 2026-03-30
  updated: 2026-03-30
  author: Claude
  tags:
    - documentation
---
# ARP/MAC 采集调度器修复 - 现场验证指南

**版本**: 1.0  
**日期**: 2026-03-30  
**适用环境**: 生产环境 / 测试环境

---

## 一、快速验证（推荐）

### 步骤 1: 部署代码

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage

# 拉取最新代码
git pull

# 或切换到修复分支
git checkout fix/regression-2026-03-26
```

### 步骤 2: 重启应用

```bash
# 重启服务
systemctl restart switch_manage

# 或（如使用 Docker）
docker-compose restart
```

### 步骤 3: 观察日志（关键）

```bash
# 实时查看日志
journalctl -u switch_manage -f

# 或查看最近 10 分钟日志
journalctl -u switch_manage --since "10 minutes ago"
```

**期望看到的日志**（✅ 成功标志）:

```
[ARP/MAC] 启动立即采集...
开始批量采集 ARP 和 MAC 表，时间：2026-03-30 14:XX:XX
共有 64 台设备需要采集
设备 XXX ARP 采集成功：XX 条
设备 XXX MAC 采集成功：XX 条
...
批量采集完成：{...}
[ARP/MAC] 启动立即采集完成
[ARP/MAC] 调度器已启动，间隔：30 分钟
```

**不应看到的日志**（❌ 失败标志）:

```
ERROR: type object 'ARPEntry' has no attribute 'device_id'
ERROR: ARP 采集全部失败，跳过 IP 定位计算
WARNING: ARP/MAC 采集失败，连续失败次数：1
INFO: ARP/MAC 采集完成：成功 0 台，失败 64 台
```

### 步骤 4: 验证数据

```bash
# 连接数据库
mysql -h 10.21.65.20 -P 3307 -u <用户名> -p

# 执行查询
SELECT COUNT(*) AS arp_count FROM arp_current;
SELECT COUNT(*) AS mac_count FROM mac_current;
SELECT MAX(last_seen) AS latest_time FROM arp_current;
SELECT MAX(last_seen) AS latest_time FROM mac_current;
```

**期望结果**:
- `arp_count > 0`（有 ARP 数据）
- `mac_count > 0`（有 MAC 数据）
- `latest_time` 为最近 5 分钟内

### 步骤 5: 等待定时采集（可选）

等待 30 分钟后，再次查看日志：

```bash
journalctl -u switch_manage --since "30 minutes ago" | grep "开始执行 ARP/MAC 采集"
```

应看到定时采集自动执行。

---

## 二、配置开关验证（可选）

### 场景 1: 禁用启动立即采集

```bash
# 编辑环境变量文件
vim .env

# 添加或修改配置
ARP_MAC_COLLECTION_ON_STARTUP=False

# 重启应用
systemctl restart switch_manage

# 观察日志
journalctl -u switch_manage -f
```

**期望**: 日志中无 `启动立即采集` 相关日志，但调度器正常启动。

### 场景 2: 完全禁用采集

```bash
# 编辑环境变量文件
vim .env

# 添加或修改配置
ARP_MAC_COLLECTION_ENABLED=False

# 重启应用
systemctl restart switch_manage

# 观察日志
journalctl -u switch_manage -f
```

**期望**: 日志显示 `[ARP/MAC] 采集功能已禁用，跳过启动`。

### 场景 3: 修改采集间隔

```bash
# 编辑环境变量文件
vim .env

# 添加或修改配置
ARP_MAC_COLLECTION_INTERVAL=60

# 重启应用
systemctl restart switch_manage

# 观察日志
journalctl -u switch_manage -f | grep "间隔"
```

**期望**: 日志显示 `[ARP/MAC] 调度器已启动，间隔：60 分钟`。

---

## 三、回滚方案（如需）

### 快速回滚

```bash
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage

# Git 回滚
git revert HEAD

# 重启应用
systemctl restart switch_manage
```

### 手动回滚

```bash
# 恢复配置文件
# 删除新增的配置项：
# - ARP_MAC_COLLECTION_ENABLED
# - ARP_MAC_COLLECTION_ON_STARTUP

# 恢复代码文件
# 将 arp_mac_scheduler.py 中的 arp_device_id/mac_device_id 改回 device_id

# 重启应用
systemctl restart switch_manage
```

---

## 四、问题排查

### 问题 1: 启动后仍然报错 device_id

**可能原因**: 代码未正确部署

**解决方案**:
```bash
# 检查代码版本
cd /mnt/d/BaiduSyncdisk/5.code/netdevops/switch_manage
git log --oneline -3

# 确认代码已更新
grep "arp_device_id" app/services/arp_mac_scheduler.py

# 重启应用
systemctl restart switch_manage
```

### 问题 2: 启动后立即采集失败

**可能原因**: 网络设备不可达、数据库连接失败

**解决方案**:
```bash
# 查看详细错误日志
journalctl -u switch_manage --since "5 minutes ago" | grep "启动立即采集失败"

# 检查网络设备连通性
ping <设备 IP>

# 检查数据库连接
mysql -h 10.21.65.20 -P 3307 -u <用户名> -p -e "SELECT 1"
```

**注意**: 即使立即采集失败，调度器仍会正常启动，定时任务会继续执行。

### 问题 3: 采集耗时过长

**可能原因**: 设备数量多、网络延迟高

**解决方案**:
1. 观察日志中的采集耗时统计
2. 考虑分批次采集（需代码优化）
3. 添加超时控制（后续优化项）

---

## 五、验证检查清单

完成验证后，请确认以下项目：

- [ ] 应用启动无报错
- [ ] 日志显示 `启动立即采集...`
- [ ] 日志显示 `启动立即采集完成`
- [ ] 日志无 `device_id` 相关错误
- [ ] `arp_current` 表有数据
- [ ] `mac_current` 表有数据
- [ ] 数据时间为最近（5 分钟内）
- [ ] 30 分钟后定时采集正常执行（可选）
- [ ] 配置开关生效（如测试）

---

## 六、联系方式

如有问题，请联系：
- 开发负责人：祥哥
- 运维负责人：[待填写]
- 技术支持：乐乐 (DevOps Agent)

---

**文档生成时间**: 2026-03-30  
**文档状态**: 已发布
