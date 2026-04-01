---
ontology:
  id: DOC-2026-03-010-PLAN
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
# 修复计划：前端路由跳转问题

**创建日期**: 2026-03-26  
**优先级**: P0  
**问题**: 
1. IP 定位模块白屏 + URL 跳转错误
2. 用户管理跳转回首页

---

## 问题分析

### 问题 1: IP 定位模块白屏
**现象**:
- 点击 IP 定位菜单，URL 跳转到 `http://localhost:5173/search`
- 正确应该是 `http://localhost:5173/ip-location/search`
- 页面白屏

**可能根因**:
- 前端路由配置中 tab 路径配置错误
- 缺少 `/ip-location` 前缀

### 问题 2: 用户管理跳转
**现象**:
- 点击用户管理跳转到 `http://localhost:5173/`
- 正确应该是 `http://localhost:5173/users`

**可能根因**:
- 路由守卫检查 `authStore.isAdmin` 返回 false
- 当前登录用户没有 admin 角色
- authStore 初始化逻辑问题

---

## 修复流程 (TDD)

### 步骤 1: 编写测试用例
创建 `tests/unit/test_frontend_routing.py`:
- 测试 IP 定位路由配置
- 测试用户管理路由权限
- 测试 authStore isAdmin 逻辑

### 步骤 2: 检查代码
- 检查 `frontend/src/views/ip-location/IPLocationIndex.vue` 中的 tabs 配置
- 检查 `frontend/src/router/index.js` 中的路由守卫
- 检查 `frontend/src/stores/authStore.js` 中的 isAdmin 计算属性

### 步骤 3: 修复代码
- 修复 IP 定位 tab 路径
- 修复用户管理权限检查

### 步骤 4: Git 提交
```bash
git add <相关.files>
git commit -m "fix: 前端路由跳转问题 (IP 定位/用户管理)"
```

---

## 验收标准

1. ✅ 点击 IP 定位菜单，URL 为 `/ip-location/search`
2. ✅ IP 定位页面正常显示，不白屏
3. ✅ admin 用户点击用户管理，URL 为 `/users`
4. ✅ 非 admin 用户点击用户管理，显示权限不足提示

---

## 执行记录

_(执行过程中填写)_

- [ ] 测试用例已创建
- [ ] 代码检查完成
- [ ] 代码已修复
- [ ] Git 已提交
