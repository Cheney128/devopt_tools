# Docker生产环境数据库迁移指南

## 概述

本文档描述了如何在Docker生产环境中安全地执行数据库迁移，特别是添加 `last_run_time` 字段到 `backup_schedules` 表的迁移过程。

## 迁移方案特点

### 1. 自动迁移（推荐）
- 在容器启动时自动检查并执行迁移
- 幂等性设计：可重复执行，不会重复添加已存在的字段
- 零停机时间：应用启动时自动完成迁移

### 2. 手动迁移
- 适合需要精确控制迁移时机的场景
- 可查看详细的迁移过程和验证结果
- 支持迁移前手动备份

### 3. 回滚机制
- 迁移前自动创建数据库备份
- 支持一键回滚到迁移前状态
- 回滚前自动备份当前数据

## 文件说明

| 文件 | 用途 | 位置 |
|------|------|------|
| `db_migrate_docker.py` | 手动迁移脚本 | `/unified-app/scripts/` |
| `auto_migrate.py` | 自动迁移脚本 | `/unified-app/scripts/` |
| `db_rollback.py` | 回滚脚本 | `/unified-app/scripts/` |
| `entrypoint.sh` | 容器入口脚本（已集成自动迁移） | `/entrypoint.sh` |

## 迁移前准备

### 1. 备份当前数据

在迁移前，建议先手动备份数据库：

```bash
# 进入容器
docker compose exec app bash

# 手动备份数据库
mysqldump -h db -u root -p'[OylKbYLJf*Hx((4dEIf]' switch_manage > /backups/manual_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 检查当前数据库状态

```bash
# 进入数据库容器
docker compose exec db bash

# 登录MySQL
mysql -u root -p'[OylKbYLJf*Hx((4dEIf]' switch_manage

# 检查表结构
DESCRIBE backup_schedules;

# 检查索引
SHOW INDEX FROM backup_schedules;
```

## 迁移方式

### 方式一：自动迁移（推荐）

自动迁移已集成到容器启动流程中，只需正常部署新版本：

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建并启动容器
docker compose up -d --build app

# 3. 查看迁移日志
docker compose logs app | grep -A 20 "Database Migration"
```

自动迁移流程：
1. 容器启动时自动检查是否需要迁移
2. 如需迁移，自动执行以下步骤：
   - 备份数据库
   - 添加 `last_run_time` 字段
   - 创建索引
   - 同步现有数据
   - 验证迁移结果
3. 应用正常启动

### 方式二：手动迁移

如果需要手动控制迁移过程：

```bash
# 1. 进入应用容器
docker compose exec app bash

# 2. 执行手动迁移
python3 /unified-app/scripts/db_migrate_docker.py
```

手动迁移输出示例：
```
============================================================
Docker生产环境数据库迁移工具
============================================================
开始时间: 2024-02-23 10:00:00
✓ 检测到Docker环境
============================================================
步骤 1/4: 备份数据库
============================================================
正在备份数据库到: /backups/db_backup_20240223_100000.sql
✓ 数据库备份成功: /backups/db_backup_20240223_100000.sql
============================================================
步骤 2/4: 检查并执行数据库迁移
============================================================
正在添加 last_run_time 字段...
✓ last_run_time 字段添加成功
正在创建索引...
✓ 索引创建成功
正在同步现有数据...
✓ 成功同步 213 条备份计划的 last_run_time
============================================================
步骤 3/4: 验证迁移结果
============================================================
✓ last_run_time 字段存在
✓ ix_backup_schedules_last_run_time 索引存在
✓ 备份计划总数: 213
✓ 已设置 last_run_time 的计划数: 213
============================================================
步骤 4/4: 更新迁移状态
============================================================
✓ 迁移状态已更新: /unified-app/.db_migration_completed
============================================================
数据库迁移成功完成!
============================================================
结束时间: 2024-02-23 10:00:15
数据库备份文件: /backups/db_backup_20240223_100000.sql
```

## 验证迁移

### 1. 检查字段是否添加成功

```bash
# 进入数据库容器
docker compose exec db bash

# 登录MySQL
mysql -u root -p'[OylKbYLJf*Hx((4dEIf]' switch_manage

# 检查表结构
DESCRIBE backup_schedules;
```

预期输出应包含：
```
+----------------+-------------+------+-----+---------+----------------+
| Field          | Type        | Null | Key | Default | Extra          |
+----------------+-------------+------+-----+---------+----------------+
| ...            | ...         | ...  | ... | ...     | ...            |
| last_run_time  | datetime    | YES  | MUL | NULL    |                |
+----------------+-------------+------+-----+---------+----------------+
```

### 2. 检查索引是否创建成功

```sql
SHOW INDEX FROM backup_schedules;
```

