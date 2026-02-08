"""
测试 /devices/all API 端点
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Base, get_db

# 使用内存数据库进行测试
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """测试数据库fixture，每个测试函数后清理数据"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """测试客户端fixture，使用测试数据库"""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_get_all_devices_returns_all_without_pagination(client, test_db):
    """测试获取所有设备不包含分页参数，使用默认limit=100"""
    # 创建设备数据（超过默认分页大小）
    for i in range(15):
        response = client.post("/api/v1/devices/", json={
            "hostname": f"Switch-{i}",
            "ip_address": f"192.168.1.{i+10}",
            "vendor": "Cisco",
            "device_type": "switch"
        })
        assert response.status_code == 201
    
    # 调用新API
    response = client.get("/api/v1/devices/all")
    
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["total"] >= 15
    assert len(data["devices"]) >= 15
    assert data["limit"] == 100  # 验证默认limit

def test_get_all_devices_with_limit(client, test_db):
    """测试带limit参数的设备获取"""
    # 创建设备数据
    for i in range(20):
        client.post("/api/v1/devices/", json={
            "hostname": f"Limit-Switch-{i}",
            "ip_address": f"192.168.2.{i+10}",
            "vendor": "Huawei",
            "device_type": "switch"
        })
    
    response = client.get("/api/v1/devices/all?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["devices"]) == 10
    assert data["total"] >= 20
    assert data["limit"] == 10

def test_get_all_devices_with_offset(client, test_db):
    """测试带offset参数的分页功能"""
    # 创建设备数据
    for i in range(20):
        client.post("/api/v1/devices/", json={
            "hostname": f"Offset-Switch-{i}",
            "ip_address": f"192.168.3.{i+10}",
            "vendor": "Cisco",
            "device_type": "switch"
        })
    
    # 获取第一页
    response1 = client.get("/api/v1/devices/all?limit=5&offset=0")
    data1 = response1.json()
    
    # 获取第二页
    response2 = client.get("/api/v1/devices/all?limit=5&offset=5")
    data2 = response2.json()
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert len(data1["devices"]) == 5
    assert len(data2["devices"]) == 5
    assert data1["offset"] == 0
    assert data2["offset"] == 5

def test_get_all_devices_filter_by_status(client, test_db):
    """测试按状态筛选设备"""
    # 创建不同状态的设备
    client.post("/api/v1/devices/", json={
        "hostname": "Online-Switch",
        "ip_address": "192.168.4.1",
        "status": "active",
        "device_type": "switch"
    })
    client.post("/api/v1/devices/", json={
        "hostname": "Offline-Switch",
        "ip_address": "192.168.4.2",
        "status": "offline",
        "device_type": "switch"
    })
    client.post("/api/v1/devices/", json={
        "hostname": "Online-Switch-2",
        "ip_address": "192.168.4.3",
        "status": "active",
        "device_type": "switch"
    })
    
    response = client.get("/api/v1/devices/all?status=active")
    
    assert response.status_code == 200
    data = response.json()
    assert all(d["status"] == "active" for d in data["devices"])

def test_get_all_devices_filter_by_vendor(client, test_db):
    """测试按厂商筛选设备"""
    # 创建不同厂商的设备
    client.post("/api/v1/devices/", json={
        "hostname": "Cisco-Switch",
        "ip_address": "192.168.5.1",
        "vendor": "Cisco",
        "device_type": "switch"
    })
    client.post("/api/v1/devices/", json={
        "hostname": "Huawei-Switch",
        "ip_address": "192.168.5.2",
        "vendor": "Huawei",
        "device_type": "switch"
    })
    client.post("/api/v1/devices/", json={
        "hostname": "Cisco-Switch-2",
        "ip_address": "192.168.5.3",
        "vendor": "Cisco",
        "device_type": "switch"
    })
    
    response = client.get("/api/v1/devices/all?vendor=Cisco")
    
    assert response.status_code == 200
    data = response.json()
    assert all(d["vendor"] == "Cisco" for d in data["devices"])

def test_get_all_devices_limit_validation(client, test_db):
    """测试limit参数验证"""
    # 测试limit超过最大值
    response = client.get("/api/v1/devices/all?limit=6000")
    assert response.status_code == 422  # 验证错误
    
    # 测试limit小于最小值
    response = client.get("/api/v1/devices/all?limit=0")
    assert response.status_code == 422  # 验证错误
