# 自动数据库迁移机制 Implementation Plan

&gt; **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自动数据库迁移机制，确保数据库 schema 变更能够自动执行，避免因字段缺失导致应用报错。

**Architecture:** 在 FastAPI 应用启动时自动检测并执行数据库迁移，创建 migration_history 表记录迁移历史，迁移失败不阻止应用启动。

**Tech Stack:** Python 3.9+, FastAPI, SQLAlchemy, MySQL

---

## 文件结构

| 文件 | 操作 | 描述 |
|------|------|------|
| `app/models/models.py` | 修改 | 添加 MigrationHistory 模型 |
| `app/services/migration_manager.py` | 新建 | 迁移管理器实现 |
| `app/main.py` | 修改 | 在 startup 事件中集成迁移检测 |
| `tests/unit/test_migration_manager.py` | 新建 | 迁移管理器单元测试 |

---

## Task 1: 添加 MigrationHistory 模型

**Files:**
- Modify: `app/models/models.py`
- Test: `tests/unit/test_migration_manager.py`

### Step 1.1: 在 models.py 中添加 MigrationHistory 模型

在 `app/models/models.py` 文件末尾（IPLocationSetting 模型之后）添加：

```python
class MigrationHistory(Base):
    """
    数据库迁移历史表
    """
    __tablename__ = "migration_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    migration_name = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # success, failed, skipped
    message = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        Index("idx_migration_name", "migration_name"),
        Index("idx_migration_status", "status"),
    )
```

### Step 1.2: 验证模型添加正确

检查文件语法是否正确：

```bash
python -m py_compile app/models/models.py
```

Expected: 无错误输出

### Step 1.3: 记录变更到 diff-change.md

按要求格式记录变更。

### Step 1.4: Commit

```bash
git add app/models/models.py docs/变更记录/diff-change.md
git commit -m "feat: add MigrationHistory model for database migration tracking"
```

---

## Task 2: 创建 MigrationManager

**Files:**
- Create: `app/services/migration_manager.py`
- Test: `tests/unit/test_migration_manager.py`

### Step 2.1: 创建 migration_manager.py

创建文件 `app/services/migration_manager.py`：

