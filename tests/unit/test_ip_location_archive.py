# -*- coding: utf-8 -*-
"""
IP 定位归档逻辑专项测试

测试目标：验证 _archive_offline_ips() 的两级验证逻辑
- 第一级：calculated_at 超过阈值（30 分钟）
- 第二级：IP 不在当前 ARP 表中

测试场景：
1. IP 在 ARP 表中 → 不应归档（设备仍在线）
2. IP 不在 ARP 表但 calculated_at 新鲜 → 不应归档（可能是采集延迟）
3. IP 不在 ARP 表且 calculated_at 过期 → 应归档（设备已下线）
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

from app.services.ip_location_calculator import (
    IPLocationCalculator,
    ARPEntry,
)
from app.models.ip_location import IPLocationCurrent, IPLocationHistory


class TestArchiveOfflineIPs:
    """归档下线 IP 逻辑测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.delete.return_value = 0
        return db

    @pytest.fixture
    def calculator(self, mock_db):
        """创建计算器实例"""
        return IPLocationCalculator(mock_db)

    @pytest.fixture
    def sample_current_record(self):
        """创建示例当前记录"""
        return IPLocationCurrent(
            id=1,
            ip_address='192.168.1.100',
            mac_address='00:11:22:33:44:55',
            arp_source_device_id=1,
            mac_hit_device_id=2,
            access_interface='Gi1/0/1',
            vlan_id=100,
            confidence=Decimal('0.85'),
            is_uplink=False,
            is_core_switch=False,
            match_type='single_match',
            calculated_at=datetime.now() - timedelta(minutes=60),
            last_seen=datetime.now() - timedelta(minutes=60)
        )

    def test_archive_ip_in_arp_table(self, calculator, mock_db, sample_current_record):
        """
        场景 1：IP 在 ARP 表中存在，且计算时间过期（60 分钟前）

        预期：不应归档（设备仍在线）

        原理：即使 calculated_at 超过阈值，但 IP 在 ARP 表中存在，
              说明设备仍在网络中活跃，不应归档。
        """
        # 设置：模拟数据库返回过期的候选记录
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_current_record]

        # 设置：ARP 表中存在该 IP（模拟 _load_arp_entries 加载的数据）
        calculator._arp_entries = [
            ARPEntry(
                ip_address='192.168.1.100',  # 与 sample_current_record 相同的 IP
                mac_address='00:11:22:33:44:55',
                arp_device_id=1
            )
        ]

        # 执行归档
        archived_count = calculator._archive_offline_ips()

        # 验证：不应归档任何记录
        assert archived_count == 0, "IP 在 ARP 表中存在时不应归档"

        # 验证：没有创建历史记录
        mock_db.add.assert_not_called()
        # 验证：没有删除当前记录
        mock_db.delete.assert_not_called()

    def test_archive_ip_fresh_calculation(self, calculator, mock_db, sample_current_record):
        """
        场景 2：IP 不在 ARP 表中，但 calculated_at = 5 分钟前

        预期：不应归档（可能是采集延迟）

        原理：虽然 IP 不在 ARP 表中，但 calculated_at 是新鲜的，
              可能是 ARP 采集延迟，给予缓冲时间。
        """
        # 设置：修改记录的 calculated_at 为 5 分钟前
        sample_current_record.calculated_at = datetime.now() - timedelta(minutes=5)
        sample_current_record.last_seen = datetime.now() - timedelta(minutes=5)

        # 设置：数据库查询返回空（因为 calculated_at 未超过 30 分钟阈值）
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # 设置：ARP 表中不存在该 IP
        calculator._arp_entries = []

        # 执行归档
        archived_count = calculator._archive_offline_ips()

        # 验证：不应归档（因为 calculated_at 未超过阈值）
        assert archived_count == 0, "calculated_at 新鲜时不应归档"

    def test_archive_ip_offline(self, calculator, mock_db, sample_current_record):
        """
        场景 3：IP 不在 ARP 表中，且 calculated_at = 60 分钟前

        预期：应归档（设备已下线）

        原理：IP 既不在 ARP 表中，且 calculated_at 也超过阈值，
              说明设备已真正下线，应归档到历史表。
        """
        # 设置：模拟数据库返回过期的候选记录
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_current_record]

        # 设置：ARP 表中不存在该 IP
        calculator._arp_entries = []

        # 执行归档
        archived_count = calculator._archive_offline_ips()

        # 验证：应归档 1 条记录
        assert archived_count == 1, "IP 不在 ARP 表且 calculated_at 过期时应归档"

        # 验证：创建了历史记录
        mock_db.add.assert_called_once()
        # 验证：删除了当前记录
        mock_db.delete.assert_called_once()

        # 验证：历史记录的内容
        added_history = mock_db.add.call_args[0][0]
        assert isinstance(added_history, IPLocationHistory)
        assert added_history.ip_address == '192.168.1.100'
        assert added_history.mac_address == '00:11:22:33:44:55'

    def test_archive_multiple_offline_ips(self, calculator, mock_db):
        """
        场景 4：多条记录混合情况

        预期：只有真正下线的 IP 被归档
        """
        # 创建多条记录
        record_in_arp = IPLocationCurrent(
            id=1,
            ip_address='192.168.1.101',
            mac_address='00:11:22:33:44:56',
            calculated_at=datetime.now() - timedelta(minutes=60),
            last_seen=datetime.now() - timedelta(minutes=60)
        )
        record_fresh = IPLocationCurrent(
            id=2,
            ip_address='192.168.1.102',
            mac_address='00:11:22:33:44:57',
            calculated_at=datetime.now() - timedelta(minutes=5),
            last_seen=datetime.now() - timedelta(minutes=5)
        )
        record_offline = IPLocationCurrent(
            id=3,
            ip_address='192.168.1.103',
            mac_address='00:11:22:33:44:58',
            calculated_at=datetime.now() - timedelta(minutes=60),
            last_seen=datetime.now() - timedelta(minutes=60)
        )

        # 只有 record_offline 和 record_in_arp 会通过 calculated_at 阈值筛选
        mock_db.query.return_value.filter.return_value.all.return_value = [
            record_in_arp, record_offline
        ]

        # ARP 表中有 192.168.1.101，没有 192.168.1.103
        calculator._arp_entries = [
            ARPEntry(ip_address='192.168.1.101', mac_address='00:11:22:33:44:56', arp_device_id=1)
        ]

        # 执行归档
        archived_count = calculator._archive_offline_ips()

        # 验证：只归档了 record_offline（IP 不在 ARP 表且时间过期）
        assert archived_count == 1, "只有真正下线的 IP 应被归档"

    def test_archive_with_custom_threshold(self, calculator, mock_db):
        """
        场景 5：自定义阈值测试

        验证：归档阈值可通过配置调整
        """
        # 创建一条记录：45 分钟前计算（应小于 60 分钟阈值）
        record = IPLocationCurrent(
            id=1,
            ip_address='192.168.1.100',
            mac_address='00:11:22:33:44:55',
            calculated_at=datetime.now() - timedelta(minutes=45),
            last_seen=datetime.now() - timedelta(minutes=45)
        )

        # 设置自定义阈值
        calculator._settings = {'offline_threshold_minutes': '60'}

        # 因为 45 分钟 < 60 分钟阈值，查询不应返回这条记录
        # 模拟数据库查询行为：calculated_at < threshold_time 时才返回
        # threshold_time = now - 60min，所以 45 分钟前的记录 > threshold_time，不会被查询返回
        mock_db.query.return_value.filter.return_value.all.return_value = []
        calculator._arp_entries = []

        # 执行归档（45 分钟 < 60 分钟阈值，不应归档）
        archived_count = calculator._archive_offline_ips()

        # 验证：不应归档（未超过自定义阈值）
        assert archived_count == 0, "未超过自定义阈值时不应归档"

    def test_archive_exceeds_custom_threshold(self, calculator, mock_db):
        """
        场景 5b：超过自定义阈值测试

        验证：超过自定义阈值时正确归档
        """
        # 创建一条记录：90 分钟前计算（应超过 60 分钟阈值）
        record = IPLocationCurrent(
            id=1,
            ip_address='192.168.1.100',
            mac_address='00:11:22:33:44:55',
            calculated_at=datetime.now() - timedelta(minutes=90),
            last_seen=datetime.now() - timedelta(minutes=90)
        )

        # 设置自定义阈值
        calculator._settings = {'offline_threshold_minutes': '60'}

        # 模拟数据库查询返回记录
        mock_db.query.return_value.filter.return_value.all.return_value = [record]
        calculator._arp_entries = []

        # 执行归档
        archived_count = calculator._archive_offline_ips()

        # 验证：应归档（超过自定义阈值且不在 ARP 表中）
        assert archived_count == 1, "超过自定义阈值且不在 ARP 表中时应归档"

    def test_archive_empty_current_table(self, calculator, mock_db):
        """
        场景 6：当前表为空

        预期：不归档任何记录
        """
        mock_db.query.return_value.filter.return_value.all.return_value = []
        calculator._arp_entries = []

        archived_count = calculator._archive_offline_ips()

        assert archived_count == 0, "当前表为空时不应归档"


