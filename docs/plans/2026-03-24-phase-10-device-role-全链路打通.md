# Phase-10 设备角色全链路打通 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `device_role` 从数据库与后端模型稳定贯通到设备管理前端展示与筛选能力。

**Architecture:** 采用“模型层 → Schema层 → API层 → 前端展示层 → 回归测试”的顺序推进，先保证后端数据可读写，再开放前端可见能力。全程以最小增量变更为原则，避免引入跨模块重构。通过增量测试确保每一步可回归。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Vue3, Pinia, Element Plus, Pytest

---

### Task 1: 恢复后端模型字段映射

**Files:**
- Modify: `app/models/models.py`
- Test: `tests/unit/test_devices.py`

**Step 1: Write the failing test**

```python
def test_device_model_contains_device_role():
    from app.models.models import Device
    assert hasattr(Device, "device_role")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_devices.py::test_device_model_contains_device_role -v`  
Expected: FAIL with missing `device_role`

**Step 3: Write minimal implementation**

```python
device_role = Column(String(20), nullable=True, index=True)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_devices.py::test_device_model_contains_device_role -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add app/models/models.py tests/unit/test_devices.py
git commit -m "feat: restore device_role in device model"
```

### Task 2: 扩展Schema并保持接口契约一致

**Files:**
- Modify: `app/schemas/schemas.py`
- Modify: `app/api/endpoints/devices.py`
- Test: `tests/unit/test_devices_all_api.py`

**Step 1: Write the failing test**

```python
def test_devices_all_response_contains_device_role(client):
    response = client.get("/api/v1/devices/all")
    assert "device_role" in response.json()["devices"][0]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_devices_all_api.py::test_devices_all_response_contains_device_role -v`  
Expected: FAIL with key not found

**Step 3: Write minimal implementation**

```python
class DeviceBase(BaseModel):
    device_role: Optional[str] = Field(None, description="设备角色")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_devices_all_api.py::test_devices_all_response_contains_device_role -v`  
Expected: PASS

**Step 5: Commit**

```bash
git add app/schemas/schemas.py app/api/endpoints/devices.py tests/unit/test_devices_all_api.py
git commit -m "feat: expose device_role in device schemas and api response"
```

### Task 3: 打通前端设备管理展示与筛选

**Files:**
- Modify: `frontend/src/views/DeviceManagement.vue`
- Modify: `frontend/src/stores/deviceStore.js`
- Test: `frontend` related component tests

**Step 1: Write the failing test**

```javascript
it('shows device role column', () => {
  expect(wrapper.text()).toContain('设备角色')
})
```

**Step 2: Run test to verify it fails**

Run: `npm run test -- DeviceManagement`  
Expected: FAIL without role column

**Step 3: Write minimal implementation**

```vue
<el-table-column prop="device_role" label="设备角色" min-width="120" />
```

**Step 4: Run test to verify it passes**

Run: `npm run test -- DeviceManagement`  
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/views/DeviceManagement.vue frontend/src/stores/deviceStore.js
git commit -m "feat: display and filter device_role in device management"
```

### Task 4: 回归验证与文档同步

**Files:**
- Modify: `docs/功能需求/ip-localtion-phase1-核心交换机下联IP优化/PROGRESS.md`
- Modify: `docs/变更记录/diff-change.md`
- Modify: `docs/decision-log.md`

**Step 1: Write the failing test**

```text
定义验证清单：后端接口字段、前端展示、筛选一致性、回归测试通过、量化退出条件满足
```

**Step 2: Run test to verify it fails**

Run: 基于验证清单执行检查  
Expected: 在实现前至少一项不满足

**Step 3: Write minimal implementation**

```text
更新进度文档、变更记录、决策记录，记录Phase-10执行结果与证据
```

**Step 4: Run test to verify it passes**

Run: 复核清单 + 运行相关测试  
Expected: 全部通过

**Step 5: Commit**

```bash
git add docs/功能需求/ip-localtion-phase1-核心交换机下联IP优化/PROGRESS.md docs/变更记录/diff-change.md docs/decision-log.md
git commit -m "docs: update phase-10 progress and governance records"
```

---

## 执行说明

- 本文档与 `Phase-10-设备角色全链路打通.md` 保持一一对应，作为执行清单。
- 角色枚举统一使用：`core / distribution / access`，禁止使用 `core_switch / access_switch`。
- 审核顺序固定为：阶段1规格符合性通过 → 阶段2代码质量通过 → 执行代码实施。
