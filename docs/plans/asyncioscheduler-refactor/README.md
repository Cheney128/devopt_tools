# AsyncIOScheduler 重构项目

## 项目概述

本项目旨在统一调度器架构，修复 P0 阻塞问题，将 APScheduler 迁移至 AsyncIOScheduler。

## 目录结构

```
asyncioscheduler-refactor/
├── Progress.md              # 进度跟踪文档
├── README.md                # 项目说明（本文件）
├── plans/                   # 方案文档
│   └── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3.md
└── reviews/                 # 评审文档
    ├── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v2-review-appendix-d.md
    └── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md
```

## 文档说明

| 文档 | 说明 |
|------|------|
| [Progress.md](Progress.md) | 项目进度跟踪文档 |
| [plans/v3.0 方案](plans/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3.md) | v3.0 最终方案（已批准可实施） |
| [reviews/v2.0 附录 D](reviews/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v2-review-appendix-d.md) | v2.0 方案技术评审 |
| [reviews/v3.0 评审](reviews/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md) | v3.0 方案评审（批准实施） |

## 项目目标

1. **P0 问题修复**
   - SSHConnectionPool 懒初始化修复
   - backup_scheduler Session 生命周期修复

2. **P1 问题修复**
   - FastAPI lifespan 集成
   - arp_mac_scheduler AsyncIOScheduler 迁移
   - Session 异步适配

3. **P2 完善性优化**
   - pytest-asyncio 配置
   - 配置文件备份脚本
   - 数据一致性验证脚本

## 关键阻塞项

| 编号 | 内容 | 状态 |
|------|------|------|
| **R1** | FastAPI lifespan 完整实现 | ✅ 已规划 |
| **R2** | arp_mac_scheduler Session 异步适配 | ✅ 已规划 |
| **R3** | SSHConnectionPool 完整懒初始化调用点 | ✅ 已规划 |
| **R4** | backup_scheduler Session 生命周期修复 | ✅ 已规划 |

## 预计工时

**总计**: 8h

| 阶段 | 工时 |
|------|------|
| 阶段 0: 项目准备 | 0.5h |
| 阶段 1: P0 问题修复 | 1.5h |
| 阶段 2: P1 问题修复 | 3h |
| 阶段 3: P2 完善性优化 | 2h |
| 阶段 4: 测试验证 | 1h |

## 相关文件

| 文件 | 说明 |
|------|------|
| `app/services/ssh_connection_pool.py` | SSH 连接池（需要懒初始化改造） |
| `app/services/backup_scheduler.py` | 备份调度器（需要 AsyncIOScheduler 改造 + Session 修复） |
| `app/services/arp_mac_scheduler.py` | ARP/MAC 调度器（需要 AsyncIOScheduler 迁移 + Session 适配） |
| `app/services/ip_location_scheduler.py` | IP 定位调度器（可选迁移） |
| `app/main.py` | 主应用（需要改为 lifespan 模式） |

---

**创建日期**: 2026-03-31
**项目状态**: ⚪ 未开始