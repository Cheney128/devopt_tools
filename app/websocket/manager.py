"""
WebSocket连接管理器
管理所有活跃的WebSocket连接，支持广播消息
"""
from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket连接管理器
    
    管理所有活跃的WebSocket连接，支持：
    - 连接注册/注销
    - 广播消息到所有连接
    - 发送消息到特定连接
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """
        接受新的WebSocket连接
        
        Args:
            websocket: WebSocket连接对象
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """
        断开WebSocket连接
        
        Args:
            websocket: 要断开的WebSocket连接
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        发送消息到特定连接
        
        Args:
            message: 消息内容（字典）
            websocket: 目标WebSocket连接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        广播消息到所有连接
        
        Args:
            message: 消息内容（字典）
        """
        if not self.active_connections:
            return
        
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            await self.disconnect(connection)
    
    async def broadcast_latency_update(self, device_id: int, latency: int, 
                                        last_check: str, status: str):
        """
        广播延迟更新消息
        
        Args:
            device_id: 设备ID
            latency: 延迟值（毫秒）
            last_check: 最后检测时间（ISO格式）
            status: 设备状态
        """
        message = {
            "type": "latency_update",
            "data": {
                "device_id": device_id,
                "latency": latency,
                "last_latency_check": last_check,
                "status": status
            },
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    def get_connection_count(self) -> int:
        """
        获取当前连接数
        
        Returns:
            活跃连接数
        """
        return len(self.active_connections)


manager = ConnectionManager()
