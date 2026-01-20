"""
巡检管理单元测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

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

def test_get_inspections():
    """
    测试获取巡检结果列表
    """
    response = client.get("/api/v1/inspections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_run_inspection():
    """
    测试执行设备巡检
    """
    # 先创建设备
    create_response = client.post("/api/v1/devices", json=test_device)
    device_id = create_response.json()["id"]
    
    # 执行巡检
    response = client.post(f"/api/v1/inspections/run/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data

def test_batch_run_inspections():
    """
    测试批量执行巡检
    """
    # 创建多个设备
    device_ids = []
    for i in range(2):
        device_data = test_device.copy()
        device_data["hostname"] = f"SW-TEST-INSPECT-{i+1}"
        device_data["ip_address"] = f"192.168.1.{120+i}"
        create_response = client.post("/api/v1/devices", json=device_data)
        device_ids.append(create_response.json()["id"])
    
    # 批量执行巡检
    response = client.post("/api/v1/inspections/batch/run", json=device_ids)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "total" in data
    assert data["total"] == 2

if __name__ == "__main__":
    pytest.main(["-v", __file__])