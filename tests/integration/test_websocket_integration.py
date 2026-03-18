"""
WebSocket集成测试

测试范围:
- WebSocket端点连接
- 延迟检测触发广播
- 多客户端连接
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.websocket import manager
import json


class TestWebSocketIntegration:
    """WebSocket集成测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_websocket_endpoint_connection(self, client):
        """测试WebSocket端点连接"""
        with client.websocket_connect("/api/v1/ws/latency") as websocket:
            message = websocket.receive_json()
            
            assert message["type"] == "connected"
            assert "message" in message
    
    def test_websocket_heartbeat(self, client):
        """测试WebSocket心跳"""
        with client.websocket_connect("/api/v1/ws/latency") as websocket:
            websocket.receive_json()
            
            websocket.send_json({"type": "ping"})
            
            response = websocket.receive_json()
            
            assert response["type"] == "pong"
            assert "timestamp" in response
    
    def test_multiple_clients_receive_broadcast(self, client):
        """测试多客户端接收广播"""
        with client.websocket_connect("/api/v1/ws/latency") as ws1:
            with client.websocket_connect("/api/v1/ws/latency") as ws2:
                ws1.receive_json()
                ws2.receive_json()
                
                import asyncio
                asyncio.run(manager.broadcast_latency_update(
                    device_id=1,
                    latency=25,
                    last_check="2026-03-16T10:30:00",
                    status="active"
                ))
                
                msg1 = ws1.receive_json()
                msg2 = ws2.receive_json()
                
                assert msg1["type"] == "latency_update"
                assert msg2["type"] == "latency_update"
                assert msg1["data"]["device_id"] == 1
    
    def test_get_websocket_status(self, client):
        """测试获取WebSocket状态端点"""
        response = client.get("/api/v1/ws/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "status" in data
