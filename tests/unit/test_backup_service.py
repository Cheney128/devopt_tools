
"""
测试 BackupService 模块
测试用例：
- TC-BS-001: collect_config - 设备不存在
- TC-BS-002: collect_config - 配置采集失败
- TC-BS-003: collect_config - 配置无变化
- TC-BS-004: collect_config - 配置有变化
- TC-BS-005: collect_config - Git 操作失败
- TC-BS-006: execute_scheduled_backup - 成功
- TC-BS-007: execute_scheduled_backup - 失败
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.backup_service import BackupService
from app.models.models import Device, Configuration, GitConfig, BackupSchedule, BackupExecutionLog


@pytest.fixture
def db_session():
    """创建 mock 数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def backup_service():
    """创建 BackupService 实例"""
    return BackupService()


class TestBackupServiceCollectConfig:
    """测试 BackupService.collect_config 方法"""

    def test_collect_config_device_not_found(self, db_session, backup_service):
        """TC-BS-001: collect_config - 设备不存在"""
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = pytest.run_coro(backup_service.collect_config(999, db_session))
        
        assert result["success"] is False
        assert result["message"] == "Device not found"

    def test_collect_config_failed_to_get_config(self, db_session, backup_service):
        """TC-BS-002: collect_config - 配置采集失败"""
        mock_device = MagicMock(spec=Device)
        mock_device.id = 1
        mock_device.hostname = "test-device"
        db_session.query.return_value.filter.return_value.first.return_value = mock_device
        
        backup_service.netmiko_service.collect_running_config = MagicMock(return_value=None)
        
        result = pytest.run_coro(backup_service.collect_config(1, db_session))
        
        assert result["success"] is False
        assert "Failed to get config" in result["message"]

    def test_collect_config_unchanged(self, db_session, backup_service):
        """TC-BS-003: collect_config - 配置无变化"""
        mock_device = MagicMock(spec=Device)
        mock_device.id = 1
        mock_device.hostname = "test-device"
        db_session.query.return_value.filter.return_value.first.side_effect = [mock_device, None]
        
        mock_config = MagicMock(spec=Configuration)
        mock_config.id = 1
        mock_config.config_content = "test-config"
        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_config
        
        backup_service.netmiko_service.collect_running_config = MagicMock(return_value="test-config")
        
        result = pytest.run_coro(backup_service.collect_config(1, db_session))
        
        assert result["success"] is True
        assert result["config_changed"] is False
        assert result["config_id"] == mock_config.id

    def test_collect_config_changed(self, db_session, backup_service):
        """TC-BS-004: collect_config - 配置有变化"""
        mock_device = MagicMock(spec=Device)
        mock_device.id = 1
        mock_device.hostname = "test-device"
        db_session.query.return_value.filter.return_value.first.side_effect = [mock_device, None]
        
        mock_config = MagicMock(spec=Configuration)
        mock_config.id = 1
        mock_config.config_content = "old-config"
        mock_config.version = "1.0"
        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_config
        
        backup_service.netmiko_service.collect_running_config = MagicMock(return_value="new-config")
        
        result = pytest.run_coro(backup_service.collect_config(1, db_session))
        
        assert result["success"] is True
        assert result["config_changed"] is True
        assert result["version"] == "1.1"


class TestBackupServiceExecuteScheduledBackup:
    """测试 BackupService.execute_scheduled_backup 方法"""

    def test_execute_scheduled_backup_success(self, db_session, backup_service):
        """TC-BS-006: execute_scheduled_backup - 成功"""
        backup_service.collect_config = MagicMock(return_value={
            "success": True,
            "message": "Success",
            "config_id": 1,
            "config_changed": True
        })
        
        mock_schedule = MagicMock(spec=BackupSchedule)
        mock_schedule.id = 1
        db_session.query.return_value.filter.return_value.first.return_value = mock_schedule
        
        result = pytest.run_coro(backup_service.execute_scheduled_backup(1, db_session, "test-task"))
        
        assert result["success"] is True
        db_session.add.assert_called()
        db_session.commit.assert_called()

    def test_execute_scheduled_backup_failed(self, db_session, backup_service):
        """TC-BS-007: execute_scheduled_backup - 失败"""
        backup_service.collect_config = MagicMock(side_effect=Exception("Test error"))
        
        result = pytest.run_coro(backup_service.execute_scheduled_backup(1, db_session, "test-task"))
        
        assert result["success"] is False
        assert "Test error" in result["message"]
        db_session.add.assert_called()
        db_session.commit.assert_called()

