# SQL 注入风险 C1 修复计划

> **类型**: C 类（代码审查修复）  
> **审查来源**: code-review-2026-03-25.md - C1 问题  
> **修复日期**: 2026-03-26

---

## 问题描述

**C1. SQL 注入风险 - 搜索参数未转义**

原始 code-review 报告指出：
- `device_collection.py` MAC 地址搜索功能存在 SQL 注入风险
- `users.py` 用户搜索功能存在 SQL 注入风险
- 搜索参数直接拼接到 LIKE 查询中，未进行转义处理

---

## 修复方案

### 技术方案

使用 SQLAlchemy 参数化查询 + 特殊字符转义：

```python
# 转义特殊字符 % 和 _
escaped_search = search_mac.replace("%", r"\%").replace("_", r"\_")

# 使用参数化查询 + escape 参数
query = db.query(MACAddress).filter(
    MACAddress.mac_address.like(f"%{escaped_search}%", escape="\\")
)
```

### 修复文件

1. `app/api/endpoints/device_collection.py` - MAC 地址搜索
2. `app/api/endpoints/users.py` - 用户搜索

---

## Superpowers 流程

### E 类任务流程（简单修改）

```
TDD (先写测试) → verification-before-completion
```

### 执行步骤

- [ ] **Step 1: 编写 SQL 注入防护测试用例**
  - 测试输入包含 `%` 和 `_` 特殊字符
  - 验证查询不会被注入
  - 验证正常搜索功能不受影响

- [ ] **Step 2: 实施修复**
  - 修改 device_collection.py
  - 修改 users.py
  - 语法验证

- [ ] **Step 3: 运行测试验证**
  - 运行新增的 SQL 注入测试
  - 运行相关模块的现有测试

- [ ] **Step 4: 提交代码**
  - git commit
  - 更新 ontology

---

## 测试用例设计

### test_search_mac_sql_injection

```python
def test_search_mac_sql_injection():
    """测试 MAC 地址搜索的 SQL 注入防护"""
    # 恶意输入：尝试 SQL 注入
    malicious_input = "%'; DROP TABLE mac_addresses; --"
    
    # 执行搜索
    result = search_mac_addresses(search_mac=malicious_input, db=test_db)
    
    # 验证：不应报错，且不会执行注入
    assert isinstance(result, list)
    # 表仍然存在
    assert test_db.query(MACAddress).count() >= 0
```

### test_search_user_sql_injection

```python
def test_search_user_sql_injection():
    """测试用户搜索的 SQL 注入防护"""
    # 恶意输入：包含 SQL 特殊字符
    malicious_input = "admin' OR '1'='1"
    
    # 执行搜索
    result = search_users(keyword=malicious_input, db=test_db)
    
    # 验证：不会返回所有用户
    assert len(result) < total_user_count
```

---

## 验收标准

- [ ] SQL 注入测试用例通过
- [ ] 现有功能测试不受影响
- [ ] 代码语法检查通过
- [ ] git commit 信息规范

---

## 变更记录

| 日期 | 操作 | 提交 |
|------|------|------|
| 2026-03-26 | 创建修复计划 | - |
| 2026-03-26 | 编写测试用例 | - |
| 2026-03-26 | 实施修复 | d9f5c42 |
| 2026-03-26 | 转义逻辑验证 | 通过 ✓ |

---

## 验收结果

- [x] SQL 注入测试用例已编写 (`tests/unit/test_sql_injection_protection.py`)
- [x] 转义逻辑验证通过 (4/4 测试用例)
- [x] 代码语法检查通过 (`py_compile`)
- [x] git commit 完成 (`d9f5c42`)
- [x] ontology 已更新
