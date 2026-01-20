"""
Netmiko服务单元测试
测试Netmiko设备操作服务的核心功能
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.netmiko_service import NetmikoService
from app.models.models import Device


class TestNetmikoService:
    """Netmiko服务测试类"""
    
    @pytest.fixture
    def netmiko_service(self):
        """创建Netmiko服务实例"""
        return NetmikoService()
    
    @pytest.fixture
    def mock_device(self):
        """创建模拟设备"""
        device = Mock(spec=Device)
        device.id = 1
        device.hostname = "test-switch"
        device.ip_address = "10.23.2.20"
        device.vendor = "cisco"
        device.model = "Catalyst WS-C3850-48T"
        device.username = "admin"
        device.password = "toW3cBee"
        device.login_port = 22
        device.login_method = "ssh"
        return device
    
    def test_get_device_type_cisco(self, netmiko_service):
        """测试Cisco设备类型映射"""
        device_type = netmiko_service.get_device_type("cisco")
        assert device_type == "cisco_ios"
    
    def test_get_device_type_huawei(self, netmiko_service):
        """测试华为设备类型映射"""
        device_type = netmiko_service.get_device_type("huawei")
        assert device_type == "huawei"
    
    def test_get_device_type_h3c(self, netmiko_service):
        """测试H3C设备类型映射"""
        device_type = netmiko_service.get_device_type("h3c")
        assert device_type == "hp_comware"
    
    def test_get_device_type_unknown(self, netmiko_service):
        """测试未知设备类型映射"""
        device_type = netmiko_service.get_device_type("unknown")
        assert device_type == "cisco_ios"  # 默认返回Cisco IOS
    
    def test_get_commands_cisco_version(self, netmiko_service):
        """测试Cisco版本命令"""
        command = netmiko_service.get_commands("cisco", "version")
        assert command == "show version"
    
    def test_get_commands_cisco_interfaces(self, netmiko_service):
        """测试Cisco接口命令"""
        command = netmiko_service.get_commands("cisco", "interfaces")
        assert command == "show interfaces"
    
    def test_get_commands_huawei_version(self, netmiko_service):
        """测试华为版本命令"""
        command = netmiko_service.get_commands("huawei", "version")
        assert command == "display version"
    
    def test_get_commands_h3c_mac_table(self, netmiko_service):
        """测试H3C MAC地址表命令"""
        command = netmiko_service.get_commands("h3c", "mac_table")
        assert command == "display mac-address"
    
    def test_parse_version_info_cisco(self, netmiko_service):
        """测试Cisco版本信息解析"""
        output = """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
System image file is "flash:c3750-ipservicesk9-mz.150-2.SE11.bin"
cisco WS-C3750-24TS (PowerPC405) processor (revision H0) with 131072K bytes of memory.
Processor board ID FOC12345678
"""
        version_info = netmiko_service.parse_version_info(output, "cisco")
        
        assert "software_version" in version_info
        assert "Cisco IOS Software" in version_info["software_version"]
        assert "system_image" in version_info
        assert "c3750-ipservicesk9-mz" in version_info["system_image"]
    
    def test_parse_serial_from_version_cisco(self, netmiko_service):
        """测试从Cisco版本信息中解析序列号"""
        output = """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
Processor board ID FOC12345678
"""
        serial = netmiko_service.parse_serial_from_version(output, "cisco")
        assert serial == "FOC12345678"
    
    def test_parse_serial_from_inventory_cisco(self, netmiko_service):
        """测试从Cisco inventory中解析序列号"""
        output = """
NAME: "1", DESCR: "WS-C3750-24TS"
PID: WS-C3750-24TS-S  , VID: V05  , SN: FOC12345678
"""
        serial = netmiko_service.parse_serial_from_inventory(output, "cisco")
        assert serial == "FOC12345678"
    
    def test_parse_mac_table_cisco(self, netmiko_service):
        """测试Cisco MAC地址表解析"""
        output = """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
  10    0011.2233.4456    STATIC      Gi1/0/2
"""
        mac_table = netmiko_service.parse_mac_table(output, "cisco")
        
        assert len(mac_table) == 2
        assert mac_table[0]["mac_address"] == "0011.2233.4455"
        assert mac_table[0]["vlan_id"] == 1
        assert mac_table[0]["interface"] == "Gi1/0/1"
        assert mac_table[0]["address_type"] == "dynamic"
        
        assert mac_table[1]["mac_address"] == "0011.2233.4456"
        assert mac_table[1]["vlan_id"] == 10
        assert mac_table[1]["interface"] == "Gi1/0/2"
        assert mac_table[1]["address_type"] == "static"
    
    def test_parse_mac_table_huawei(self, netmiko_service):
        """测试华为MAC地址表解析"""
        output = """