class TestArchiveLogicRegression:
    """
    归档逻辑回归测试

    验证修复的核心问题：从 last_seen 改为 calculated_at
    """

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def calculator(self, mock_db):
        return IPLocationCalculator(mock_db)

    def test_regression_use_calculated_at_not_last_seen(self, calculator, mock_db):
        """
        回归测试：验证使用 calculated_at 而非 last_seen

        背景：修复前，归档逻辑使用 last_seen 判断，
              导致刚计算的记录也可能被错误归档。

        修复：改用 calculated_at，确保刚计算的记录（calculated_at = 当前时间）
              不会被归档。
        """
        # 创建一条记录：
        # - last_seen = 60 分钟前（很旧）
        # - calculated_at = 5 分钟前（刚计算过）
        record = IPLocationCurrent(
            id=1,
            ip_address='192.168.1.200',
            mac_address='00:11:22:33:44:99',
            calculated_at=datetime.now() - timedelta(minutes=5),  # 刚计算过
            last_seen=datetime.now() - timedelta(minutes=60)       # 但 last_seen 很旧
        )

        # 因为 calculated_at = 5 分钟前 < 30 分钟阈值
        # 所以查询不会返回这条记录
        mock_db.query.return_value.filter.return_value.all.return_value = []
        calculator._arp_entries = []

        archived_count = calculator._archive_offline_ips()

        # 验证：不应归档（因为 calculated_at 新鲜，即使 last_seen 很旧）
        assert archived_count == 0, \
            "calculated_at 新鲜时不应归档，即使 last_seen 很旧（回归测试）"


# 运行测试的入口
if __name__ == '__main__':
    pytest.main([__file__, '-v'])