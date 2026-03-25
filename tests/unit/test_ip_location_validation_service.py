# -*- coding: utf-8 -*-
"""
IP 定位验证服务单元测试

测试 IPLocationValidationService 的验证和回滚功能。
"""
from unittest.mock import Mock

from app.services.ip_location_validation_service import IPLocationValidationService


class TestIPLocationValidationService:
    """IP 定位验证服务测试类"""

    def test_validate_and_activate_batch_blocked_when_exceeds_threshold(self):
        """测试差异比例超过阈值时阻止激活"""
        service = IPLocationValidationService(Mock())
        service.snapshot_service = Mock()
        service.snapshot_service.get_active_batch_id.return_value = "active_old"
        
        # 差异比例 30% > 阈值 20%，应该拒绝激活
        result = service.validate_and_activate_batch(
            candidate_batch_id="batch_new",
            sample_total=100,
            diff_total=30,
            threshold=0.2
        )
        
        assert result["passed"] is False
        assert result["active_batch_id"] == "active_old"
        service.snapshot_service.activate_batch.assert_not_called()

    def test_validate_and_activate_batch_success(self):
        """测试验证通过并成功激活批次"""
        service = IPLocationValidationService(Mock())
        service.snapshot_service = Mock()
        
        # 差异比例 5% < 阈值 20%，应该激活
        result = service.validate_and_activate_batch(
            candidate_batch_id="batch_new",
            sample_total=100,
            diff_total=5,
            threshold=0.2
        )
        
        assert result["passed"] is True
        assert result["active_batch_id"] == "batch_new"
        service.snapshot_service.activate_batch.assert_called_once_with("batch_new")

    def test_validate_invalid_sample_total(self):
        """测试 sample_total 为 0 或负数时的处理"""
        service = IPLocationValidationService(Mock())
        service.snapshot_service = Mock()
        service.snapshot_service.get_active_batch_id.return_value = "active_old"
        
        result = service.validate_and_activate_batch(
            candidate_batch_id="batch_new",
            sample_total=0,
            diff_total=0,
            threshold=0.1
        )
        
        assert result["passed"] is False
        assert result["difference_ratio"] == 1.0
        assert "positive" in result["message"]

    def test_rollback_success(self):
        """测试成功回滚到历史批次"""
        service = IPLocationValidationService(Mock())
        service.snapshot_service = Mock()
        service.snapshot_service.rollback_to_batch.return_value = True
        service.snapshot_service.get_active_batch_id.return_value = "batch_old"
        
        result = service.rollback("batch_old")
        
        assert result["success"] is True
        assert result["active_batch_id"] == "batch_old"
        assert "message" not in result

    def test_rollback_failure(self):
        """测试回滚失败时的处理"""
        service = IPLocationValidationService(Mock())
        service.snapshot_service = Mock()
        service.snapshot_service.rollback_to_batch.return_value = False
        service.snapshot_service.get_active_batch_id.return_value = "batch_current"
        
        result = service.rollback("batch_not_found")
        
        assert result["success"] is False
        assert result["active_batch_id"] == "batch_current"
        assert "message" in result
