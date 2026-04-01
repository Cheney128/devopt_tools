---
ontology:
  id: DOC-2026-04-000-INDEX
  type: index
  status: active
  created: 2026-04-01
  updated: 2026-04-01
  author: Claude
  tags:
    - documentation
    - index
---

# Switch Manage 文档索引

> 本索引提供项目文档的完整概览，按问题类别组织。

## 目录结构

| 目录 | 用途 | 文档数 | 状态 |
|------|------|--------|------|
| `projects/` | 按问题组织的活跃文档 | ~182 | 新增 |
| `archive/` | 历史归档文档（中间版本） | ~30 | 新增 |
| `项目分析/` | 项目架构分析文档 | 7 | 规范 |
| `功能需求/` | 功能开发文档 | 45 | 较规范 |
| `plans/asyncioscheduler-refactor/` | AsyncIOScheduler 迁移项目 | 25 | 规范 |
| `debugs/` | 问题排查文档 | 22 | 保留 |
| `变更记录/` | 变更记录 | 1 | 规范 |

---

## 项目列表

### P001: ARP/MAC 调度器修复

| 属性 | 值 |
|------|-----|
| **问题描述** | ARP/MAC 采集调度器运行时错误、Netmiko 超时、字段名错误等 |
| **状态** | 已完成 |
| **创建日期** | 2026-03-30 |
| **文档数** | 35 |
| **关键决策** | 使用 expect_string 替代 timeout；重构调度器生命周期管理 |

**文档类型分布：**
- analysis: 8
- plan: 2
- review: 1
- verification: 10
- test: 6
- investigation: 1
- summary: 1

**查看目录：** [`projects/P001-arp-mac-scheduler-fix/`](projects/P001-arp-mac-scheduler-fix/)

---

### P002: SSH连接池 AsyncIOScheduler 迁移

| 属性 | 值 |
|------|-----|
| **问题描述** | SSH连接池事件循环不匹配，迁移到 AsyncIOScheduler |
| **状态** | 已完成 |
| **创建日期** | 2026-03-30 |
| **文档数** | 15 |
| **关键决策** | 移除 BackgroundScheduler，使用 AsyncIOScheduler 管理周期任务 |

**文档类型分布：**
- analysis: 1
- plan: 1
- review: 4
- verification: 4

**查看目录：** [`projects/P002-asyncioscheduler-migration/`](projects/P002-asyncioscheduler-migration/)

---

### P003: IP 定位功能优化

| 属性 | 值 |
|------|-----|
| **问题描述** | IP定位500错误、设备ID根因分析、Phase1代码修复 |
| **状态** | 进行中 |
| **创建日期** | 2026-03-20 |
| **文档数** | 20 |
| **关键决策** | 核心交换机下联IP定位优化 |

**查看目录：** [`projects/P003-ip-location-optimization/`](projects/P003-ip-location-optimization/)

---

### P004: 批量配置备份功能

| 属性 | 值 |
|------|-----|
| **问题描述** | 配置管理模块批量备份功能开发 |
| **状态** | 已完成 |
| **文档数** | 18 |
| **位置** | [`功能需求/前端/plans/批量配置备份功能/`](功能需求/前端/plans/批量配置备份功能/) |

---

### P005: 监控面板问题

| 属性 | 值 |
|------|-----|
| **问题描述** | 备份计划监控面板显示问题 |
| **状态** | 已完成 |
| **文档数** | 9 |
| **位置** | [`功能需求/监控面板问题反馈/`](功能需求/监控面板问题反馈/) |

---

### P006: 前端频繁登出

| 属性 | 值 |
|------|-----|
| **问题描述** | 前端页面频繁登出问题 |
| **状态** | 已完成 |
| **文档数** | 4 |
| **位置** | [`功能需求/前端页面频繁登出/`](功能需求/前端页面频繁登出/) |

---

### P007: 批量设备上传

| 属性 | 值 |
|------|-----|
| **问题描述** | 批量设备上传功能失效、502错误 |
| **状态** | 已完成 |
| **文档数** | 10 |
| **位置** | [`debugs/20260205/前端页面-设备管理-批量设备上传失效/`](debugs/20260205/前端页面-设备管理-批量设备上传失效/) |

---

### P008: ARP Current 数据错误

| 属性 | 值 |
|------|-----|
| **问题描述** | ARP Current 表数据 vendor 字段大小写不一致导致查询错误 |
| **状态** | 已完成 |
| **创建日期** | 2026-04-01 |
| **文档数** | 5 |
| **关键决策** | 统一 vendor 字段为小写 |

**文档类型分布：**
- analysis: 1 (root-cause)
- plan: 1 (v2)
- review: 1 (v2)
- report: 1 (implementation)

**查看目录：** [`projects/P008-arp-current-data-fix/`](projects/P008-arp-current-data-fix/)

---

