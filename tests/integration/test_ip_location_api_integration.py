"""
IP定位API集成测试
测试IP定位功能的完整流程，包括核心交换机过滤、设备角色管理和配置管理
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import get_db
from app.models.models import Base, Device


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ip_location.db"
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
        "hostname": "core-switch-01",
        "ip_address": "10.0.0.1",
        "vendor": "Huawei",
        "model": "S7706",
        "location": "机房A",
        "status": "active",
        "login_method": "ssh",
        "login_port": 22,
        "username": "admin",
        "password": "password123"
    }


@pytest.fixture
def create_test_devices(test_client, mock_device_data):
    """创建测试设备"""
    devices = [
        {**mock_device_data, "hostname": "core-switch-01", "ip_address": "10.0.0.1", "location": "机房A"},
        {**mock_device_data, "hostname": "access-switch-01", "ip_address": "10.0.0.2", "location": "机房A"},
        {**mock_device_data, "hostname": "distribution-switch-01", "ip_address": "10.0.0.3", "location": "机房B"}
    ]
    
    created_devices = []
    for device in devices:
        response = test_client.post("/api/v1/devices/", json=device)
        assert response.status_code == 201
        created_devices.append(response.json())
    
    return created_devices


class TestIPLocationAPIIntegration:
    """IP定位API集成测试"""

    def test_complete_device_role_workflow(self, test_client, create_test_devices):
        """测试完整的设备角色管理工作流"""
        devices = create_test_devices
        
        # 1. 智能推断设备角色
        with patch('app.api.endpoints.devices.DeviceRoleManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.preview_infer_results.return_value = [
                {
                    "device_id": devices[0]["id"],
                    "hostname": "core-switch-01",
                    "current_role": None,
                    "inferred_role": "core",
                    "confidence": 0.95
                },
                {
                    "device_id": devices[1]["id"],
                    "hostname": "access-switch-01",
                    "current_role": None,
                    "inferred_role": "access",
                    "confidence": 0.9
                }
            ]
            mock_instance.apply_infer_results.return_value = (2, 0, 0)
            mock_instance.is_valid_role.return_value = True
            mock_manager.return_value = mock_instance
            
            # 预览推断结果
            infer_response = test_client.post("/api/v1/devices/role/infer")
            assert infer_response.status_code == 200
            infer_data = infer_response.json()
            assert infer_data["total"] == 2
            
            # 应用推断结果
            apply_response = test_client.post(
                "/api/v1/devices/role/infer/apply",
                json={"updates": [
                    {"device_id": devices[0]["id"], "role": "core"},
                    {"device_id": devices[1]["id"], "role": "access"}
                ]}
            )
            assert apply_response.status_code == 200
            apply_data = apply_response.json()
            assert apply_data["updated"] == 2

    def test_configuration_and_locate_workflow(self, test_client):
        """测试配置管理和IP定位工作流"""
        
        # 1. 获取默认配置
        with patch('app.api.endpoints.ip_location_config.IPLocationConfigManager') as mock_config_manager:
            mock_instance = Mock()
            mock_instance.get_all_configs.return_value = {
                "enable_core_switch_filter": True,
                "core_switch_keywords": "core,核心"
            }
            mock_instance.get_config.return_value = True
            mock_instance.validate_config.return_value = (True, None)
            mock_instance.set_config.return_value = True
            mock_config_manager.return_value = mock_instance
            
            # 获取所有配置
            get_configs_response = test_client.get("/api/v1/ip-location/configs")
            assert get_configs_response.status_code == 200
            
            # 更新单个配置
            update_response = test_client.put(
                "/api/v1/ip-location/configs/enable_core_switch_filter",
                json={"value": "false"}
            )
            assert update_response.status_code == 200

    def test_locate_ip_with_filters(self, test_client):
        """测试带过滤器的IP定位"""
        
        with patch('app.api.endpoints.ip_location.get_ip_location_service') as mock_service:
            mock_instance = Mock()
            mock_instance.locate_ip.return_value = []
            mock_service.return_value = mock_instance
            
            # 测试带filter_core_switch参数
            locate_response = test_client.post(
                "/api/ip-location/locate",
                json={
                    "ip_address": "192.168.1.100",
                    "filter_uplink": True,
                    "filter_core_switch": True
                }
            )
            assert locate_response.status_code == 200
            
            # 测试带location参数
            search_response = test_client.get(
                "/api/ip-location/search/192.168.1.100?location=机房A"
            )
            assert search_response.status_code == 200

    def test_batch_set_role_by_vendor(self, test_client, create_test_devices):
        """测试按厂商批量设置角色"""
        
        with patch('app.api.endpoints.devices.DeviceRoleManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.batch_set_role_by_vendor.return_value = (3, 0)
            mock_manager.return_value = mock_instance
            
            response = test_client.put(
                "/api/v1/devices/role/batch-by-vendor",
                json={"vendor": "Huawei", "role": "core"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 3
            assert data["updated"] == 3

    def test_get_devices_by_role(self, test_client, create_test_devices):
        """测试按角色查询设备"""
        
        with patch('app.api.endpoints.devices.DeviceRoleManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_devices_by_role.return_value = (1, [])
            mock_instance.is_valid_role.return_value = True
            mock_manager.return_value = mock_instance
            
            response = test_client.get("/api/v1/devices/by-role/core?page=1&page_size=50")
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "devices" in data


class TestIPLocationConfigIntegration:
    """IP定位配置管理集成测试"""

    def test_config_crud_operations(self, test_client):
        """测试配置的完整CRUD操作"""
        
        with patch('app.api.endpoints.ip_location_config.IPLocationConfigManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.get_all_configs.return_value = {
                "enable_core_switch_filter": True,
                "core_switch_keywords": "core,核心"
            }
            mock_instance.get_config.side_effect = lambda key: True if key == "enable_core_switch_filter" else None
            mock_instance.validate_config.return_value = (True, None)
            mock_instance.set_config.return_value = True
            mock_instance.reset_config.return_value = True
            mock_instance.reset_all_configs.return_value = True
            mock_manager.return_value = mock_instance
            
            # 1. 获取所有配置
            get_all_response = test_client.get("/api/v1/ip-location/configs")
            assert get_all_response.status_code == 200
            
            # 2. 更新配置
            update_response = test_client.put(
                "/api/v1/ip-location/configs/enable_core_switch_filter",
                json={"value": "false"}
            )
            assert update_response.status_code == 200
            
            # 3. 批量更新配置
            batch_update_response = test_client.put(
                "/api/v1/ip-location/configs",
                json={"configs": {
                    "enable_core_switch_filter": "true",
                    "core_switch_keywords": "core,main"
                }}
            )
            assert batch_update_response.status_code == 200
            
            # 4. 重置单个配置
            reset_response = test_client.delete(
                "/api/v1/ip-location/configs/enable_core_switch_filter"
            )
            assert reset_response.status_code == 200
            
            # 5. 重置所有配置
            reset_all_response = test_client.delete("/api/v1/ip-location/configs")
            assert reset_all_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])
