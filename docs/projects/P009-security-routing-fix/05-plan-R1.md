---
ontology:
  id: DOC-2026-03-005-PLAN
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
# R1 修复计划：IP 定位模块消失

**创建日期**: 2026-03-26  
**优先级**: P0  
**问题**: IP 定位模块在前端消失  
**根因**: 前端代码未提交到 Git

---

## 问题分析

根据 git status，工作区有以下 IP 定位相关未提交代码：

### 后端代码
- `app/api/endpoints/ip_location.py` - IP 定位 API 端点
- `app/schemas/ip_location_schemas.py` - IP 定位数据模型

### 前端代码
- `frontend/src/views/ip-location/` - IP 定位视图组件
- `frontend/src/components/ip-location/` - IP 定位通用组件
- `frontend/src/utils/` - 工具函数（可能包含 IP 定位相关）
- `frontend/src/api/index.js` - API 调用（已修改）
- `frontend/src/router/index.js` - 路由配置（已修改）
- `frontend/src/App.vue` - 主应用（已修改，可能包含菜单）

---

## 修复流程 (TDD)

### 步骤 1: 编写测试用例
创建 `tests/unit/test_regression_r1.py`：
- 测试前端路由是否包含 IP 定位页面
- 测试 API 端点是否存在
- 测试菜单配置是否包含 IP 定位

### 步骤 2: 运行测试 (预期失败 - 红)
确认测试在未提交代码的情况下失败

### 步骤 3: 修复代码
- 检查前端代码完整性：
  - 路由配置是否正确
  - 菜单配置是否正确
  - 组件是否完整
  - API 调用是否正确
- 如不完整则补全
- 如完整则直接提交

### 步骤 4: 运行测试 (预期通过 - 绿)
确认所有测试通过

### 步骤 5: Git 提交
```bash
git add <相关.files>
git commit -m "fix: IP 定位模块前端代码提交 (R1)"
```

---

## 验收标准

1. ✅ 前端能看到 IP 定位菜单
2. ✅ 点击菜单能正常访问 IP 定位页面
3. ✅ 页面能正常加载数据
4. ✅ 测试用例全部通过

---

## 风险与回滚

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 前端代码不完整 | 中 | 中 | 仔细检查路由、菜单、组件 |
| API 接口不匹配 | 低 | 中 | 检查前后端字段一致性 |

**回滚方案**: `git reset --hard HEAD~1`

---

## 执行记录

_(执行过程中填写)_

- [ ] 测试用例已创建
- [ ] 测试运行 (红)
- [ ] 代码已修复
- [ ] 测试运行 (绿)
- [ ] Git 已提交
