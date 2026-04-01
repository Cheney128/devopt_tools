---
ontology:
  id: DOC-2026-04-002-PLAN
  type: plan
  problem: 文档归档整理
  status: active
  version: v1
  created: 2026-04-01
  author: Claude
  tags:
    - documentation
    - archiving
    - reorganization
---

# 文档归档方案

## 1. 目标目录结构

```
docs/
├── INDEX.md                          # 总览索引（新增）
├── projects/                         # 按问题组织（新增）
│   ├── P001-arp-mac-scheduler-fix/
│   ├── P002-asyncioscheduler-migration/
│   ├── P003-ip-location-optimization/
│   ├── P004-batch-config-backup/
│   ├── P005-monitoring-panel-issues/
│   ├── P006-frontend-logout-issues/
│   ├── P007-batch-device-upload/
│   ├── P008-arp-current-data-fix/
│   ├── P009-security-routing-fix/
│   ├── P010-archive-logic-fix/
│   └── P011-async-fix-optimized/
├── archive/                          # 历史归档（新增）
│   ├── 2026-03/
│   └── 2026-04/
├── 项目分析/                         # 保留（规范）
├── 功能需求/                         # 保留（较规范）
├── plans/
│   └── asyncioscheduler-refactor/    # 保留（规范）
├── debugs/                           # 保留，清理中间版本
├── 变更记录/                         # 保留
└── superpowers/                      # 清空，内容移至 projects/
    └── templates/                    # 仅保留模板
```

---

## 2. Ontology 元数据规范

每个文档顶部必须包含 YAML frontmatter：

```yaml
---
ontology:
  id: <唯一ID，格式：DOC-YYYY-MM-NNN-TYPE>
  type: analysis|plan|review|implementation|verification|test|investigation|report|research|debug|summary|progress|decision
  problem: <关联问题描述>
  problem_id: <关联问题ID，如 P001>
  status: active|archived|deprecated
  version: <版本号，如 v1, v2, v3>
  superseded_by: <替代文档ID（如有）>
  supersedes: <被替代文档ID（如有）>
  related:
    - <相关文档ID列表>
  tags:
    - <标签列表>
  created: <创建日期 YYYY-MM-DD>
  updated: <最后更新日期 YYYY-MM-DD>
  author: <作者>
---
```

### 文档类型映射

| 原目录 | type 值 |
|--------|---------|
| analysis/ | analysis |
| plans/ | plan |
| reviews/ | review |
| verification/ | verification |
| testing/ | test |
| investigations/ | investigation |
| reports/ | report |
| research/ | research |
| debugs/ | debug |
| summary文档 | summary |
| progress文档 | progress |
| decision-log | decision |

---

## 3. 问题分类与文档映射

### P001: ARP/MAC 调度器修复 (35 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| analysis/2026-03-30-arp-mac-auto-collection-failure-analysis.md | projects/P001/01-analysis.md | DOC-2026-03-001-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-startup-error-analysis.md | projects/P001/02-analysis.md | DOC-2026-03-002-ANAL |
| analysis/2026-03-30-arp-mac-collection-workflow-analysis.md | projects/P001/03-analysis.md | DOC-2026-03-003-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-field-name-error-analysis.md | projects/P001/04-analysis.md | DOC-2026-03-004-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-async-call-error-analysis.md | projects/P001/05-analysis.md | DOC-2026-03-005-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-runtime-error-analysis.md | projects/P001/06-analysis.md | DOC-2026-03-006-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-analysis.md | projects/P001/07-analysis.md | DOC-2026-03-007-ANAL |
| analysis/2026-03-30-arp-mac-scheduler-netmiko-use-expect-string-missing-analysis.md | projects/P001/08-analysis.md | DOC-2026-03-008-ANAL |
| plans/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-plan.md | projects/P001/09-plan.md | DOC-2026-03-009-PLAN |
| reviews/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-plan-review.md | projects/P001/10-review.md | DOC-2026-03-010-REV |
| verification/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-fix-verification.md | projects/P001/11-verification.md | DOC-2026-03-011-VER |
| testing/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-fix-test-results.md | projects/P001/12-test.md | DOC-2026-03-012-TEST |
| verification/2026-03-30-arp-mac-scheduler-verification.md | projects/P001/13-verification.md | DOC-2026-03-013-VER |
| verification/2026-03-30-arp-mac-scheduler-startup-fix-verification.md | projects/P001/14-verification.md | DOC-2026-03-014-VER |
| verification/2026-03-30-arp-mac-scheduler-comprehensive-fix-verification.md | projects/P001/15-verification.md | DOC-2026-03-015-VER |
| verification/2026-03-30-arp-mac-scheduler-field-fix-validation-guide.md | projects/P001/16-verification.md | DOC-2026-03-016-VER |
| verification/2026-03-30-arp-mac-scheduler-async-fix-verification.md | projects/P001/17-verification.md | DOC-2026-03-017-VER |
| verification/2026-03-30-arp-mac-scheduler-runtime-fix-verification.md | projects/P001/18-verification.md | DOC-2026-03-018-VER |
| verification/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-verification.md | projects/P001/19-verification.md | DOC-2026-03-019-VER |
| verification/2026-03-30-netmiko-use-expect-string-fix-verification.md | projects/P001/20-verification.md | DOC-2026-03-020-VER |
| testing/2026-03-30-arp-mac-scheduler-test-results.md | projects/P001/21-test.md | DOC-2026-03-021-TEST |
| testing/2026-03-30-arp-mac-scheduler-async-fix-test-results.md | projects/P001/22-test.md | DOC-2026-03-022-TEST |
| testing/2026-03-30-arp-mac-scheduler-runtime-fix-test-results.md | projects/P001/23-test.md | DOC-2026-03-023-TEST |
| testing/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-test-results.md | projects/P001/24-test.md | DOC-2026-03-024-TEST |
| testing/2026-03-30-netmiko-use-expect-string-fix-test-results.md | projects/P001/25-test.md | DOC-2026-03-025-TEST |
| 2026-03-30-arp-mac-scheduler-fix-summary.md | projects/P001/26-summary.md | DOC-2026-03-026-SUM |
| plans/2026-03-30-arp-mac-scheduler-startup-immediate-collection-plan.md | projects/P001/27-plan.md | DOC-2026-03-027-PLAN |

