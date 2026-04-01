---
ontology:
  id: DOC-2026-03-003-PLAN
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
# I2 问题修复：配置缓存改为动态获取

> **类型**: E 类（简单修改/代码质量优化）  
> **审查来源**: code-review-2026-03-25.md - I2 问题  
> **修复日期**: 2026-03-26

---

## 问题描述

**I2. 配置字典缓存可能导致数据不一致**

原始 code-review 报告指出：
- `IPLocationSnapshotService` 在初始化时缓存配置字典
- 运行期间如果配置被修改，服务将使用过期配置
- 可能导致行为不一致

---

## 修复方案

使用 `@property` 动态获取配置：

```python
class IPLocationSnapshotService:
    def __init__(self, db: Session):
        self.config_manager = IPLocationConfigManager(db)
    
    @property
    def config(self) -> Dict[str, Any]:
        """动态获取最新配置"""
        return self.config_manager.get_config_dict_for_service()
```

**优势**：
- 每次访问 `self.config` 都获取最新配置
- 支持运行时配置变更
- 代码简洁，符合 Python 最佳实践

---

## Superpowers 流程

### E 类任务流程

```
verification-before-completion
```

### 执行步骤

- [ ] **Step 1: 创建修复计划文档**
  - 保存到 `docs/superpowers/plans/2026-03-26-fix-i2-config-cache.md`

- [ ] **Step 2: 实施修复**
  - 修改 `app/services/ip_location_snapshot_service.py`
  - 移除 `__init__` 中的 `self.config = ...` 赋值
  - 添加 `@property` 装饰器的 `config` 方法

- [ ] **Step 3: 验证**
  - 语法检查 `py_compile`

- [ ] **Step 4: 提交代码**
  - git add + commit

- [ ] **Step 5: 更新 ontology**

---

## 验收标准

- [ ] 使用 `@property` 动态获取配置
- [ ] 语法检查通过
- [ ] git commit 信息规范
- [ ] ontology 已更新

---

## 变更记录

| 日期 | 操作 | 提交 |
|------|------|------|
| 2026-03-26 | 创建修复计划 | - |
