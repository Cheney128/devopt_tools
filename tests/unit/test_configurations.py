"""
配置管理单元测试
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.oxidized_service import OxidizedService

# 创建测试客户端
client = TestClient(app)

# 测试数据
test_device = {
    "hostname": "SW-TEST-001",
    "ip_address": "192.168.1.100",
    "vendor": "Huawei",
    "model": "S5700",
    "status": "active"
}

def test_get_configurations():
    """
    测试获取配置列表
    """
    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@patch("app.services.oxidized_service.OxidizedService.get_oxidized_status")
def test_get_oxidized_status(mock_get_status):
    """
    测试获取Oxidized服务状态
    """
    # 模拟返回值
    mock_get_status.return_value = {
        "success": True,
        "status": "running"
    }
    
    response = client.get("/api/v1/configurations/oxidized/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["status"] == "running"

@patch("app.services.oxidized_service.OxidizedService.sync_with_oxidized")
def test_sync_with_oxidized(mock_sync):
    """
    测试与Oxidized同步设备信息
    """
    # 模拟返回值
    mock_sync.return_value = {
        "success": True,
        "message": "Synced 5 devices from Oxidized"
    }
    
    response = client.post("/api/v1/configurations/oxidized/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Synced 5 devices from Oxidized" in data["message"]

@patch("app.services.oxidized_service.OxidizedService.get_device_config")
def test_get_config_from_oxidized(mock_get_config):
    """
    测试从Oxidized获取设备配置
    """
    # 先创建设备
    create_response = client.post("/api/v1/devices", json=test_device)
    device_id = create_response.json()["id"]
    
    # 模拟返回值
    mock_get_config.return_value = "interface GigabitEthernet1/0/1\n description Test\n!"
    
    response = client.get(f"/api/v1/configurations/oxidized/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Config fetched from Oxidized and saved" in data["message"]
    assert "config_id" in data

if __name__ == "__main__":
    pytest.main(["-v", __file__])