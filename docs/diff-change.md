# 代码变更记录

## 变更记录格式

每次代码变更请按照以下格式记录：

### YYYY-MM-DD HH:MM:SS

**变更文件**：文件路径
**变更位置**：行号范围
**变更内容**：具体变更的代码内容
**变更原因**：变更的目的和原因

---

## 变更记录

### 2026-02-09 12:00:00

**变更文件**：app/api/endpoints/configurations.py
**变更位置**：487-540
**变更内容**：
- 修改 `@router.get("/backup-schedules")` 的 response_model 从 `List[BackupScheduleSchema]` 改为 `Dict[str, Any]`
- 添加分页参数：`page: int = Query(1, ge=1, description="页码")` 和 `page_size: int = Query(10, ge=1, le=100, description="每页数量")`
- 添加总数查询：`total = query.count()`
- 添加分页查询逻辑：使用 `offset((page - 1) * page_size).limit(page_size)` 实现真正的分页
- 修改返回值格式：从直接返回数组 `return schedules` 改为返回对象 `return {"schedules": schedules, "total": total}`

**变更原因**：修复备份计划API返回格式与前端期望不匹配的问题。后端原直接返回数组，但前端期望 `{schedules: [], total: N}` 格式，导致数据无法正确显示并触发 setAttribute 错误。同时添加分页支持，提高大数据量查询性能。