预期输出应包含：
```
+---------+------------+--------------------------------+--------------+---------------+-----------+-------------+----------+--------+------+------------+---------+---------------+
| Table   | Non_unique | Key_name                       | Seq_in_index | Column_name   | Collation | Cardinality | Sub_part | Packed | Null | Index_type | Comment | Index_comment |
+---------+------------+--------------------------------+--------------+---------------+-----------+-------------+----------+--------+------+------------+---------+---------------+
| backup_schedules | 1 | ix_backup_schedules_last_run_time | 1 | last_run_time | A         | ...         | NULL     | NULL   | YES  | BTREE      |         |               |
+---------+------------+--------------------------------+--------------+---------------+-----------+-------------+----------+--------+------+------------+---------+---------------+
```

### 3. 检查数据同步情况

```sql
-- 查看已设置 last_run_time 的备份计划数量
SELECT COUNT(*) FROM backup_schedules WHERE last_run_time IS NOT NULL;

-- 查看示例数据
SELECT id, device_id, schedule_type, last_run_time 
FROM backup_schedules 
WHERE last_run_time IS NOT NULL 
LIMIT 5;
```

### 4. 通过API验证

```bash
# 获取备份计划列表
curl -X GET "http://localhost/api/v1/configurations/backup-schedules?page=1&page_size=10"

# 检查返回数据中是否包含 last_run_time 字段
```

## 回滚操作

如果迁移后出现问题，可以回滚到迁移前的状态：

### 1. 查看可用的备份

```bash
# 进入应用容器
docker compose exec app bash

# 列出所有备份
python3 /unified-app/scripts/db_rollback.py --list
```

### 2. 回滚到最新的备份

```bash
python3 /unified-app/scripts/db_rollback.py --latest
```

### 3. 回滚到指定的备份

```bash
python3 /unified-app/scripts/db_rollback.py --backup /backups/db_backup_20240223_100000.sql
```

### 4. 强制回滚（跳过确认）

```bash
python3 /unified-app/scripts/db_rollback.py --latest --force
```

**注意：** 回滚会丢失备份后产生的所有数据变更，请谨慎操作！

## 故障排除

### 问题1：迁移脚本无法连接到数据库

**症状：**
```
错误: DATABASE_URL 环境变量未设置
```

**解决：**
```bash
# 检查环境变量
docker compose exec app env | grep DATABASE_URL

# 如果未设置，检查 .env.docker 文件是否正确挂载
```

### 问题2：字段已存在但数据未同步

**症状：**
```
✓ last_run_time 字段已存在，跳过添加
✓ ix_backup_schedules_last_run_time 索引已存在，跳过创建
✓ 成功同步 0 条备份计划的 last_run_time
```

**解决：**
```bash
# 手动执行数据同步
python3 /unified-app/scripts/db_migrate_docker.py

# 或者检查 backup_execution_logs 表是否有数据
```

### 问题3：备份目录不存在

**症状：**
```
备份目录不存在: /backups
```

**解决：**
```bash
# 在宿主机上创建备份目录
mkdir -p /data/it-devops/backups

# 检查 docker-compose.yml 中是否正确挂载了备份目录
volumes:
  - ./backups:/backups
```

### 问题4：mysqldump 命令未找到

**症状：**
```
[Errno 2] No such file or directory: 'mysqldump'
```

**解决：**
```bash
# 在应用容器中安装 mysql-client
apt-get update && apt-get install -y default-mysql-client

# 或者在 Dockerfile 中添加安装命令
```

## 最佳实践

### 1. 生产环境部署流程

```bash
# 1. 备份当前数据库
docker compose exec app bash -c "mysqldump -h db -u root -p'[OylKbYLJf*Hx((4dEIf]' switch_manage > /backups/pre_deploy_backup_$(date +%Y%m%d_%H%M%S).sql"

# 2. 拉取最新代码
git pull

# 3. 停止应用服务
docker compose stop app

# 4. 重新构建并启动
docker compose up -d --build app

# 5. 监控迁移日志
docker compose logs -f app | grep -E "(Migration|backup_schedules|last_run_time)"

# 6. 验证迁移结果
docker compose exec app python3 /unified-app/scripts/db_migrate_docker.py

# 7. 检查应用状态
docker compose ps
curl -f http://localhost/health
```

### 2. 监控和告警

建议在迁移后监控以下指标：

- 应用启动时间
- 数据库连接状态
- API响应时间
- 备份计划列表加载时间

### 3. 定期备份策略

```bash
# 设置定时任务（crontab）
0 2 * * * cd /data/it-devops && docker compose exec -T app mysqldump -h db -u root -p'[OylKbYLJf*Hx((4dEIf]' switch_manage > /data/it-devops/backups/auto_backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql

# 清理旧备份（保留最近30天）
0 3 * * * find /data/it-devops/backups -name "auto_backup_*.sql" -mtime +30 -delete
```

## 总结

本迁移方案提供了三种迁移方式：

1. **自动迁移**：适合大多数场景，零停机时间
2. **手动迁移**：适合需要精确控制的场景
3. **回滚机制**：提供安全保障，可快速恢复

通过幂等性设计和完善的验证机制，确保数据库迁移的安全性和可靠性。