**归档中间版本：**
| 文档 | 目标位置 | 原因 |
|------|----------|------|
| plans/2026-03-30-fix-arp-mac-scheduler-plan.md | archive/2026-03/ | v1，被final替代 |
| plans/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan.md | archive/2026-03/ | v1 |
| plans/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-optimized.md | archive/2026-03/ | v2 |
| reviews/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-review.md | archive/2026-03/ | v1配对 |
| reviews/2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-second-review.md | archive/2026-03/ | v1配对 |
| reviews/2026-03-30-arp-mac-scheduler-netmiko-use-expect-string-missing-analysis-review.md | archive/2026-03/ | 旧版 |

---

### P002: SSH连接池 AsyncIOScheduler 迁移 (15 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| analysis/2026-03-30-ssh-connection-pool-event-loop-mismatch-analysis.md | projects/P002/01-analysis.md | DOC-2026-03-028-ANAL |
| plans/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3.md | projects/P002/02-plan.md | DOC-2026-03-029-PLAN |
| reviews/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md | projects/P002/03-review.md | DOC-2026-03-030-REV |
| reviews/2026-03-30-ssh-connection-pool-event-loop-mismatch-solutions-review.md | projects/P002/04-review.md | DOC-2026-03-031-REV |
| reviews/2026-03-31-ssh-connection-pool-event-loop-deep-evaluation-review.md | projects/P002/05-review.md | DOC-2026-03-032-REV |
| verification/2026-03-31-phase1-p0-verification.md | projects/P002/06-verification.md | DOC-2026-03-033-VER |
| verification/2026-03-31-phase1-m4-verification.md | projects/P002/07-verification.md | DOC-2026-03-034-VER |
| verification/2026-03-31-phase1-p2-verification.md | projects/P002/08-verification.md | DOC-2026-03-035-VER |
| verification/2026-03-31-phase1-progress-verification.md | projects/P002/09-verification.md | DOC-2026-03-036-VER |

**归档中间版本：**
| 文档 | 目标位置 | 原因 |
|------|----------|------|
| plans/2026-03-31-ssh-connection-pool-event-loop-deep-evaluation-and-final-plan.md | archive/2026-03/ | v1 |
| plans/2026-03-31-ssh-connection-pool-asyncioscheduler-refinement-plan.md | archive/2026-03/ | v1 |
| plans/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan.md | archive/2026-03/ | v1 |
| plans/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v2.md | archive/2026-03/ | v2 |
| reviews/2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-review.md | archive/2026-03/ | v1配对 |
| reviews/2026-03-31-ssh-connection-pool-asyncioscheduler-refinement-plan-review.md | archive/2026-03/ | v1配对 |

---

