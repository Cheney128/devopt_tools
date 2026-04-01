---
ontology:
  id: DOC-2026-04-001-INV
  type: inventory
  problem: 文档归档整理
  status: active
  created: 2026-04-01
  author: Claude
  tags:
    - documentation
    - inventory
    - archiving
---

# 文档盘点报告

## 盘点概览

| 类别 | 目录 | 文档数量 | 状态 |
|------|------|----------|------|
| superpowers | docs/superpowers/** | 92 | 需整理 |
| 功能需求 | docs/功能需求/** | 45 | 较规范 |
| debugs | docs/debugs/** | 22 | 需整理 |
| 项目分析 | docs/项目分析/** | 7 | 规范 |
| plans | docs/plans/** | 27 | 部分需整理 |
| 根目录 | docs/*.md | 17 | 需整理 |
| 变更记录 | docs/变更记录/** | 1 | 规范 |
| **总计** | - | **212** | - |

---

## 一、docs/superpowers/ 目录分析 (92个文档)

### 1.1 plans/ 目录 (37个文档)

**按问题归类：**

#### A. ARP/MAC 采集器相关 (16个)
| 文档名 | 类型 | 版本 | 关联问题 |
|--------|------|------|----------|
| 2026-03-30-fix-arp-mac-scheduler-plan.md | plan | v1 | ARP/MAC调度器修复 |
| 2026-03-30-arp-mac-scheduler-startup-immediate-collection-plan.md | plan | v1 | 启动即时采集 |
| 2026-03-30-arp-mac-scheduler-async-fix-plan-a-detailed.md | plan | v1 | 异步修复 |
| 2026-03-30-arp-mac-scheduler-async-fix-plan-a-review.md | review | v1 | 异步修复评审 |
| 2026-03-30-arp-mac-scheduler-async-fix-plan-a-optimized.md | plan | v2 | 异步修复优化 |
| 2026-03-30-arp-mac-scheduler-async-fix-plan-a-optimized-review.md | review | v2 | 异步修复优化评审 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan.md | plan | v1 | Netmiko超时修复 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-optimized.md | plan | v2 | Netmiko超时修复优化 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-plan.md | plan | v3 | Netmiko超时最终版 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-plan-review.md | review | v3 | Netmiko超时最终版评审 |
| 2026-03-27-fix-archive-logic.md | plan | v1 | 归档逻辑修复 |
| 2026-03-27-review-archive-logic.md | review | v1 | 归档逻辑评审 |
| 2026-03-27-fix-archive-logic-optimized.md | plan | v2 | 归档逻辑优化 |
| 2026-03-27-review-archive-logic-optimized.md | review | v2 | 归档逻辑优化评审 |
| 2026-04-01-arp-current-fix-plan.md | plan | v1 | ARP Current数据修复 |
| 2026-04-01-arp-current-fix-plan-v2.md | plan | v2 | ARP Current数据修复v2 |

#### B. SSH连接池/AsyncIOScheduler相关 (12个)
| 文档名 | 类型 | 版本 | 关联问题 |
|--------|------|------|----------|
| 2026-03-31-ssh-connection-pool-event-loop-deep-evaluation-and-final-plan.md | plan | v1 | SSH连接池评估 |
| 2026-03-31-ssh-connection-pool-event-loop-deep-evaluation-review.md | review | v1 | SSH连接池评估评审 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-refinement-plan.md | plan | v1 | AsyncIOScheduler细化 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-refinement-plan-review.md | review | v1 | AsyncIOScheduler细化评审 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan.md | plan | v1 | AsyncIOScheduler最终版 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-review.md | review | v1 | AsyncIOScheduler最终版评审 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v2.md | plan | v2 | AsyncIOScheduler最终版v2 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3.md | plan | v3 | AsyncIOScheduler最终版v3 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md | review | v3 | AsyncIOScheduler最终版v3评审 |

#### C. IP定位相关 (5个)
| 文档名 | 类型 | 版本 | 关联问题 |
|--------|------|------|----------|
| 2026-03-20-ip-location-review-fixes.md | plan | v1 | IP定位评审修复 |
| 2026-03-23-ip-location-code-review-fix.md | plan | v1 | IP定位代码评审 |
| 2026-03-23-ip-location-phase1-code-review-fixes.md | plan | v1 | IP定位Phase1修复 |
| ip-location-optimization.md | plan | v1 | IP定位优化 |
| 2026-03-27-fix-ip-location-collection.md | plan | v1 | IP定位采集修复 |

#### D. 安全/路由修复 (9个)
| 文档名 | 类型 | 版本 | 关联问题 |
|--------|------|------|----------|
| 2026-03-26-fix-sql-injection-c1.md | plan | v1 | SQL注入修复 |
| 2026-03-26-fix-i1-untracked-file.md | plan | v1 | 未追踪文件修复 |
| 2026-03-26-fix-i2-config-cache.md | plan | v1 | 配置缓存修复 |
| 2026-03-26-fix-i3-transaction.md | plan | v1 | 事务修复 |
| 2026-03-26-fix-R1.md | plan | v1 | R1修复 |
| 2026-03-26-fix-R2.md | plan | v1 | R2修复 |
| 2026-03-26-fix-R3.md | plan | v1 | R3修复 |
| 2026-03-26-fix-R4.md | plan | v1 | R4修复 |
| 2026-03-26-fix-route-order.md | plan | v1 | 路由顺序修复 |
| 2026-03-26-fix-frontend-routing.md | plan | v1 | 前端路由修复 |

#### E. 设备角色批量设置 (1个)
| 文档名 | 类型 | 版本 | 关联问题 |
|--------|------|------|----------|
| 2026-03-29-batch-set-device-role.md | plan | v1 | 批量设置设备角色 |

**问题：**
- 同一问题存在多个版本（v1/v2/v3）
- plan和review分散在不同文件

---

### 1.2 analysis/ 目录 (14个文档)

| 文档名 | 关联问题 | 类型 |
|--------|----------|------|
| 2026-03-30-ip-location-500-error-analysis.md | IP定位500错误 | analysis |
| 2026-03-30-ip-location-device-id-root-cause.md | IP定位设备ID | root-cause |
| 2026-03-30-arp-mac-auto-collection-failure-analysis.md | ARP/MAC采集失败 | analysis |
| 2026-03-30-arp-mac-scheduler-startup-error-analysis.md | ARP/MAC启动错误 | analysis |
| 2026-03-30-arp-mac-collection-workflow-analysis.md | ARP/MAC工作流 | analysis |
| 2026-03-30-arp-mac-scheduler-field-name-error-analysis.md | ARP/MAC字段名错误 | analysis |
| 2026-03-30-arp-mac-scheduler-fix-verification-report.md | ARP/MAC修复验证 | verification |
| 2026-03-30-arp-mac-scheduler-async-call-error-analysis.md | ARP/MAC异步调用错误 | analysis |
| 2026-03-30-arp-mac-scheduler-runtime-error-analysis.md | ARP/MAC运行时错误 | analysis |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-analysis.md | Netmiko超时分析 | analysis |
| 2026-03-30-arp-mac-scheduler-netmiko-use-expect-string-missing-analysis.md | Netmiko expect_string缺失 | analysis |
| 2026-03-30-ssh-connection-pool-event-loop-mismatch-analysis.md | SSH连接池事件循环 | analysis |
| 各厂商 ARP-MAC 地址数据格式分析.md | ARP/MAC数据格式 | analysis |
| 2026-04-01-arp-current-data-error-root-cause.md | ARP Current数据错误 | root-cause |

---

### 1.3 reviews/ 目录 (14个文档)

| 文档名 | 关联Plan | 状态 |
|--------|----------|------|
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-review.md | Netmiko超时修复v1 | 配对 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-plan-second-review.md | Netmiko超时修复v1 | 配对 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-plan-review.md | Netmiko超时修复v3 | 配对 |
| 2026-03-30-arp-mac-scheduler-netmiko-use-expect-string-missing-analysis-review.md | Netmiko expect_string | 配对 |
| 2026-03-30-ssh-connection-pool-event-loop-mismatch-solutions-review.md | SSH连接池 | 配对 |
| 2026-03-31-ssh-connection-pool-event-loop-deep-evaluation-review.md | SSH连接池评估 | 配对 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-refinement-plan-review.md | AsyncIOScheduler细化 | 配对 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-review.md | AsyncIOScheduler最终版v1 | 配对 |
| 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md | AsyncIOScheduler最终版v3 | 配对 |
| 2026-04-01-arp-current-fix-plan-review.md | ARP Current修复v1 | 配对 |
| 2026-04-01-arp-current-fix-plan-v2-review.md | ARP Current修复v2 | 配对 |

---

### 1.4 verification/ 目录 (17个文档)

| 文档名 | 关联问题 | 类型 |
|--------|----------|------|
| 2026-03-27-ip-location-collection-summary.md | IP定位采集 | verification |
| 2026-03-27-doc-update-summary.md | 文档更新 | verification |
| 2026-03-30-arp-mac-scheduler-verification.md | ARP/MAC调度器 | verification |
| 2026-03-30-arp-mac-scheduler-startup-fix-verification.md | ARP/MAC启动修复 | verification |
| 2026-03-30-arp-mac-scheduler-comprehensive-fix-verification.md | ARP/MAC综合修复 | verification |
| 2026-03-30-arp-mac-scheduler-field-fix-validation-guide.md | ARP/MAC字段修复 | verification |
| 2026-03-30-arp-mac-scheduler-async-fix-verification.md | ARP/MAC异步修复 | verification |
| 2026-03-30-arp-mac-scheduler-runtime-fix-verification.md | ARP/MAC运行时修复 | verification |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-verification.md | Netmiko超时修复 | verification |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-fix-verification.md | Netmiko超时最终修复 | verification |
| 2026-03-30-netmiko-use-expect-string-fix-verification.md | Netmiko expect_string | verification |
| 2026-03-31-project-docs-verification.md | 项目文档 | verification |
| 2026-03-31-phase1-p0-verification.md | Phase1 P0 | verification |
| 2026-03-31-phase1-m4-verification.md | Phase1 M4 | verification |
| 2026-03-31-phase1-p2-verification.md | Phase1 P2 | verification |
| 2026-03-31-phase1-progress-verification.md | Phase1进度 | verification |

---

### 1.5 testing/ 目录 (6个文档)

| 文档名 | 关联问题 |
|--------|----------|
| 2026-03-30-arp-mac-scheduler-test-results.md | ARP/MAC调度器测试 |
| 2026-03-30-arp-mac-scheduler-async-fix-test-results.md | ARP/MAC异步修复测试 |
| 2026-03-30-arp-mac-scheduler-runtime-fix-test-results.md | ARP/MAC运行时修复测试 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-fix-test-results.md | Netmiko超时修复测试 |
| 2026-03-30-arp-mac-scheduler-netmiko-readtimeout-final-fix-test-results.md | Netmiko超时最终修复测试 |
| 2026-03-30-netmiko-use-expect-string-fix-test-results.md | Netmiko expect_string测试 |

---

### 1.6 investigations/ 目录 (3个文档)

| 文档名 | 关联问题 |
|--------|----------|
| 2026-03-27-scheduler-status-report.md | 调度器状态 |
| 2026-03-27-doc-code-diff-analysis.md | 文档代码差异 |
| 2026-03-29-frontend-bug-report.md | 前端Bug |

---

### 1.7 reports/ 目录 (1个文档)

| 文档名 | 关联问题 |
|--------|----------|
| 2026-04-01-arp-current-fix-implementation.md | ARP Current修复实施 |

---

### 1.8 research/ 目录 (1个文档)

| 文档名 | 关联问题 |
|--------|----------|
| 2026-03-31-project-docs-research-report.md | 项目文档研究 |

---

### 1.9 根目录文档 (1个)

| 文档名 | 关联问题 |
|--------|----------|
| 2026-03-30-arp-mac-scheduler-fix-summary.md | ARP/MAC调度器修复总结 |

---

## 二、docs/plans/ 目录分析 (27个文档)

### 2.1 asyncioscheduler-refactor 子目录 (25个文档)

这是一个较为规范的项目目录，包含完整的阶段文档。

**目录结构：**
```
asyncioscheduler-refactor/
├── README.md                          # 项目总览
├── Progress.md                        # 进度跟踪
├── plans/                             # 方案文档
│   ├── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3.md
│   ├── 2026-03-31-phase1-code-review-fix-plan.md
│   ├── 2026-03-31-phase1-supplement-fix-plan.md
│   ├── 2026-03-31-x1-x3-supplement-issue-verification-fix-plan.md
│   ├── 2026-03-31-phase1-x1-x3-fix-plan.md
│   ├── 2026-03-31-phase1-merged-plan.md
├── reviews/                           # 评审文档
│   ├── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v3-review.md
│   ├── 2026-03-31-phase1-code-review.md
│   ├── 2026-03-31-phase1-code-review-supplement.md
│   ├── 2026-03-31-comprehensive-plan-review.md
│   ├── 2026-03-31-phase1-code-review-issues.md
│   ├── 2026-03-31-ssh-connection-pool-asyncioscheduler-final-plan-v2-review-appendix-d.md
├── tests/                             # 测试文档
│   ├── phase1-test-report.md
│   ├── phase1-verification-report.md
├── verification/                      # 验证文档
│   ├── 2026-03-31-phase1-p0-verification.md
│   ├── 2026-03-31-phase1-m4-verification.md
│   ├── 2026-03-31-phase1-p2-verification.md
│   ├── 2026-03-31-phase1-progress-verification.md
└── phase1-completion-summary.md       # 完成总结
```

**评估：** 该目录结构规范，可保留现有组织方式，仅需添加Ontology元数据。

### 2.2 plans 根目录 (2个文档)

| 文档名 | 类型 | 状态 |
|--------|------|------|
| progress.md | progress | 通用 |
| 2026-03-23-phase-9-审查问题修复闭环.md | plan | Phase9 |
| 2026-03-24-phase-10-device-role-全链路打通.md | plan | Phase10 |
| 2026-03-24-ip-location-ver3-实施计划.md | plan | IP定位v3 |

---

## 三、docs/功能需求/ 目录分析 (45个文档)

### 3.1 批量配置备份功能 (18个文档)

```
前端/plans/批量配置备份功能/
├── 配置管理模块问题分析与优化方案.md
├── 配置管理模块问题分析与优化方案-评审文档.md
├── 功能开发总结.md
├── Phase1-修复设备列表显示问题/
│   ├── 实施计划.md
│   ├── Phase1-修复设备列表显示问题-评审文档.md
├── Phase2-批量备份功能/
│   ├── Phase2-批量备份功能-评审文档.md
│   ├── 实施计划.md
│   ├── 实施报告.md
├── Phase3-备份计划监控面板/
│   ├── Phase3-备份计划监控面板-评审文档.md
│   ├── 实施计划.md
│   ├── 实施报告.md
│   ├── 前端无监控面板-问题分析报告-技术审查.md
│   ├── 前端无监控面板-问题分析及修复方案.md
│   ├── 前端测试报告.md
│   ├── 备份监控-前端控制台报错：信息获取失败.md
│   ├── 数据库自动迁移解决方案.md
```

**评估：** 结构较规范，按Phase组织，可保留。

### 3.2 监控面板问题反馈 (9个文档)

```
监控面板问题反馈/
├── 备份计划监控面板问题解决方案.md
├── 备份计划监控面板问题解决方案-评审报告.md
├── 备份计划监控面板问题解决方案-第二轮评审报告.md
├── 备份计划监控面板问题解决方案-评审报告-kimi.md
├── 备份计划监控面板问题解决方案-评审报告-kimi-v2.md
├── 实施后问题分析报告.md
├── 实施后问题分析报告-评审报告.md
├── 测试报告.md
```

**问题：** 多个评审版本并存，需要清理。

### 3.3 前端页面频繁登出 (4个文档)

```
前端页面频繁登出/
├── 问题分析与解决方案.md
├── 前端页面频繁登出解决方案-评审.md
├── 测试报告.md
├── code-review-report.md
```

**评估：** 结构规范。

### 3.4 IP定位Phase1 (8个文档)

```
ip-localtion-phase1-核心交换机下联IP优化/
├── ISSUE-数据库device_role字段缺失导致多个模块报错.md
├── IMPLEMENTATION-PLAN-自动数据库迁移机制.md
├── IMPLEMENTATION-PLAN-本地核验问题修复闭环.md
├── IP定位优化-核心交换机下联IP-整体设计.md
├── Phase-10-设备角色全链路打通.md
├── Phase-9-审查问题修复闭环.md
├── code-review-report.md
├── PROGRESS.md
```

**评估：** 结构规范。

### 3.5 IP定位ver3 (8个文档)

```
ip-location-ver3/
├── 整体架构设计.md
├── Phase-1-数据模型与快照分层.md
├── Phase-2-定位计算引擎.md
├── Phase-3-采集与增量刷新.md
├── Phase-4-查询API与前端接入.md
├── Phase-5-一致性校验与回滚机制.md
├── PROGRESS.MD
```

**评估：** 结构规范，按Phase组织。

---

## 四、docs/debugs/ 目录分析 (22个文档)

### 4.1 根目录 (12个文档)

| 文档名 | 类型 | 日期 |
|--------|------|------|
| command-template-errors.md | debug | - |
| command-execution-task-record.md | debug | - |
| ssh-connection-analysis-report.md | debug | - |
| full-chain-test-report-2026-02-01.md | debug | 2026-02-01 |
| command-execution-debug-report.md | debug | - |
| command-execution-test-summary.md | debug | - |
| linux docker未连接生产数据库问题排查.md | debug | - |
| docker环境 前端页面登录验证码显示异常.md | debug | - |
| 2026-03-23-IP定位优化功能本地运行问题分析报告.md | debug | 2026-03-23 |
| 2026-03-23-IP定位功能异常修复报告.md | debug | 2026-03-23 |
| 2026-03-26-常见问题根因分析与修复指南.md | debug | 2026-03-26 |
| 2026-03-26-IP定位模块故障根因分析与修复计划.md | debug | 2026-03-26 |

### 4.2 20260205 子目录 (10个文档)

```
20260205/
├── 修改文件后，前端登录报错/
│   └── 前端登录报错问题-项目知识文档.md
├── 前端页面-设备管理-批量设备上传失效/
│   ├── 批量上传失效-原因分析及修复方案.md
│   ├── 评审文档-v1.md
│   ├── 批量上传失效-优化修复方案-v2.md
│   ├── 评审文档-v2.md
│   ├── 批量上传失效-优化修复方案-v3.md
│   ├── 评审文档-v3.md
│   ├── 修复总结文档.md
├── 远程服务器问题排查/
    ├── 批量上传502错误排查总结-20260205.md
    ├── 验证码无法显示问题排查-20260206.md
    ├── 20260206-批量上传功能修复与环境配置优化.md
```

**问题：** 多个v1/v2/v3版本并存。

---

## 五、docs/项目分析/ 目录 (7个文档)

| 文档名 | 类型 | 状态 |
|--------|------|------|
| 01-项目架构分析.md | analysis | 规范 |
| 02-技术栈分析.md | analysis | 规范 |
| 03-API接口分析.md | analysis | 规范 |
| 04-数据库模型分析.md | analysis | 规范 |
| 05-前端架构分析.md | analysis | 规范 |
| 06-部署架构分析.md | analysis | 规范 |
| 07.ISSUES.MD | issues | 规范 |

**评估：** 结构规范，编号有序。

---

## 六、docs根目录零散文档 (17个文档)

| 文档名 | 类型 | 应归类 |
|--------|------|--------|
| command-execution-analysis.md | analysis | debugs |
| issue_template_creation_error.md | debug | debugs |
| commit-message.txt | misc | archive |
| decision-log-2026-03-24.md | decision | decisions |
| decision-log.md | decision | decisions |
| ip-location-optimization-plan.md | plan | 功能需求 |
| frontend-analysis.md | analysis | 项目分析 |
| login-and-captcha-fix-report.md | fix | debugs |
| project_analysis.md | analysis | 项目分析 |
| diff-change.md | change | 变更记录 |
| ip-location-optimization-summary.md | summary | 功能需求 |
| verification-report-2026-03-26.md | verification | verification |
| browser-verification-plan.md | verification | verification |
| browser-verification-result.md | verification | verification |
| browser-ip-location-verification.md | verification | verification |
| PROJECT_PROGRESS_2026-03-29.md | progress | progress |
| p2_optimization_verification_report.md | verification | verification |

---

## 七、问题归类汇总

### 主要问题类别：

| 问题ID | 问题名称 | 文档数 | 主要目录 |
|--------|----------|--------|----------|
| P001 | ARP/MAC调度器修复 | 35 | superpowers |
| P002 | SSH连接池AsyncIOScheduler | 15 | superpowers/plans |
| P003 | IP定位功能优化 | 20 | 功能需求/superpowers |
| P004 | 批量配置备份 | 18 | 功能需求 |
| P005 | 监控面板问题 | 9 | 功能需求 |
| P006 | 前端频繁登出 | 4 | 功能需求 |
| P007 | 批量设备上传 | 10 | debugs |
| P008 | ARP Current数据错误 | 5 | superpowers |
| P009 | 安全/路由修复 | 10 | superpowers |

---

## 八、归档建议

### 8.1 需归档的中间版本

| 原文档 | 保留版本 | 归档版本 |
|--------|----------|----------|
| ARP/MAC Netmiko超时修复 | v3 (final) | v1, v2 |
| AsyncIOScheduler迁移 | v3 | v1, v2 |
| ARP Current数据修复 | v2 | v1 |
| 归档逻辑修复 | v2 (optimized) | v1 |
| ARP/MAC异步修复 | v2 (optimized) | v1 |
| 批量上传修复 | v3 | v1, v2 |
| 监控面板评审 | kimi-v2 | 其他版本 |

### 8.2 目录重组建议

**保留现有结构：**
- docs/项目分析/ - 规范
- docs/功能需求/ - 较规范
- docs/plans/asyncioscheduler-refactor/ - 规范

**需要重组：**
- docs/superpowers/ - 按问题归类到 projects/
- docs/debugs/ - 合理归档历史版本
- docs根目录零散文档 - 移入相应目录

---

## 九、下一步行动

1. 创建 `docs/projects/` 目录
2. 按问题ID归类文档
3. 移动中间版本到 `docs/archive/2026-04/`
4. 为每个文档添加Ontology元数据
5. 创建 `docs/INDEX.md` 总览索引

---

*盘点完成时间: 2026-04-01*