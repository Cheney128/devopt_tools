---
ontology:
  id: DOC-2026-03-007-PLAN
  type: plan
  problem: 安全/路由修复
  problem_id: P009
  status: active
  created: 2026-03-26
  updated: 2026-03-26
  author: Claude
  tags:
    - documentation
---
# R3 修复计划：用户管理跳转登录

**创建日期**: 2026-03-26  
**优先级**: P1  
**问题**: 访问用户管理页面时跳转登录  
**根因**: 用户权限配置问题

---

## 问题分析

根据任务描述，访问用户管理页面时跳转登录，可能原因：
1. 当前登录用户没有 admin 角色
2. /auth/me API 返回的用户信息缺少 is_superuser 字段
3. 前端权限检查逻辑有问题

---

## 修复流程 (TDD)

### 步骤 1: 编写测试用例
创建 `tests/unit/test_regression_r3.py`：
- 测试用户管理路由是否配置 requiresAdmin
- 测试前端 authStore 是否正确检查 isAdmin
- 测试后端 /auth/me API 是否返回角色信息

### 步骤 2: 检查代码
- 检查前端路由配置
- 检查前端 authStore
- 检查后端认证 API

### 步骤 3: 修复代码
- 修复权限检查逻辑
- 提交代码

### 步骤 4: 运行测试 (预期通过 - 绿)
确认所有测试通过

### 步骤 5: Git 提交
```bash
git add <相关.files>
git commit -m "fix: 用户管理权限检查 (R3)"
```

---

## 验收标准

1. ✅ 前端路由配置 requiresAdmin 正确
2. ✅ authStore 正确解析 isAdmin 字段
3. ✅ 后端 /auth/me API 返回用户角色信息
4. ✅ admin 用户能访问用户管理页面
5. ✅ 测试用例全部通过

---

## 风险与回滚

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 权限逻辑错误 | 低 | 中 | 仔细检查条件判断 |
| API 返回格式变化 | 低 | 中 | 检查 API 响应 |

**回滚方案**: `git reset --hard HEAD~1`

---

## 执行记录

_(执行过程中填写)_

- [ ] 测试用例已创建
- [ ] 代码检查完成
- [ ] 代码已修复
- [ ] 测试运行 (绿)
- [ ] Git 已提交