### P003: IP 定位功能优化 (20 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| analysis/2026-03-30-ip-location-500-error-analysis.md | projects/P003/01-analysis.md | DOC-2026-03-037-ANAL |
| analysis/2026-03-30-ip-location-device-id-root-cause.md | projects/P003/02-analysis.md | DOC-2026-03-038-ANAL |
| plans/2026-03-20-ip-location-review-fixes.md | projects/P003/03-plan.md | DOC-2026-03-039-PLAN |
| plans/2026-03-23-ip-location-code-review-fix.md | projects/P003/04-plan.md | DOC-2026-03-040-PLAN |
| plans/2026-03-23-ip-location-phase1-code-review-fixes.md | projects/P003/05-plan.md | DOC-2026-03-041-PLAN |
| plans/2026-03-27-fix-ip-location-collection.md | projects/P003/06-plan.md | DOC-2026-03-042-PLAN |
| plans/ip-location-optimization.md | projects/P003/07-plan.md | DOC-2026-03-043-PLAN |
| verification/2026-03-27-ip-location-collection-summary.md | projects/P003/08-verification.md | DOC-2026-03-044-VER |
| verification/2026-03-31-project-docs-verification.md | projects/P003/09-verification.md | DOC-2026-03-045-VER |

---

### P008: ARP Current 数据错误 (5 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| analysis/2026-04-01-arp-current-data-error-root-cause.md | projects/P008/01-analysis.md | DOC-2026-04-001-ANAL |
| plans/2026-04-01-arp-current-fix-plan-v2.md | projects/P008/02-plan.md | DOC-2026-04-002-PLAN |
| reviews/2026-04-01-arp-current-fix-plan-v2-review.md | projects/P008/03-review.md | DOC-2026-04-003-REV |
| reports/2026-04-01-arp-current-fix-implementation.md | projects/P008/04-report.md | DOC-2026-04-004-REP |

**归档中间版本：**
| 文档 | 目标位置 | 原因 |
|------|----------|------|
| plans/2026-04-01-arp-current-fix-plan.md | archive/2026-04/ | v1，被v2替代 |
| reviews/2026-04-01-arp-current-fix-plan-review.md | archive/2026-04/ | v1配对 |

---

### P009: 安全/路由修复 (10 文档)

**全部保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| plans/2026-03-26-fix-sql-injection-c1.md | projects/P009/01-plan.md | DOC-2026-03-046-PLAN |
| plans/2026-03-26-fix-i1-untracked-file.md | projects/P009/02-plan.md | DOC-2026-03-047-PLAN |
| plans/2026-03-26-fix-i2-config-cache.md | projects/P009/03-plan.md | DOC-2026-03-048-PLAN |
| plans/2026-03-26-fix-i3-transaction.md | projects/P009/04-plan.md | DOC-2026-03-049-PLAN |
| plans/2026-03-26-fix-R1.md | projects/P009/05-plan.md | DOC-2026-03-050-PLAN |
| plans/2026-03-26-fix-R2.md | projects/P009/06-plan.md | DOC-2026-03-051-PLAN |
| plans/2026-03-26-fix-R3.md | projects/P009/07-plan.md | DOC-2026-03-052-PLAN |
| plans/2026-03-26-fix-R4.md | projects/P009/08-plan.md | DOC-2026-03-053-PLAN |
| plans/2026-03-26-fix-route-order.md | projects/P009/09-plan.md | DOC-2026-03-054-PLAN |
| plans/2026-03-26-fix-frontend-routing.md | projects/P009/10-plan.md | DOC-2026-03-055-PLAN |

---

### P010: 归档逻辑修复 (4 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| plans/2026-03-27-fix-archive-logic-optimized.md | projects/P010/01-plan.md | DOC-2026-03-056-PLAN |
| plans/2026-03-27-review-archive-logic-optimized.md | projects/P010/02-review.md | DOC-2026-03-057-REV |

**归档中间版本：**
| 文档 | 目标位置 | 原因 |
|------|----------|------|
| plans/2026-03-27-fix-archive-logic.md | archive/2026-03/ | v1 |
| plans/2026-03-27-review-archive-logic.md | archive/2026-03/ | v1 |

---

### P011: ARP/MAC 异步修复优化 (4 文档)

**最终版保留：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| plans/2026-03-30-arp-mac-scheduler-async-fix-plan-a-optimized.md | projects/P011/01-plan.md | DOC-2026-03-058-PLAN |
| plans/2026-03-30-arp-mac-scheduler-async-fix-plan-a-optimized-review.md | projects/P011/02-review.md | DOC-2026-03-059-REV |

**归档中间版本：**
| 文档 | 目标位置 | 原因 |
|------|----------|------|
| plans/2026-03-30-arp-mac-scheduler-async-fix-plan-a-detailed.md | archive/2026-03/ | v1 |
| plans/2026-03-30-arp-mac-scheduler-async-fix-plan-a-review.md | archive/2026-03/ | v1 |