```python
"""
数据库迁移管理器
自动检测和执行数据库迁移
"""
import logging
from typing import List, Tuple, Callable, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus, urlparse, urlunparse
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self, db_url: str):
        self.db_url = self._fix_database_url(db_url)
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @staticmethod
    def _fix_database_url(db_url: str) -&gt; str:
        """修复数据库URL中的密码编码问题"""
        parsed = urlparse(db_url)
        if parsed.password:
            encoded_password = quote_plus(parsed.password)
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        return db_url
    
    def ensure_migration_history_table(self) -&gt; bool:
        """确保 migration_history 表存在，不存在则创建"""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            if "migration_history" in tables:
                logger.debug("migration_history 表已存在")
                return True
            
            with self.engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE migration_history (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        migration_name VARCHAR(100) NOT NULL COMMENT '迁移名称',
                        status VARCHAR(20) NOT NULL COMMENT '状态：success/failed/skipped',
                        message TEXT NULL COMMENT '执行信息',
                        executed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
                        INDEX idx_migration_name (migration_name),
                        INDEX idx_migration_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移历史表'
                """))
            logger.info("✓ 创建 migration_history 表成功")
            return True
        except Exception as e:
            logger.error(f"创建 migration_history 表失败: {e}")
            return False
    
    def get_executed_migrations(self) -&gt; List[str]:
        """获取已执行的迁移列表（成功的）"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT DISTINCT migration_name 
                    FROM migration_history 
                    WHERE status = 'success'
                    ORDER BY executed_at DESC
                """))
                return [row[0] for row in result]
        except Exception as e:
            logger.warning(f"获取已执行迁移列表失败: {e}")
            return []
    
    def is_migration_executed(self, migration_name: str) -&gt; bool:
        """检查迁移是否已执行（成功的）"""
        executed = self.get_executed_migrations()
        return migration_name in executed
    
    def record_migration(self, migration_name: str, success: bool, message: str = ""):
        """记录迁移执行结果"""
        try:
            status = "success" if success else "failed"
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO migration_history (migration_name, status, message, executed_at)
                    VALUES (:migration_name, :status, :message, :executed_at)
                """), {
                    "migration_name": migration_name,
                    "status": status,
                    "message": message,
                    "executed_at": datetime.now()
                })
            logger.debug(f"记录迁移 {migration_name} 状态: {status}")
        except Exception as e:
            logger.error(f"记录迁移历史失败: {e}")
    
    def execute_migration(self, migration_name: str, migration_func: Callable) -&gt; bool:
        """执行单个迁移"""
        if self.is_migration_executed(migration_name):
            logger.info(f"迁移 {migration_name} 已执行，跳过")
            self.record_migration(migration_name, True, "already executed")
            return True
        
        logger.info(f"开始执行迁移: {migration_name}")
        try:
            migration_func()
            self.record_migration(migration_name, True, "success")
            logger.info(f"✓ 迁移 {migration_name} 执行成功")
            return True
        except Exception as e:
            error_msg = str(e)
            self.record_migration(migration_name, False, error_msg)
            logger.error(f"✗ 迁移 {migration_name} 执行失败: {error_msg}")
            return False
    
    def _migrate_ip_location_core_switch(self):
        """执行 IP 定位核心交换机优化迁移"""
        with self.engine.begin() as conn:
            result = conn.execute(text("SHOW COLUMNS FROM devices LIKE 'device_role'"))
            if not result.fetchone():
                conn.execute(text("""
                    ALTER TABLE devices 
                    ADD COLUMN device_role VARCHAR(20) NULL 
                    COMMENT '设备角色：core（核心）、distribution（汇聚）、access（接入）'
                """))
                logger.info("✓ 添加device_role字段到devices表")
                
                conn.execute(text("""
                    CREATE INDEX idx_devices_device_role ON devices(device_role)
                """))
                logger.info("✓ 创建device_role索引")
            else:
                logger.info("✓ device_role字段已存在，跳过")
            
            result = conn.execute(text("SHOW TABLES LIKE 'ip_location_settings'"))
            if not result.fetchone():
                conn.execute(text("""
                    CREATE TABLE ip_location_settings (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        `key` VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
                        value TEXT NULL COMMENT '配置值',
                        description TEXT NULL COMMENT '配置描述',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        INDEX idx_ip_location_settings_key (`key`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IP定位配置表'
                """))
                logger.info("✓ 创建ip_location_settings表")
            else:
                logger.info("✓ ip_location_settings表已存在，跳过")
            
            initial_configs = [
                ("enable_core_switch_filter", "true", "是否启用核心交换机过滤"),
                ("core_switch_keywords", "core,核心", "核心交换机主机名关键词（逗号分隔）"),
                ("vlan_interface_keywords", "Vlan,Vlanif,VLAN,Interface-Vlan", "VLAN接口关键词（逗号分隔）"),
                ("retain_interface_desc_keywords", "接入,access,用户,user", "保留接口描述关键词（逗号分隔）"),
                ("filter_interface_desc_keywords", "上联,核心,汇聚,uplink", "过滤接口描述关键词（逗号分隔）"),
                ("core_switch_retain_physical_interfaces", "false", "核心交换机是否默认保留物理接口")
            ]
            
            for key, value, description in initial_configs:
                conn.execute(text("""
                    INSERT IGNORE INTO ip_location_settings (`key`, value, description)
                    VALUES (:key, :value, :description)
                """), {"key": key, "value": value, "description": description})
            logger.info("✓ 初始化配置数据完成")
    
    def run_all_migrations(self) -&gt; Tuple[int, int]:
        """运行所有迁移，返回 (成功数, 失败数)"""
        if not self.ensure_migration_history_table():
            logger.warning("无法确保 migration_history 表存在，跳过迁移")
            return 0, 0
        
        success_count = 0
        fail_count = 0
        
        migrations = [
            ("ip_location_core_switch", self._migrate_ip_location_core_switch),
        ]
        
        for migration_name, migration_func in migrations:
            if self.execute_migration(migration_name, migration_func):
                success_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count
```

### Step 2.2: 验证文件语法

```bash
python -m py_compile app/services/migration_manager.py
```

Expected: 无错误输出

### Step 2.3: 记录变更到 diff-change.md

按要求格式记录变更。

### Step 2.4: Commit

```bash
git add app/services/migration_manager.py docs/变更记录/diff-change.md
git commit -m "feat: create MigrationManager for automatic database migrations"
```

---

## Task 3: 在 FastAPI 启动事件中集成迁移检测

**Files:**
- Modify: `app/main.py:80-133`
- Test: 手动测试应用启动

### Step 3.1: 修改 app/main.py

在 `@app.on_event("startup")` 事件中，在初始化主事件循环之后添加迁移检测逻辑：

```python
@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    # 初始化主事件循环引用
    init_main_event_loop()
    
    # 数据库迁移检测和执行
    try:
        logger.info("[Startup] Checking and running database migrations...")
        from app.services.migration_manager import MigrationManager
        from app.config import settings
        migration_manager = MigrationManager(settings.DATABASE_URL)
        success_count, fail_count = migration_manager.run_all_migrations()
        if fail_count == 0:
            logger.info(f"[Startup] Database migrations completed: {success_count} succeeded")
        else:
            logger.warning(f"[Startup] Database migrations completed: {success_count} succeeded, {fail_count} failed")
    except Exception as e:
        logger.error(f"[Startup] Database migration check failed: {e}")
        logger.warning("[Startup] Application will continue, but some features may not work correctly.")
    
    # ... 保留原有代码 ...
```

### Step 3.2: 验证文件语法

```bash
python -m py_compile app/main.py
```

Expected: 无错误输出

### Step 3.3: 记录变更到 diff-change.md

按要求格式记录变更。

### Step 3.4: Commit

```bash
git add app/main.py docs/变更记录/diff-change.md
git commit -m "feat: integrate database migration check in FastAPI startup event"
```

---

## Task 4: 创建单元测试

