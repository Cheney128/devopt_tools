"""
配置管理单元测试
"""
import pytest
from unittest.mock import Mock, patch
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

def test_get_configurations():
    """
    测试获取配置列表
    """
    response = client.get("/api/v1/configurations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