MAC Address    VLAN/VSI    Learned-From        Type
0011-2233-4455 1/-         GE1/0/1             dynamic
0011-2233-4456 10/-        GE1/0/2             static
"""
        mac_table = netmiko_service.parse_mac_table(output, "huawei")
        
        assert len(mac_table) == 2
        assert mac_table[0]["mac_address"] == "0011-2233-4455"
        assert mac_table[0]["vlan_id"] == 1
        assert mac_table[0]["interface"] == "GE1/0/1"
        assert mac_table[0]["address_type"] == "dynamic"
    
    @pytest.mark.asyncio
    async def test_batch_collect_device_info_success(self, netmiko_service, mock_device):
        """测试批量采集设备信息成功场景"""
        # 模拟成功的采集结果
        with patch.object(netmiko_service, 'collect_device_version') as mock_version, \
             patch.object(netmiko_service, 'collect_device_serial') as mock_serial, \
             patch.object(netmiko_service, 'collect_interfaces_info') as mock_interfaces, \
             patch.object(netmiko_service, 'collect_mac_table') as mock_mac:
            
            mock_version.return_value = {
                "device_id": 1,
                "software_version": "Cisco IOS Software",
                "collected_at": datetime.now()
            }
            mock_serial.return_value = "FOC12345678"
            mock_interfaces.return_value = [
                {"device_id": 1, "port_name": "Gi1/0/1", "status": "up"}
            ]
            mock_mac.return_value = [
                {"device_id": 1, "mac_address": "00:11:22:33:44:55", "vlan_id": 1}
            ]
            
            devices = [mock_device]
            collect_types = ["version", "serial", "interfaces", "mac_table"]
            
            results = await netmiko_service.batch_collect_device_info(devices, collect_types)
            
            assert results["total"] == 1
            assert results["success"] == 1
            assert results["failed"] == 0
            assert len(results["details"]) == 1
            
            detail = results["details"][0]
            assert detail["device_id"] == 1
            assert detail["hostname"] == "test-switch"
            assert detail["success"] == True
            assert "version" in detail["data"]
            assert "serial" in detail["data"]
            assert "interfaces" in detail["data"]
            assert "mac_table" in detail["data"]
    
    @pytest.mark.asyncio
    async def test_batch_collect_device_info_partial_failure(self, netmiko_service, mock_device):
        """测试批量采集设备信息部分失败场景"""
        # 模拟部分失败的采集结果
        with patch.object(netmiko_service, 'collect_device_version') as mock_version, \
             patch.object(netmiko_service, 'collect_device_serial') as mock_serial:
            
            mock_version.return_value = None  # 版本采集失败
            mock_serial.return_value = "FOC12345678"  # 序列号采集成功
            
            devices = [mock_device]
            collect_types = ["version", "serial"]
            
            results = await netmiko_service.batch_collect_device_info(devices, collect_types)
            
            assert results["total"] == 1
            assert results["success"] == 1  # 只要有部分数据就算成功
            assert results["failed"] == 0
            
            detail = results["details"][0]
            assert detail["success"] == True
            assert "serial" in detail["data"]
            assert "version" not in detail["data"]
    
    @pytest.mark.asyncio
    async def test_batch_collect_device_info_all_failure(self, netmiko_service, mock_device):
        """测试批量采集设备信息全部失败场景"""
        # 模拟全部失败的采集结果
        with patch.object(netmiko_service, 'collect_device_version') as mock_version, \
             patch.object(netmiko_service, 'collect_device_serial') as mock_serial:
            
            mock_version.return_value = None
            mock_serial.return_value = None
            
            devices = [mock_device]
            collect_types = ["version", "serial"]
            
            results = await netmiko_service.batch_collect_device_info(devices, collect_types)
            
            assert results["total"] == 1
            assert results["success"] == 0
            assert results["failed"] == 1
            
            detail = results["details"][0]
            assert detail["success"] == False
            assert detail["error"] == "未采集到任何有效数据"
    
    def test_parse_interfaces_info_cisco(self, netmiko_service):
        """测试Cisco接口信息解析"""
        interfaces_output = """
GigabitEthernet1/0/1 is up, line protocol is up (connected)
  Hardware is Gigabit Ethernet, address is 0011.2233.4455 (bia 0011.2233.4455)
  Description: Uplink to Core Switch
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
  
