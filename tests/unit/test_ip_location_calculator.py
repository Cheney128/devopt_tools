# -*- coding: utf-8 -*-
"""
IP 定位预计算服务单元测试
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Optional

from app.services.ip_location_calculator import (
    IPLocationCalculator,
    ARPEntry,
    MACEntry,
    DeviceInfo,
    CalculationResult
)


class TestIPLocationCalculator:
    """IPLocationCalculator 测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def calculator(self, mock_db):
        """创建计算器实例"""
        return IPLocationCalculator(mock_db)

    def test_init(self, calculator, mock_db):
        """测试初始化"""
        assert calculator.db == mock_db
        assert calculator._device_cache == {}
        assert calculator._arp_entries == []
        assert calculator._mac_entries == []

    def test_is_core_switch_positive(self, calculator):
        """测试核心交换机判断 - 正向"""
        device = DeviceInfo(
            id=1,
            hostname='Core-SW-01',
            ip_address='10.0.0.1',
            location='机房A'
        )
        assert calculator._is_core_switch(device) is True

    def test_is_core_switch_negative(self, calculator):
        """测试核心交换机判断 - 反向"""
        device = DeviceInfo(
            id=2,
            hostname='Access-SW-01',
            ip_address='10.0.0.2',
            location='楼层B'
        )
        assert calculator._is_core_switch(device) is False

    def test_is_core_switch_none(self, calculator):
        """测试核心交换机判断 - None"""
        assert calculator._is_core_switch(None) is False

    def test_is_uplink_interface_positive(self, calculator):
        """测试上行链路判断 - 正向"""
        assert calculator._is_uplink_interface('Eth-Trunk1') is True
        assert calculator._is_uplink_interface('uplink-port') is True

    def test_is_uplink_interface_negative(self, calculator):
        """测试上行链路判断 - 反向"""
        assert calculator._is_uplink_interface('GigabitEthernet1/0/1') is False
        assert calculator._is_uplink_interface('Ethernet0/1') is False

    def test_is_uplink_interface_none(self, calculator):
        """测试上行链路判断 - None"""
        assert calculator._is_uplink_interface(None) is False

    def test_calculate_confidence_base(self, calculator):
        """测试置信度计算 - 基础"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1
        )
        mac = MACEntry(
            mac_address='00:11:22:33:44:55',
            mac_device_id=2,
            mac_interface='Gi1/0/1',
            is_trunk=False
        )

        confidence = calculator._calculate_confidence(arp, mac, False)
        assert confidence >= Decimal('0.50')
        assert confidence <= Decimal('1.00')

    def test_calculate_confidence_vlan_match(self, calculator):
        """测试置信度计算 - VLAN 匹配"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1,
            vlan_id=100
        )
        mac = MACEntry(
            mac_address='00:11:22:33:44:55',
            mac_device_id=2,
            mac_interface='Gi1/0/1',
            vlan_id=100,
            is_trunk=False
        )

        confidence = calculator._calculate_confidence(arp, mac, True)
        assert confidence >= Decimal('0.70')  # 基础 0.50 + VLAN 匹配 0.20

    def test_calculate_confidence_max(self, calculator):
        """测试置信度计算 - 最大值限制"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1,
            vlan_id=100,
            last_seen=datetime.now()
        )
        mac = MACEntry(
            mac_address='00:11:22:33:44:55',
            mac_device_id=2,
            mac_interface='Gi1/0/1',
            vlan_id=100,
            is_trunk=False,
            interface_description='User PC',
            last_seen=datetime.now()
        )

        confidence = calculator._calculate_confidence(arp, mac, True)
        assert confidence <= Decimal('1.00')

    def test_match_mac_to_arp_single(self, calculator):
        """测试 MAC 匹配 - 单个匹配"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1
        )

        mac_map = {
            '00:11:22:33:44:55': [
                MACEntry(
                    mac_address='00:11:22:33:44:55',
                    mac_device_id=2,
                    mac_interface='Gi1/0/1'
                )
            ]
        }

        result, match_type = calculator._match_mac_to_arp(arp, mac_map)
        assert result is not None
        assert match_type == 'single_match'

    def test_match_mac_to_arp_no_match(self, calculator):
        """测试 MAC 匹配 - 无匹配"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1
        )

        mac_map = {}

        result, match_type = calculator._match_mac_to_arp(arp, mac_map)
        assert result is None
        assert match_type == 'no_mac_found'

    def test_match_mac_to_arp_cross_device(self, calculator):
        """测试 MAC 匹配 - 跨设备多匹配"""
        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1,
            vlan_id=100
        )

        mac_map = {
            '00:11:22:33:44:55': [
                MACEntry(
                    mac_address='00:11:22:33:44:55',
                    mac_device_id=2,
                    mac_interface='Gi1/0/1',
                    vlan_id=100
                ),
                MACEntry(
                    mac_address='00:11:22:33:44:55',
                    mac_device_id=3,
                    mac_interface='Gi2/0/1',
                    vlan_id=200
                )
            ]
        }

        result, match_type = calculator._match_mac_to_arp(arp, mac_map)
        assert result is not None
        assert match_type == 'cross_device'

    def test_fill_device_redundancy(self, calculator):
        """测试填充设备冗余信息"""
        calculator._device_cache = {
            1: DeviceInfo(id=1, hostname='SW-A', ip_address='10.0.0.10', location='机房A'),
            2: DeviceInfo(id=2, hostname='SW-B', ip_address='10.0.0.11', location='机房B'),
        }

        arp = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1
        )

        mac = MACEntry(
            mac_address='00:11:22:33:44:55',
            mac_device_id=2,
            mac_interface='Gi1/0/1'
        )

        result = CalculationResult(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_source_device_id=1,
            mac_hit_device_id=2,
            access_interface='Gi1/0/1',
            vlan_id=None,
            confidence=Decimal('0.80'),
            is_uplink=False,
            is_core_switch=False,
            match_type='single_match',
            last_seen=datetime.now()
        )

        calculator._fill_device_redundancy(result, arp, mac)

        assert result.arp_device_hostname == 'SW-A'
        assert result.arp_device_ip == '10.0.0.10'
        assert result.arp_device_location == '机房A'
        assert result.mac_device_hostname == 'SW-B'
        assert result.mac_device_ip == '10.0.0.11'
        assert result.mac_device_location == '机房B'


class TestARPEntry:
    """ARPEntry 数据类测试"""

    def test_create(self):
        """测试创建 ARP 条目"""
        entry = ARPEntry(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_device_id=1,
            vlan_id=100,
            arp_interface='Vlan100'
        )

        assert entry.ip_address == '10.0.0.1'
        assert entry.mac_address == '00:11:22:33:44:55'
        assert entry.arp_device_id == 1
        assert entry.vlan_id == 100
        assert entry.arp_interface == 'Vlan100'


class TestMACEntry:
    """MACEntry 数据类测试"""

    def test_create(self):
        """测试创建 MAC 条目"""
        entry = MACEntry(
            mac_address='00:11:22:33:44:55',
            mac_device_id=1,
            mac_interface='GigabitEthernet1/0/1',
            vlan_id=100,
            is_trunk=False
        )

        assert entry.mac_address == '00:11:22:33:44:55'
        assert entry.mac_device_id == 1
        assert entry.mac_interface == 'GigabitEthernet1/0/1'
        assert entry.vlan_id == 100
        assert entry.is_trunk is False


class TestDeviceInfo:
    """DeviceInfo 数据类测试"""

    def test_create(self):
        """测试创建设备信息"""
        device = DeviceInfo(
            id=1,
            hostname='Core-SW-01',
            ip_address='10.0.0.1',
            location='机房A',
            vendor='Huawei',
            model='S5735'
        )

        assert device.id == 1
        assert device.hostname == 'Core-SW-01'
        assert device.ip_address == '10.0.0.1'
        assert device.location == '机房A'


class TestCalculationResult:
    """CalculationResult 数据类测试"""

    def test_create(self):
        """测试创建计算结果"""
        now = datetime.now()
        result = CalculationResult(
            ip_address='10.0.0.1',
            mac_address='00:11:22:33:44:55',
            arp_source_device_id=1,
            mac_hit_device_id=2,
            access_interface='Gi1/0/1',
            vlan_id=100,
            confidence=Decimal('0.85'),
            is_uplink=False,
            is_core_switch=False,
            match_type='single_match',
            last_seen=now,
            arp_device_hostname='SW-A',
            arp_device_ip='10.0.0.10',
            arp_device_location='机房A'
        )

        assert result.ip_address == '10.0.0.1'
        assert result.confidence == Decimal('0.85')
        assert result.match_type == 'single_match'
        assert result.arp_device_hostname == 'SW-A'


# 运行测试的入口
if __name__ == '__main__':
    pytest.main([__file__, '-v'])