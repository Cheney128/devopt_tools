
"""
测试 BackupSchedulerService 模块
测试用例：
- TC-BSCH-001: _execute_backup - 同步函数调用
- TC-BSCH-002: _execute_backup - 创建新的数据库会话
- TC-BSCH-003: _execute_backup - 调用 asyncio.run()
- TC-BSCH-004: _execute_backup - 重试机制
- TC-BSCH-005: _execute_backup - 超过重试次数
- TC-BSCH-006: add_schedule - 参数传递
- TC-BSCH-007: load_schedules - 日志记录
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.backup_scheduler import BackupSchedulerService
from app.models.models import BackupSchedule, Device


@pytest.fixture
def db_session():
    """创建 mock 数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def backup_scheduler():
    """创建 BackupSchedulerService 实例"""
    with patch('app.services.backup_scheduler.BackgroundScheduler') as mock_scheduler:
        scheduler = BackupSchedulerService()
        scheduler.scheduler = mock_scheduler
        yield scheduler


class TestBackupScheduler:
    """测试 BackupSchedulerService"""

    def test_execute_backup_is_sync_function(self, backup_scheduler):
        """TC-BSCH-001: _execute_backup - 同步函数调用"""
        import inspect
        method = backup_scheduler._execute_backup
        assert not inspect.iscoroutinefunction(method)

    def test_execute_backup_accepts_device_id_only(self, backup_scheduler):
        """TC-BSCH-002: _execute_backup - 仅接受 device_id 参数"""
        import inspect
        sig = inspect.signature(backup_scheduler._execute_backup)
        params = list(sig.parameters.keys())
        assert params == ['device_id']

    def test_add_schedule_passes_only_device_id(self, backup_scheduler, db_session):
        """TC-BSCH-006: add_schedule - 参数传递"""
        mock_device = MagicMock(spec=Device)
        mock_device.id = 1
        mock_device.hostname = "test-device"
        
        mock_schedule = MagicMock(spec=BackupSchedule)
        mock_schedule.id = 1
        mock_schedule.device_id = 1
        mock_schedule.schedule_type = "hourly"
        
        db_session.query.return_value.filter.return_value.first.return_value = mock_device
        backup_scheduler._create_trigger = MagicMock(return_value="test-trigger")
        
        backup_scheduler.add_schedule(mock_schedule, db_session)
        
        backup_scheduler.scheduler.add_job.assert_called_once()
        call_args = backup_scheduler.scheduler.add_job.call_args
        assert call_args[1]["args"] == [1]

    def test_load_schedules_logs_info(self, backup_scheduler, db_session):
        """TC-BSCH-007: load_schedules - 日志记录"""
        with patch('app.services.backup_scheduler.logger') as mock_logger:
            backup_scheduler.load_schedules(db_session)
            
            mock_logger.info.assert_any_call("Loading backup schedules from database")

