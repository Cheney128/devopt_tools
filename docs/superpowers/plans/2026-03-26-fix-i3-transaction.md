# I3 问题修复：批次激活事务保护

> **类型**: E 类（简单修改/代码质量优化）  
> **审查来源**: code-review-2026-03-25.md - I3 问题  
> **修复日期**: 2026-03-26

---

## 问题描述

**I3. 批次激活缺少事务保护**

原始 code-review 报告指出：
- `activate_batch` 方法执行两次 UPDATE 操作但只有一次 commit
- 如果第一次成功第二次失败，会导致数据不一致（没有批次是 active 状态）

---

## 修复方案

使用 SQLAlchemy 的 `with db.begin()` 上下文管理器：

```python
def activate_batch(self, batch_id: str) -> None:
    """激活候选批次，自动回滚旧批次"""
    with self.db.begin():  # 异常自动回滚，成功自动提交
        self.db.query(IPLocationCurrent).filter(...).update(...)
        self.db.query(IPLocationCurrent).filter(...).update(...)
```

**优势**：
- 代码更简洁（少 5 行 try/except）
- 异常处理更可靠（不会忘记 rollback）
- Pythonic 风格，符合现代 SQLAlchemy 最佳实践

---

## Superpowers 流程

### E 类任务流程

```
verification-before-completion
```

### 执行步骤

- [ ] **Step 1: 创建修复计划文档**
  - 保存到 `docs/superpowers/plans/2026-03-26-fix-i3-transaction.md`

- [ ] **Step 2: 实施修复**
  - 修改 `app/services/ip_location_snapshot_service.py`
  - 使用 `with self.db.begin()` 包装两次 UPDATE
  - 添加/完善方法文档字符串

- [ ] **Step 3: 编写测试**
  - 修改 `tests/unit/test_ip_location_snapshot_service.py`
  - 新增 `test_activate_batch_rollback_on_exception` 测试用例

- [ ] **Step 4: 验证**
  - 语法检查 `py_compile`

- [ ] **Step 5: 提交代码**
  - git add + commit

- [ ] **Step 6: 更新 ontology**

---

## 验收标准

- [ ] 代码使用 `with db.begin()` 上下文管理器
- [ ] 方法包含文档字符串
- [ ] 新增事务回滚测试用例（1 个）
- [ ] 语法检查通过
- [ ] git commit 信息规范

---

## 变更记录

| 日期 | 操作 | 提交 |
|------|------|------|
| 2026-03-26 | 创建修复计划 | - |