**Files:**
- Create: `tests/unit/test_migration_manager.py`

### Step 4.1: 创建测试文件

创建 `tests/unit/test_migration_manager.py`：

```python
"""
MigrationManager 单元测试
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine, text
from app.services.migration_manager import MigrationManager


class TestMigrationManager:
    """MigrationManager 测试类"""
    
    def test_fix_database_url_with_password(self):
        """测试修复包含密码的数据库URL"""
        original_url = "mysql+pymysql://user:pass@word@localhost:3306/db"
        fixed_url = MigrationManager._fix_database_url(original_url)
        assert "%40" in fixed_url
        assert "pass@word" not in fixed_url
    
    def test_fix_database_url_without_password(self):
        """测试修复不包含密码的数据库URL"""
        original_url = "mysql+pymysql://user@localhost:3306/db"
        fixed_url = MigrationManager._fix_database_url(original_url)
        assert fixed_url == original_url
    
    def test_ensure_migration_history_table(self):
        """测试确保 migration_history 表存在"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            db_url = f"sqlite:///{db_path}"
            manager = MigrationManager(db_url)
            
            # 第一次调用应该创建表
            result = manager.ensure_migration_history_table()
            assert result is True
            
            # 验证表存在
            inspector = __import__("sqlalchemy").inspect(manager.engine)
            tables = inspector.get_table_names()
            assert "migration_history" in tables
            
            # 第二次调用应该跳过
            result = manager.ensure_migration_history_table()
            assert result is True
        finally:
            os.unlink(db_path)
    
    def test_record_and_check_migration(self):
        """测试记录和检查迁移"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            db_url = f"sqlite:///{db_path}"
            manager = MigrationManager(db_url)
            manager.ensure_migration_history_table()
            
            # 记录一个成功的迁移
            manager.record_migration("test_migration_1", True, "success")
            
            # 检查迁移是否已执行
            assert manager.is_migration_executed("test_migration_1") is True
            assert manager.is_migration_executed("test_migration_2") is False
            
            # 获取已执行的迁移列表
            executed = manager.get_executed_migrations()
            assert "test_migration_1" in executed
            
            # 记录一个失败的迁移
            manager.record_migration("test_migration_2", False, "failed")
            
            # 失败的迁移不应该出现在已执行列表中
            assert manager.is_migration_executed("test_migration_2") is False
        finally:
            os.unlink(db_path)
    
    def test_execute_migration(self):
        """测试执行迁移"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            db_url = f"sqlite:///{db_path}"
            manager = MigrationManager(db_url)
            manager.ensure_migration_history_table()
            
            # 创建一个测试表的迁移函数
            test_table_created = False
            
            def test_migration_func():
                nonlocal test_table_created
                with manager.engine.begin() as conn:
                    conn.execute(text("CREATE TABLE test_table (id INT PRIMARY KEY)"))
                test_table_created = True
            
            # 执行迁移
            result = manager.execute_migration("test_migration", test_migration_func)
            assert result is True
            assert test_table_created is True
            
            # 再次执行应该跳过
            test_table_created = False
            result = manager.execute_migration("test_migration", test_migration_func)
            assert result is True
            assert test_table_created is False
        finally:
            os.unlink(db_path)
```

### Step 4.2: 运行测试

```bash
python -m pytest tests/unit/test_migration_manager.py -v
```

Expected: 所有测试通过

### Step 4.3: 记录变更到 diff-change.md

按要求格式记录变更。

### Step 4.4: Commit

```bash
git add tests/unit/test_migration_manager.py docs/变更记录/diff-change.md
git commit -m "test: add unit tests for MigrationManager"
```

---

## Task 5: 运行所有测试

**Files:**
- Test: 所有测试文件

### Step 5.1: 运行所有单元测试

```bash
python -m pytest tests/unit/ -v
```

Expected: 所有测试通过

### Step 5.2: 运行集成测试（如果有）

```bash
python -m pytest tests/integration/ -v
```

Expected: 所有测试通过

---

## Task 6: 手动测试验证

**Files:**
- Test: 手动启动应用验证

### Step 6.1: 启动后端应用

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6.2: 检查启动日志

查看日志中是否有迁移相关的信息：
- "Checking and running database migrations..."
- "Database migrations completed: X succeeded"

### Step 6.3: 验证 API 端点正常

访问以下端点验证功能正常：
- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/api/v1/devices` - 设备列表
- `http://localhost:8000/api/v1/ip-location` - IP定位

---

## 验证清单

- [ ] MigrationHistory 模型已添加到 models.py
- [ ] MigrationManager 已创建并可以正常工作
- [ ] 应用启动时自动执行迁移
- [ ] 迁移历史正确记录到 migration_history 表
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动测试验证通过
- [ ] 变更记录已更新到 diff-change.md

---

## 相关文档

- [Phase-8-自动数据库迁移机制.md](./Phase-8-自动数据库迁移机制.md)
- [ISSUE-数据库device_role字段缺失导致多个模块报错.md](./ISSUE-数据库device_role字段缺失导致多个模块报错.md)
