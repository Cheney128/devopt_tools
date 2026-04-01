# -*- coding: utf-8 -*-
"""
ARP 表解析单元测试

测试覆盖:
1. vendor 大小写处理
2. MAC 地址标准化
3. IP/MAC 格式验证
4. 数据过滤逻辑
"""
import pytest
import re
from unittest.mock import Mock, patch


from app.services.netmiko_service import NetmikoService
from app.services.arp_mac_scheduler import validate_arp_entry


class TestMACNormalization:
    """MAC 地址标准化测试"""

    @pytest.fixture
    def service(self):
        """创建 NetmikoService 实例"""
        return NetmikoService()

    def test_mac_normalization_huawei(self, service):
        """测试华为 MAC 标准化 (横线格式)"""
        result = service._normalize_mac_address("609b-b431-d2c3")
        assert result == "60:9B:B4:31:D2:C3"

    def test_mac_normalization_cisco(self, service):
        """测试 Cisco MAC 标准化 (点格式)"""
        result = service._normalize_mac_address("2401.c7d9.2241")
        assert result == "24:01:C7:D9:22:41"

    def test_mac_normalization_h3c(self, service):
        """测试 H3C MAC 标准化 (横线格式)"""
        result = service._normalize_mac_address("3cc7-86b4-72c4")
        assert result == "3C:C7:86:B4:72:C4"

    def test_mac_normalization_standard(self, service):
        """测试标准冒号格式 MAC"""
        result = service._normalize_mac_address("3C:C7:86:B4:72:C4")
        assert result == "3C:C7:86:B4:72:C4"

    def test_mac_normalization_lowercase(self, service):
        """测试小写 MAC 标准化"""
        result = service._normalize_mac_address("3c:c7:86:b4:72:c4")
        assert result == "3C:C7:86:B4:72:C4"

    def test_mac_normalization_no_separator(self, service):
        """测试无分隔符 MAC 标准化"""
        result = service._normalize_mac_address("3CC786B472C4")
        assert result == "3C:C7:86:B4:72:C4"

    def test_mac_normalization_invalid(self, service):
        """测试无效 MAC 处理"""
        result = service._normalize_mac_address("invalid")
        assert result == "INVALID"  # 返回原值大写


class TestVendorCaseInsensitive:
    """vendor 大小写测试"""

    @pytest.fixture
    def service(self):
        """创建 NetmikoService 实例"""
        return NetmikoService()

    def test_h3c_vendor_case_insensitive(self, service):
        """测试 H3C vendor 大小写"""
        # 模拟 ARP 表输出
        mock_output = """
  IP 地址      MAC 地址     VLAN  接口
  10.23.2.1   609b-b431-d2c3   10    GE1/0/1
"""
        # 测试大写 H3C
        result_upper = service._parse_arp_table(mock_output, "H3C")
        assert len(result_upper) == 1
        assert result_upper[0]['ip_address'] == '10.23.2.1'
        assert result_upper[0]['mac_address'] == '60:9B:B4:31:D2:C3'

        # 测试小写 h3c
        result_lower = service._parse_arp_table(mock_output, "h3c")
        assert len(result_lower) == 1
        assert result_lower[0]['mac_address'] == '60:9B:B4:31:D2:C3'

    def test_huawei_vendor_case_insensitive(self, service):
        """测试 Huawei vendor 大小写"""
        # 模拟 ARP 表输出
        mock_output = """
  IP 地址      MAC 地址     VLAN  接口
  10.23.2.56  2401.c7d9.2241   20    GE1/0/2
"""
        # 测试混合大小写 Huawei
        result_mixed = service._parse_arp_table(mock_output, "Huawei")
        assert len(result_mixed) == 1
        assert result_mixed[0]['ip_address'] == '10.23.2.56'
        assert result_mixed[0]['mac_address'] == '24:01:C7:D9:22:41'

        # 测试小写 huawei
        result_lower = service._parse_arp_table(mock_output, "huawei")
        assert len(result_lower) == 1
        assert result_lower[0]['mac_address'] == '24:01:C7:D9:22:41'

    def test_cisco_vendor_case_insensitive(self, service):
        """测试 Cisco vendor 大小写"""
        # 模拟 Cisco ARP 表输出
        mock_output = """
Protocol  IP Address      Age (min)  MAC Address     Type   Interface
Internet  10.23.2.13      -          0011.2233.4455  ARPA   Gi1/0/1
"""
        # 测试大写 CISCO
        result_upper = service._parse_arp_table(mock_output, "CISCO")
        assert len(result_upper) == 1
        assert result_upper[0]['ip_address'] == '10.23.2.13'
        assert result_upper[0]['mac_address'] == '00:11:22:33:44:55'

        # 测试小写 cisco
        result_lower = service._parse_arp_table(mock_output, "cisco")
        assert len(result_lower) == 1
        assert result_lower[0]['mac_address'] == '00:11:22:33:44:55'


