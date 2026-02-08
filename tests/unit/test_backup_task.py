"""
备份任务模型单元测试
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models import Base
from app.models.backup_task import BackupTask, BackupTaskStatus, BackupPriority


# 创建内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module():
    """创建测试数据库表"""
    Base.metadata.create_all(bind=engine)


def teardown_module():
    """清理测试数据库"""
    Base.metadata.drop_all(bind=engine)


def get_test_db():
    """获取测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestBackupTaskStatus:
    """测试备份任务状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert BackupTaskStatus.PENDING.value == "pending"
        assert BackupTaskStatus.RUNNING.value == "running"
        assert BackupTaskStatus.COMPLETED.value == "completed"
        assert BackupTaskStatus.FAILED.value == "failed"
        assert BackupTaskStatus.CANCELLED.value == "cancelled"

    def test_status_count(self):
        """测试状态枚举数量"""
        assert len(BackupTaskStatus) == 5


class TestBackupPriority:
    """测试备份任务优先级枚举"""

    def test_priority_values(self):
        """测试优先级枚举值"""
        assert BackupPriority.LOW.value == "low"
        assert BackupPriority.NORMAL.value == "normal"
        assert BackupPriority.HIGH.value == "high"

    def test_priority_count(self):
        """测试优先级枚举数量"""
        assert len(BackupPriority) == 3


class TestBackupTaskModel:
    """测试备份任务模型"""

    def test_create_backup_task(self):
        """测试创建备份任务"""
        db = next(get_test_db())
        try:
            task = BackupTask(
                task_id="test-task-001",
                status=BackupTaskStatus.PENDING,
                priority=BackupPriority.NORMAL,
                total=10,
                completed=0,
                success_count=0,
                failed_count=0,
                filters={"vendor": "Huawei"},
                max_concurrent=3,
                timeout=300,
                retry_count=2,
                notify_on_complete=0,
                created_by="admin"
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            assert task.id is not None
            assert task.task_id == "test-task-001"
            assert task.status == BackupTaskStatus.PENDING
            assert task.priority == BackupPriority.NORMAL
            assert task.total == 10
            assert task.completed == 0
            assert task.filters == {"vendor": "Huawei"}
        finally:
            db.rollback()
            db.close()

    def test_backup_task_default_values(self):
        """测试备份任务默认值"""
        db = next(get_test_db())
        try:
            task = BackupTask(task_id="test-task-002")
            db.add(task)
            db.commit()
            db.refresh(task)

            assert task.status == BackupTaskStatus.PENDING
            assert task.priority == BackupPriority.NORMAL
            assert task.total == 0
            assert task.completed == 0
            assert task.filters == {}
            assert task.max_concurrent == 3
            assert task.timeout == 300
            assert task.retry_count == 2
        finally:
            db.rollback()
            db.close()

    def test_backup_task_unique_task_id(self):
        """测试备份任务ID唯一性约束"""
        db = next(get_test_db())
        try:
            task1 = BackupTask(
                task_id="unique-task-001",
                status=BackupTaskStatus.PENDING
            )
            db.add(task1)
            db.commit()

            task2 = BackupTask(
                task_id="unique-task-001",
                status=BackupTaskStatus.PENDING
            )
            db.add(task2)

            with pytest.raises(IntegrityError):
                db.commit()
        except IntegrityError:
            db.rollback()
        finally:
            db.close()

    def test_backup_task_timestamps(self):
        """测试备份任务时间戳"""
        db = next(get_test_db())
        try:
            task = BackupTask(task_id="timestamp-test-001")
            db.add(task)
            db.commit()
            db.refresh(task)

            assert task.created_at is not None
            assert task.started_at is None
            assert task.completed_at is None

            task.status = BackupTaskStatus.RUNNING
            task.started_at = datetime.now()
            db.commit()
            db.refresh(task)

            assert task.status == BackupTaskStatus.RUNNING
            assert task.started_at is not None
        finally:
            db.rollback()
            db.close()

    def test_backup_task_progress_tracking(self):
        """测试备份任务进度跟踪"""
        db = next(get_test_db())
        try:
            task = BackupTask(task_id="progress-test-001", total=5)
            db.add(task)
            db.commit()
            db.refresh(task)

            task.completed = 3
            task.success_count = 2
            task.failed_count = 1
            db.commit()
            db.refresh(task)

            assert task.completed == 3
            assert task.success_count == 2
            assert task.failed_count == 1
        finally:
            db.rollback()
            db.close()

    def test_backup_task_auto_generate_task_id(self):
        """测试自动生成任务ID"""
        db = next(get_test_db())
        try:
            task = BackupTask()
            db.add(task)
            db.commit()
            db.refresh(task)

            assert task.task_id is not None
            assert len(task.task_id) == 36  # UUID length
        finally:
            db.rollback()
            db.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
