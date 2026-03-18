"""
WebSocket连接管理器单元测试

测试范围:
- 连接注册/注销
- 消息广播
- 延迟更新广播
"""
import pytest
from unittest.mock import AsyncMock
from app.websocket.manager import ConnectionManager


@pytest.fixture
def manager():
    """创建连接管理器实例"""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """创建模拟WebSocket连接"""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestConnectionManager:
    """ConnectionManager 测试类"""
    
    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """测试连接注册"""
        await manager.connect(mock_websocket)
        
        assert len(manager.active_connections) == 1
        assert mock_websocket in manager.active_connections
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """测试连接注销"""
        await manager.connect(mock_websocket)
        await manager.disconnect(mock_websocket)
        
        assert len(manager.active_connections) == 0
        assert mock_websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager, mock_websocket):
        """测试发送个人消息"""
        await manager.connect(mock_websocket)
        
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, mock_websocket)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_all_connections(self, manager):
        """测试广播消息到所有连接"""
        mock_ws1 = AsyncMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)
        
        message = {"type": "broadcast", "data": "test"}
        await manager.broadcast(message)
        
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_latency_update(self, manager, mock_websocket):
        """测试延迟更新广播"""
        await manager.connect(mock_websocket)
        
        await manager.broadcast_latency_update(
            device_id=1,
            latency=25,
            last_check="2026-03-16T10:30:00",
            status="active"
        )
        
        # 验证发送的消息格式
        call_args = mock_websocket.send_json.call_args
        message = call_args[0][0]
        
        assert message["type"] == "latency_update"
        assert message["data"]["device_id"] == 1
        assert message["data"]["latency"] == 25
        assert message["data"]["last_latency_check"] == "2026-03-16T10:30:00"
        assert message["data"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_broadcast_handles_disconnected_client(self, manager):
        """测试广播时处理断开的客户端"""
        mock_ws_good = AsyncMock()
        mock_ws_good.accept = AsyncMock()
        mock_ws_good.send_json = AsyncMock()
        
        mock_ws_bad = AsyncMock()
        mock_ws_bad.accept = AsyncMock()
        mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Connection lost"))
        
        await manager.connect(mock_ws_good)
        await manager.connect(mock_ws_bad)
        
        message = {"type": "test"}
        await manager.broadcast(message)
        
        # 好的连接应该收到消息
        mock_ws_good.send_json.assert_called_once()
        # 坏的连接应该被移除
        assert mock_ws_bad not in manager.active_connections
    
    def test_get_connection_count(self, manager, mock_websocket):
        """测试获取连接数"""
        assert manager.get_connection_count() == 0
        
        # 手动添加连接（同步测试）
        manager.active_connections.append(mock_websocket)
        assert manager.get_connection_count() == 1
