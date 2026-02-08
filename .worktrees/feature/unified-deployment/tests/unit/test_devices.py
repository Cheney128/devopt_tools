"""
设备管理单元测试
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base, get_db
from app.models.models import Device

# 创建内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建测试数据库表
Base.metadata.create_all(bind=engine)

# 依赖项覆盖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 创建测试客户端
client = TestClient(app)

# 测试数据
test_device = {
    "hostname": "SW-TEST-001",
    "ip_address": "192.168.1.100",
    "vendor": "Huawei",
    "model": "S5700",
    "os_version": "V200R019C00",
    "location": "测试机房",
    "contact": "test@example.com",
    "status": "active"
}

def test_create_device():
    """
    测试创建设备
    """
    response = client.post("/api/v1/devices", json=test_device)
    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == test_device["hostname"]
    assert data["ip_address"] == test_device["ip_address"]
    assert data["vendor"] == test_device["vendor"]
    assert "id" in data

def test_get_devices():
    """
    测试获取设备列表
    """
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_device():
    """
    测试获取设备详情
    """
    # 先创建设备
    create_response = client.post("/api/v1/devices", json=test_device)
    device_id = create_response.json()["id"]
    
    # 获取设备详情
    response = client.get(f"/api/v1/devices/{device_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == device_id
    assert data["hostname"] == test_device["hostname"]

def test_update_device():
    """
    测试更新设备
    """
    # 先创建设备
    create_response = client.post("/api/v1/devices", json=test_device)
    device_id = create_response.json()["id"]
    
    # 更新设备
    update_data = {
        "hostname": "SW-TEST-001-UPDATED",
        "location": "更新后的机房",
        "status": "maintenance"
    }
    response = client.put(f"/api/v1/devices/{device_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == device_id
    assert data["hostname"] == update_data["hostname"]
    assert data["location"] == update_data["location"]
    assert data["status"] == update_data["status"]

def test_delete_device():
    """
    测试删除设备
    """
    # 先创建设备
    create_response = client.post("/api/v1/devices", json=test_device)
    device_id = create_response.json()["id"]
    
    # 删除设备
    response = client.delete(f"/api/v1/devices/{device_id}")
    assert response.status_code == 204
    
    # 验证设备是否已删除
    get_response = client.get(f"/api/v1/devices/{device_id}")
    assert get_response.status_code == 404

def test_batch_delete_devices():
    """
    测试批量删除设备
    """
    # 创建多个设备
    device_ids = []
    for i in range(3):
        device_data = test_device.copy()
        device_data["hostname"] = f"SW-TEST-{i+1}"
        device_data["ip_address"] = f"192.168.1.{101+i}"
        create_response = client.post("/api/v1/devices", json=device_data)
        device_ids.append(create_response.json()["id"])
    
    # 批量删除设备
    response = client.post("/api/v1/devices/batch/delete", json=device_ids)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["success_count"] == 3

def test_batch_update_status():
    """
    测试批量更新设备状态
    """
    # 创建多个设备
    device_ids = []
    for i in range(2):
        device_data = test_device.copy()
        device_data["hostname"] = f"SW-TEST-STATUS-{i+1}"
        device_data["ip_address"] = f"192.168.1.{110+i}"
        create_response = client.post("/api/v1/devices", json=device_data)
        device_ids.append(create_response.json()["id"])
    
    # 批量更新设备状态
    response = client.post("/api/v1/devices/batch/update-status", json=device_ids, params={"status": "offline"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["success_count"] == 2

if __name__ == "__main__":
    pytest.main(["-v", __file__])