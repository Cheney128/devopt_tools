"""
WebSocket API端点
提供实时通信能力
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket import manager
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/latency")
async def websocket_latency_endpoint(websocket: WebSocket):
    """
    延迟检测实时更新WebSocket端点
    
    连接后，客户端将实时接收延迟检测更新消息
    
    消息格式:
    {
        "type": "latency_update",
        "data": {
            "device_id": 1,
            "latency": 25,
            "last_latency_check": "2026-03-16T10:30:00",
            "status": "active"
        },
        "timestamp": "2026-03-16T10:30:00.123456"
    }
    """
    await manager.connect(websocket)
    
    try:
        await manager.send_personal_message(
            {"type": "connected", "message": "WebSocket connected successfully"},
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        {"type": "pong", "timestamp": datetime.now().isoformat()},
                        websocket
                    )
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


@router.get("/status")
async def get_websocket_status():
    """
    获取WebSocket服务状态
    
    Returns:
        当前连接数等信息
    """
    return {
        "active_connections": manager.get_connection_count(),
        "status": "running"
    }