GigabitEthernet1/0/2 is down, line protocol is down (notconnect)
  Hardware is Gigabit Ethernet, address is 0011.2233.4456 (bia 0011.2233.4456)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
"""
        
        interfaces = netmiko_service.parse_interfaces_info(interfaces_output, None, "cisco")
        
        assert len(interfaces) == 2
        
        # 检查第一个接口
        assert interfaces[0]["port_name"] == "GigabitEthernet1/0/1"
        assert interfaces[0]["status"] == "up"
        assert interfaces[0]["description"] == "Uplink to Core Switch"
        assert "1000000 Kbit" in interfaces[0]["speed"]
        
        # 检查第二个接口
        assert interfaces[1]["port_name"] == "GigabitEthernet1/0/2"
        assert interfaces[1]["status"] == "down"
    
    def test_parse_interfaces_info_with_status(self, netmiko_service):
        """测试带状态信息的接口解析"""
        interfaces_output = """
GigabitEthernet1/0/1 is up, line protocol is up
GigabitEthernet1/0/2 is down, line protocol is down
"""
        
        interface_status_output = """
Port      Name               Status       Vlan       Duplex  Speed Type
Gi1/0/1   Uplink             connected    1          a-full  a-100 10/100/1000BaseTX
Gi1/0/2   Access Port        notconnect   1          auto    auto  10/100/1000BaseTX
"""
        
        interfaces = netmiko_service.parse_interfaces_info(
            interfaces_output, 
            interface_status_output, 
            "cisco"
        )
        
        assert len(interfaces) == 2
        
        # 检查状态是否正确合并
        assert interfaces[0]["status"] == "up"
        assert interfaces[1]["status"] == "down"


class TestNetmikoServiceErrorHandling:
    """Netmiko服务错误处理测试类"""
    
    @pytest.fixture
    def netmiko_service(self):
        """创建Netmiko服务实例"""
        return NetmikoService()
    
    def test_get_device_type_empty_string(self, netmiko_service):
        """测试空字符串设备类型"""
        device_type = netmiko_service.get_device_type("")
        assert device_type == "cisco_ios"  # 默认返回
    
    def test_get_device_type_none(self, netmiko_service):
        """测试None设备类型"""
        device_type = netmiko_service.get_device_type(None)
        assert device_type == "cisco_ios"  # 默认返回
    
    def test_get_commands_invalid_vendor(self, netmiko_service):
        """测试无效厂商的命令获取"""
        command = netmiko_service.get_commands("invalid_vendor", "version")
        assert command == "show version"  # 默认返回Cisco命令
    
    def test_get_commands_invalid_command_type(self, netmiko_service):
        """测试无效命令类型"""
        command = netmiko_service.get_commands("cisco", "invalid_command")
        assert command == ""  # 返回空字符串
    
    def test_parse_version_info_empty_output(self, netmiko_service):
        """测试空输出的版本信息解析"""
        version_info = netmiko_service.parse_version_info("", "cisco")
        assert version_info == {}
    
    def test_parse_serial_from_version_no_serial(self, netmiko_service):
        """测试没有序列号的版本输出"""
        output = """
Cisco IOS Software, Version 15.0
No serial number here
"""
        serial = netmiko_service.parse_serial_from_version(output, "cisco")
        assert serial is None
    
    def test_parse_mac_table_empty_output(self, netmiko_service):
        """测试空输出的MAC地址表解析"""
        mac_table = netmiko_service.parse_mac_table("", "cisco")
        assert mac_table == []
    
    def test_parse_mac_table_invalid_format(self, netmiko_service):
        """测试无效格式的MAC地址表"""
        output = """
This is not a valid MAC table
No MAC addresses here
"""
        mac_table = netmiko_service.parse_mac_table(output, "cisco")
        assert mac_table == []
    
    @pytest.mark.asyncio
    async def test_batch_collect_device_info_exception(self, netmiko_service, mock_device):
        """测试批量采集时的异常处理"""
        # 模拟异常
        with patch.object(netmiko_service, 'collect_device_version') as mock_version:
            mock_version.side_effect = Exception("Network error")
            
            devices = [mock_device]
            collect_types = ["version"]
            
            results = await netmiko_service.batch_collect_device_info(devices, collect_types)
            
            assert results["total"] == 1
            assert results["success"] == 0
            assert results["failed"] == 1
            
            detail = results["details"][0]
            assert detail["success"] == False
            assert "Network error" in detail["error"]


if __name__ == "__main__":
    pytest.main([__file__])
