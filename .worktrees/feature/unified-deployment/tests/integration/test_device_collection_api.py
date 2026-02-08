"""
设备信息采集API集成测试
测试设备信息采集功能的完整流程
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import get_db
from app.models.models import Base, Device, DeviceVersion, Port, MACAddress


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆盖数据库依赖
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_client():
    """创建测试客户端"""
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_device_data():
    """创建模拟设备数据"""
    return {
        "hostname": "test-switch",
        "ip_address": "192.168.1.100",
        "vendor": "cisco",
        "model": "Catalyst 3750",
        "os_version": "15.0(2)SE11",
        "location": "Test Lab",
        "contact": "admin@example.com",
        "status": "active",
        "login_method": "ssh",
        "login_port": 22,
        "username": "admin",
        "password": "password123",
        "sn": "FOC12345678"
    }


@pytest.fixture
def create_test_device(test_client, mock_device_data):
    """创建测试设备"""
    response = test_client.post("/api/v1/devices", json=mock_device_data)
    assert response.status_code == 201
    return response.json()


class TestDeviceCollectionAPI:
    """设备信息采集API测试类"""
    
    def test_collect_device_version_success(self, test_client, create_test_device):
        """测试成功采集设备版本信息"""
        device_id = create_test_device["id"]
        
        # 模拟Netmiko连接和命令执行
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
System image file is "flash:c3750-ipservicesk9-mz.150-2.SE11.bin"
cisco WS-C3750-24TS (PowerPC405) processor (revision H0) with 131072K bytes of memory.
Processor board ID FOC12345678
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/version")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "Version info collected successfully" in data["message"]
            assert data["data"]["software_version"] is not None
    
    def test_collect_device_version_device_not_found(self, test_client):
        """测试设备不存在时的版本信息采集"""
        response = test_client.post("/api/v1/devices/999/collect/version")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_collect_device_serial_success(self, test_client, create_test_device):
        """测试成功采集设备序列号"""
        device_id = create_test_device["id"]
        
        # 模拟Netmiko连接和命令执行
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
Processor board ID FOC12345678
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/serial")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "Serial number collected successfully" in data["message"]
            assert data["data"]["serial"] == "FOC12345678"
    
    def test_collect_interfaces_info_success(self, test_client, create_test_device):
        """测试成功采集接口信息"""
        device_id = create_test_device["id"]
        
        # 模拟Netmiko连接和命令执行
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.side_effect = [
                # show interfaces 输出
                """
GigabitEthernet1/0/1 is up, line protocol is up (connected)
  Hardware is Gigabit Ethernet, address is 0011.2233.4455 (bia 0011.2233.4455)
  Description: Uplink to Core Switch
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
  
GigabitEthernet1/0/2 is down, line protocol is down (notconnect)
  Hardware is Gigabit Ethernet, address is 0011.2233.4456 (bia 0011.2233.4456)
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
""",
                # show interfaces status 输出
                """
Port      Name               Status       Vlan       Duplex  Speed Type
Gi1/0/1   Uplink             connected    1          a-full  a-100 10/100/1000BaseTX
Gi1/0/2   Access Port        notconnect   1          auto    auto  10/100/1000BaseTX
"""
            ]
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/interfaces")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "Interfaces info collected successfully" in data["message"]
            assert data["data"]["interfaces_count"] == 2
    
    def test_collect_mac_table_success(self, test_client, create_test_device):
        """测试成功采集MAC地址表"""
        device_id = create_test_device["id"]
        
        # 模拟Netmiko连接和命令执行
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
  10    0011.2233.4456    STATIC      Gi1/0/2
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/mac-table")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "MAC table collected successfully" in data["message"]
            assert data["data"]["mac_entries_count"] == 2
    
    def test_get_mac_addresses_empty(self, test_client):
        """测试获取空的MAC地址表"""
        response = test_client.get("/api/v1/devices/mac-addresses")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_search_mac_addresses_not_found(self, test_client):
        """测试搜索不存在的MAC地址"""
        response = test_client.post("/api/v1/devices/mac-addresses/search", json="00:11:22:33:44:55")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_device_mac_addresses_device_not_found(self, test_client):
        """测试获取不存在设备的MAC地址表"""
        response = test_client.get("/api/v1/devices/999/mac-addresses")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_batch_collect_device_info_success(self, test_client, create_test_device):
        """测试批量采集设备信息成功"""
        device_id = create_test_device["id"]
        
        # 模拟Netmiko连接和命令执行
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.side_effect = [
                # 版本信息
                """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
