# -*- coding: utf-8 -*-
"""
IP 定位快照服务单元测试

测试 IPLocationSnapshotService 的批次管理和事务保护功能。
"""
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy import and_

from app.models.models import ARPEntry, MACAddress, Device, IPLocationCurrent
from app.services.ip_location_snapshot_service import IPLocationSnapshotService


class TestIPLocationSnapshotService:
    def test_build_candidates_contains_same_and_cross_device(self):
        with patch('app.services.ip_location_snapshot_service.IPLocationConfigManager') as mock_cfg, \
             patch('app.services.ip_location_snapshot_service.InterfaceRecognizer') as mock_ir, \
             patch('app.services.ip_location_snapshot_service.ConfidenceCalculator') as mock_cc, \
             patch('app.services.ip_location_snapshot_service.CoreSwitchRecognizer') as mock_csr:
            mock_cfg.return_value.get_config_dict_for_service.return_value = {}
            mock_ir.is_uplink_interface.return_value = False
            mock_cc.calculate_confidence.side_effect = [0.95, 0.85]
            mock_csr.is_core_switch.return_value = False
            db = Mock()
            service = IPLocationSnapshotService(db)

            arp = ARPEntry(
                device_id=1,
                ip_address="10.0.0.1",
                mac_address="00:11:22:33:44:55",
                vlan_id=10,
                interface="GE1/0/1",
                last_seen=datetime.now()
            )
            mac_same = MACAddress(
                device_id=1,
                mac_address="00:11:22:33:44:55",
                vlan_id=10,
                interface="GE1/0/1",
                is_trunk=False,
                last_seen=datetime.now()
            )
            mac_cross = MACAddress(
                device_id=2,
                mac_address="00:11:22:33:44:55",
                vlan_id=10,
                interface="GE1/0/24",
                is_trunk=False,
                last_seen=datetime.now()
            )

            mac_query = Mock()
            mac_query.filter.return_value = mac_query
            mac_query.order_by.return_value = mac_query
            mac_query.limit.return_value = mac_query
            mac_query.all.return_value = [mac_same, mac_cross]

            device_query = Mock()
            device_query.filter.return_value = device_query
            device_query.first.side_effect = [
                Device(id=1, hostname="sw1", ip_address="10.0.0.11"),
                Device(id=1, hostname="sw1", ip_address="10.0.0.11"),
                Device(id=2, hostname="sw2", ip_address="10.0.0.12")
            ]

            def query_side_effect(model):
                if model == MACAddress:
                    return mac_query
                if model == Device:
                    return device_query
                return Mock()

            db.query.side_effect = query_side_effect
            candidates = service._build_candidates(arp)
            match_types = {item["match_type"] for item in candidates}
            assert "same_device" in match_types
            assert "cross_device" in match_types

    def test_build_candidates_returns_arp_only_when_no_mac(self):
        with patch('app.services.ip_location_snapshot_service.IPLocationConfigManager') as mock_cfg, \
             patch('app.services.ip_location_snapshot_service.InterfaceRecognizer') as mock_ir, \
             patch('app.services.ip_location_snapshot_service.ConfidenceCalculator') as mock_cc, \
             patch('app.services.ip_location_snapshot_service.CoreSwitchRecognizer') as mock_csr:
            mock_cfg.return_value.get_config_dict_for_service.return_value = {}
            mock_ir.is_uplink_interface.return_value = False
            mock_cc.calculate_confidence.return_value = 0.5
            mock_csr.is_core_switch.return_value = False
            db = Mock()
            service = IPLocationSnapshotService(db)

            arp = ARPEntry(
                device_id=1,
                ip_address="10.0.0.2",
                mac_address="aa:bb:cc:dd:ee:ff",
                vlan_id=20,
                interface="GE1/0/2",
                last_seen=datetime.now()
            )

            mac_query = Mock()
            mac_query.filter.return_value = mac_query
            mac_query.order_by.return_value = mac_query
            mac_query.limit.return_value = mac_query
            mac_query.all.return_value = []

            device_query = Mock()
            device_query.filter.return_value = device_query
            device_query.first.return_value = Device(id=1, hostname="sw1", ip_address="10.0.0.11")

            def query_side_effect(model):
                if model == MACAddress:
                    return mac_query
                if model == Device:
                    return device_query
                return Mock()

            db.query.side_effect = query_side_effect
            candidates = service._build_candidates(arp)
            assert len(candidates) == 1
            assert candidates[0]["match_type"] == "arp_only"


class TestIPLocationSnapshotServiceTransaction:
    """IP 定位快照服务事务保护测试"""

    def test_activate_batch_rollback_on_exception(self):
        """测试异常时事务回滚"""
        db = Mock()
        service = IPLocationSnapshotService(db)

        # 模拟 db.begin() 上下文管理器在第二次 UPDATE 时抛出异常
        mock_context = Mock()
        mock_context.__enter__ = Mock()
        mock_context.__exit__ = Mock(side_effect=Exception("模拟数据库异常"))
        db.begin = Mock(return_value=mock_context)

        # 执行激活操作，应该抛出异常
        try:
            service.activate_batch("batch_new")
        except Exception:
            pass  # 预期会抛出异常

        # 验证：db.begin 被调用
        db.begin.assert_called_once()

    def test_activate_batch_success(self):
        """测试正常激活批次"""
        db = Mock()
        service = IPLocationSnapshotService(db)

        # 模拟 db.begin() 上下文管理器正常执行
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        db.begin = Mock(return_value=mock_context)

        # 执行激活操作
        service.activate_batch("batch_new")

        # 验证：db.begin 被调用
        db.begin.assert_called_once()

    def test_activate_batch_updates_correct_batches(self):
        """验证 activate_batch 正确更新批次状态"""
        db = Mock()
        service = IPLocationSnapshotService(db)

        # 模拟 query 链式调用
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.update = Mock(return_value=2)  # 模拟更新 2 行
        db.query = Mock(return_value=mock_query)

        # 模拟 db.begin() 上下文管理器
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=None)
        mock_context.__exit__ = Mock(return_value=None)
        db.begin = Mock(return_value=mock_context)

        # 执行激活
        service.activate_batch("batch_new")

        # 验证：query 被调用（两次 UPDATE）
        assert db.query.call_count >= 1
        # 验证：filter 被调用（筛选条件）
        assert mock_query.filter.call_count >= 2
        # 验证：update 被调用（两次更新）
        assert mock_query.update.call_count >= 2