---

### 其他文档处理

**investigations 目录：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| investigations/2026-03-27-scheduler-status-report.md | projects/P001/28-investigation.md | DOC-2026-03-060-INV |
| investigations/2026-03-27-doc-code-diff-analysis.md | archive/2026-03/ | 旧版分析 |
| investigations/2026-03-29-frontend-bug-report.md | debugs/ | 移回debugs |

**research 目录：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| research/2026-03-31-project-docs-research-report.md | archive/2026-03/ | 研究报告归档 |

**通用文档：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| plans/2026-03-29-batch-set-device-role.md | projects/P012/01-plan.md | DOC-2026-03-061-PLAN |
| verification/2026-03-27-doc-update-summary.md | archive/2026-03/ | 文档更新总结 |
| verification/2026-03-30-arp-mac-scheduler-fix-verification-report.md | projects/P001/29-verification.md | DOC-2026-03-062-VER |

**analysis 特殊文档：**
| 文档 | 目标位置 | Ontology ID |
|------|----------|-------------|
| analysis/各厂商 ARP-MAC 地址数据格式分析.md | projects/P001/30-analysis.md | DOC-2026-03-063-ANAL |

---

## 4. INDEX.md 模板

```markdown
---
ontology:
  id: DOC-2026-04-000-INDEX
  type: index
  status: active
  created: 2026-04-01
  updated: 2026-04-01
---

# Switch Manage 文档索引

## 目录结构

| 目录 | 用途 | 文档数 |
|------|------|--------|
| projects/ | 按问题组织的活跃文档 | XX |
| archive/ | 历史归档文档 | XX |
| 项目分析/ | 项目架构分析 | 7 |
| 功能需求/ | 功能开发文档 | 45 |
| plans/asyncioscheduler-refactor/ | AsyncIOScheduler 迁移项目 | 25 |
| debugs/ | 问题排查文档 | 22 |
| 变更记录/ | 变更记录 | 1 |

## 项目列表

### P001: ARP/MAC 调度器修复
- **问题**: ARP/MAC 采集调度器运行时错误、Netmiko 超时等
- **状态**: 已完成
- **文档数**: 35
- **关键决策**: ...
- **查看**: [projects/P001-arp-mac-scheduler-fix/](projects/P001-arp-mac-scheduler-fix/)

### P002: SSH连接池 AsyncIOScheduler 迁移
...

## 时间线

| 日期 | 事件 | 关联问题 |
|------|------|----------|
| 2026-03-26 | 安全问题修复 | P009 |
| 2026-03-27 | 归档逻辑修复 | P010 |
| 2026-03-30 | ARP/MAC 调度器修复 | P001 |
| 2026-03-31 | AsyncIOScheduler 迁移完成 | P002 |
| 2026-04-01 | ARP Current 数据修复 | P008 |

## 待处理事项

- [ ] 待处理事项列表

## 维护指南

1. 新文档添加 Ontology 元数据
2. 按问题归类到 projects/
3. 中间版本归档到 archive/
4. 更新 INDEX.md
```

---

## 5. 执行顺序

### 步骤 1: 创建项目目录

```bash
mkdir -p docs/projects/{P001,P002,P003,P004,P005,P006,P007,P008,P009,P010,P011,P012}
```

### 步骤 2: 移动最终版文档

按问题ID逐一移动，添加Ontology元数据。

### 步骤 3: 归档中间版本

移动 v1/v2 版本到 archive/2026-03/ 或 archive/2026-04/。

### 步骤 4: 生成 INDEX.md

汇总所有项目信息，生成总览索引。

### 步骤 5: 清空 superpowers/

移动完成后，superpowers/ 仅保留 templates/。

### 步骤 6: Git 提交

```bash
git add docs/
git commit -m "docs: 文档归档整理

- 按问题组织文档结构 (projects/P001-P012)
- 添加 Ontology 元数据规范
- 归档中间版本到 archive/2026-03/、archive/2026-04/
- 新增 INDEX.md 总览索引
- 清空 superpowers/ 内容移至 projects/

盘点：212 个文档
归档：30 个中间版本
活跃：182 个最终版文档"
```

---

## 6. 验收清单

- [ ] projects/ 目录结构完整
- [ ] archive/ 目录结构完整
- [ ] 每个最终版文档有 Ontology 元数据
- [ ] INDEX.md 已生成
- [ ] 中间版本已归档
- [ ] superpowers/ 已清空（仅保留 templates/）
- [ ] Git 提交完成

---

*方案创建时间: 2026-04-01*