Processor board ID FOC12345678
""",
                # 序列号（从inventory）
                """
NAME: "1", DESCR: "WS-C3750-24TS"
PID: WS-C3750-24TS-S  , VID: V05  , SN: FOC12345678
""",
                # 接口信息
                """
GigabitEthernet1/0/1 is up, line protocol is up (connected)
  Description: Uplink to Core Switch
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
""",
                # MAC地址表
                """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
"""
            ]
            mock_connect.return_value = mock_connection
            
            request_data = {
                "device_ids": [device_id],
                "collect_types": ["version", "serial", "interfaces", "mac_table"]
            }
            
            response = test_client.post("/api/v1/devices/batch/collect", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "Batch collection completed" in data["message"]
            assert data["data"]["total"] == 1
            assert data["data"]["success"] == 1
            assert data["data"]["failed"] == 0
    
    def test_batch_collect_device_info_empty_devices(self, test_client):
        """测试批量采集空设备列表"""
        request_data = {
            "device_ids": [],
            "collect_types": ["version"]
        }
        
        response = test_client.post("/api/v1/devices/batch/collect", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "No valid devices found" in data["message"]
    
    def test_batch_collect_device_info_invalid_device_ids(self, test_client):
        """测试批量采集无效设备ID"""
        request_data = {
            "device_ids": [999, 1000],
            "collect_types": ["version"]
        }
        
        response = test_client.post("/api/v1/devices/batch/collect", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "No valid devices found" in data["message"]
    
    def test_batch_collect_device_info_connection_error(self, test_client, create_test_device):
        """测试批量采集时的连接错误"""
        device_id = create_test_device["id"]
        
        # 模拟连接错误
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            request_data = {
                "device_ids": [device_id],
                "collect_types": ["version"]
            }
            
            response = test_client.post("/api/v1/devices/batch/collect", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == False
            assert "Error in batch collection" in data["message"]


class TestMACAddressManagementAPI:
    """MAC地址管理API测试类"""
    
    def test_create_and_get_mac_addresses(self, test_client, create_test_device):
        """测试创建和获取MAC地址"""
        device_id = create_test_device["id"]
        
        # 首先采集MAC地址表
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
  10    0011.2233.4456    STATIC      Gi1/0/2
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/mac-table")
            assert response.status_code == 200
        
        # 获取所有MAC地址
        response = test_client.get("/api/v1/devices/mac-addresses")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # 按设备ID过滤
        response = test_client.get(f"/api/v1/devices/mac-addresses?device_id={device_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # 按VLAN ID过滤
        response = test_client.get("/api/v1/devices/mac-addresses?vlan_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["vlan_id"] == 1
        
        # 按接口过滤
        response = test_client.get("/api/v1/devices/mac-addresses?interface=Gi1/0/1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["interface"] == "Gi1/0/1"
    
    def test_search_mac_addresses(self, test_client, create_test_device):
        """测试搜索MAC地址"""
        device_id = create_test_device["id"]
        
        # 首先采集MAC地址表
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/mac-table")
            assert response.status_code == 200
        
        # 搜索MAC地址
        response = test_client.post("/api/v1/devices/mac-addresses/search", json="0011.2233.4455")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "0011.2233.4455" in data[0]["mac_address"]
        
        # 模糊搜索
        response = test_client.post("/api/v1/devices/mac-addresses/search", json="0011.22")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
    
    def test_get_device_mac_addresses_pagination(self, test_client, create_test_device):
        """测试设备MAC地址分页"""
        device_id = create_test_device["id"]
        
        # 创建多个MAC地址记录
        with patch('app.services.netmiko_service.ConnectHandler') as mock_connect:
            mock_connection = Mock()
            mock_connection.send_command.return_value = """
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0011.2233.4455    DYNAMIC     Gi1/0/1
   1    0011.2233.4456    DYNAMIC     Gi1/0/2
   1    0011.2233.4457    DYNAMIC     Gi1/0/3
   1    0011.2233.4458    DYNAMIC     Gi1/0/4
   1    0011.2233.4459    DYNAMIC     Gi1/0/5
"""
            mock_connect.return_value = mock_connection
            
            response = test_client.post(f"/api/v1/devices/{device_id}/collect/mac-table")
            assert response.status_code == 200
        
        # 测试分页
        response = test_client.get(f"/api/v1/devices/{device_id}/mac-addresses?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        response = test_client.get(f"/api/v1/devices/{device_id}/mac-addresses?skip=3&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


if __name__ == "__main__":
    pytest.main([__file__])