class TestARPValidation:
    """ARP 条目验证测试"""

    def test_valid_entry(self):
        """测试有效条目"""
        entry = {
            'ip_address': '10.23.2.1',
            'mac_address': '60:9B:B4:31:D2:C3'
        }
        assert validate_arp_entry(entry) == True

    def test_invalid_ip_filter(self):
        """测试无效 IP 过滤"""
        entry = {
            'ip_address': 'invalid-ip',
            'mac_address': '60:9B:B4:31:D2:C3'
        }
        assert validate_arp_entry(entry) == False

    def test_invalid_mac_filter(self):
        """测试无效 MAC 过滤"""
        entry = {
            'ip_address': '10.23.2.1',
            'mac_address': 'invalid-mac'
        }
        assert validate_arp_entry(entry) == False

    def test_missing_ip_field(self):
        """测试缺少 IP 字段"""
        entry = {
            'mac_address': '60:9B:B4:31:D2:C3'
        }
        assert validate_arp_entry(entry) == False

    def test_missing_mac_field(self):
        """测试缺少 MAC 字段"""
        entry = {
            'ip_address': '10.23.2.1'
        }
        assert validate_arp_entry(entry) == False

    def test_empty_fields(self):
        """测试空字段"""
        entry = {
            'ip_address': '',
            'mac_address': ''
        }
        assert validate_arp_entry(entry) == False


class TestARPParsing:
    """ARP 表解析集成测试"""

    @pytest.fixture
    def service(self):
        """创建 NetmikoService 实例"""
        return NetmikoService()

    def test_huawei_arp_parsing(self, service):
        """测试华为 ARP 表解析"""
        mock_output = """
  IP 地址      MAC 地址     VLAN  接口         老化时间    类型
  10.23.2.1   609b-b431-d2c3   10    GE1/0/1      5         dynamic
  10.23.2.2   2401.c7d9.2241   20    GE1/0/2      10        dynamic
"""
        result = service._parse_arp_table(mock_output, "huawei")
        assert len(result) == 2
        assert result[0]['ip_address'] == '10.23.2.1'
        assert result[0]['mac_address'] == '60:9B:B4:31:D2:C3'
        assert result[0]['vlan_id'] == 10
        assert result[0]['interface'] == 'GE1/0/1'

    def test_cisco_arp_parsing(self, service):
        """测试 Cisco ARP 表解析"""
        mock_output = """
Protocol  IP Address      Age (min)  MAC Address     Type   Interface
Internet  10.23.2.13      -          0011.2233.4455  ARPA   Gi1/0/1
Internet  10.23.2.14      5          0022.3344.5566  ARPA   Gi1/0/2
"""
        result = service._parse_arp_table(mock_output, "cisco")
        assert len(result) == 2
        assert result[0]['ip_address'] == '10.23.2.13'
        assert result[0]['mac_address'] == '00:11:22:33:44:55'
        assert result[0]['interface'] == 'Gi1/0/1'

    def test_invalid_data_filtered(self, service):
        """测试无效数据被过滤"""
        mock_output = """
  IP 地址      MAC 地址     VLAN  接口
  10.23.2.1   609b-b431-d2c3   10    GE1/0/1
  invalid-ip  2401.c7d9.2241   20    GE1/0/2
  10.23.2.3   invalid-mac      30    GE1/0/3
"""
        result = service._parse_arp_table(mock_output, "huawei")
        # 只有第一条有效
        assert len(result) == 1
        assert result[0]['ip_address'] == '10.23.2.1'