### P009: 安全/路由修复

| 属性 | 值 |
|------|-----|
| **问题描述** | SQL注入、配置缓存、事务、路由顺序等问题修复 |
| **状态** | 已完成 |
| **创建日期** | 2026-03-26 |
| **文档数** | 10 |

**修复项：**
- C1: SQL注入
- I1-I3: 未追踪文件、配置缓存、事务
- R1-R4: 路由问题
- 前端路由

**查看目录：** [`projects/P009-security-routing-fix/`](projects/P009-security-routing-fix/)

---

### P010: 归档逻辑修复

| 属性 | 值 |
|------|-----|
| **问题描述** | ARP/MAC 归档逻辑修复 |
| **状态** | 已完成 |
| **文档数** | 4 |

**查看目录：** [`projects/P010-archive-logic-fix/`](projects/P010-archive-logic-fix/)

---

### P011: ARP/MAC 异步修复优化

| 属性 | 值 |
|------|-----|
| **问题描述** | ARP/MAC 调度器异步调用错误修复 |
| **状态** | 已完成 |
| **文档数** | 4 |

**查看目录：** [`projects/P011-async-fix-optimized/`](projects/P011-async-fix-optimized/)

---

### P012: 批量设置设备角色

| 属性 | 值 |
|------|-----|
| **问题描述** | 批量设置设备角色功能 |
| **状态** | 已完成 |
| **文档数** | 1 |

**查看目录：** [`projects/P012-batch-device-role/`](projects/P012-batch-device-role/)

---

## 时间线

| 日期 | 事件 | 关联问题 |
|------|------|----------|
| 2026-02-01 | 全链路测试报告 | P007 |
| 2026-02-05 | 批量上传502错误排查 | P007 |
| 2026-02-06 | 验证码显示问题排查 | P007 |
| 2026-03-20 | IP定位评审修复 | P003 |
| 2026-03-23 | IP定位 Phase1 代码修复 | P003 |
| 2026-03-24 | IP定位 ver3 实施计划 | P003 |
| 2026-03-26 | 安全问题修复（C1/I1-I3/R1-R4） | P009 |
| 2026-03-27 | 归档逻辑修复、IP定位采集修复 | P010, P003 |
| 2026-03-29 | 批量设置设备角色 | P012 |
| 2026-03-30 | ARP/MAC 调度器修复、SSH连接池分析 | P001, P002 |
| 2026-03-31 | AsyncIOScheduler 迁移完成 | P002 |
| 2026-04-01 | ARP Current 数据修复 | P008 |
| 2026-04-01 | 文档归档整理 | DOC归档 |

---

## 归档说明

### archive/ 目录结构

```
archive/
├── 2026-03/           # 2026年3月的中间版本
│   ├── plans/         # 计划文档中间版本
│   ├── reviews/       # 评审文档中间版本
│   └── research/      # 研究报告
└── 2026-04/           # 2026年4月的中间版本
│   ├── plans/
│   └── reviews/
```

### 归档原则

1. **保留最终版**：每个问题保留最终实施的版本
2. **归档中间版本**：v1/v2 等中间版本移至 archive/
3. **添加 Ontology 元数据**：每个文档标明版本关系（supersedes/superseded_by）

---

## 维护指南

### 新文档添加流程

1. 创建文档时添加 Ontology 元数据
2. 按问题归类到对应 `projects/PXXX-xxx/` 目录
3. 如有中间版本，归档旧版本到 `archive/YYYY-MM/`
4. 更新本 INDEX.md 文件

### Ontology 元数据规范

```yaml
---
ontology:
  id: DOC-YYYY-MM-NNN-TYPE    # 唯一ID
  type: analysis|plan|review|implementation|verification|test|...
  problem: <问题描述>
  problem_id: <PXXX>
  status: active|archived|deprecated
  version: <v1|v2|v3>
  superseded_by: <替代文档ID>
  supersedes: <被替代文档ID>
  related: [<相关文档ID>]
  tags: [<标签>]
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  author: <作者>
---
```

### 文档类型缩写

| TYPE | 缩写 | 说明 |
|------|------|------|
| analysis | ANAL | 分析文档 |
| plan | PLAN | 计划文档 |
| review | REV | 评审文档 |
| verification | VER | 验证文档 |
| test | TEST | 测试文档 |
| investigation | INV | 调查文档 |
| report | REP | 报告文档 |
| research | RES | 研究文档 |
| summary | SUM | 总结文档 |
| progress | PROG | 进度文档 |
| decision | DEC | 决策文档 |
| debug | DBG | 调试文档 |
| inventory | INV | 盘点文档 |
| index | IDX | 索引文档 |

---

## 相关文档

- [盘点报告](archive/2026-04-01-document-inventory.md)
- [归档方案](archive/2026-04-01-archiving-plan.md)

---

*索引创建时间: 2026-04-01*