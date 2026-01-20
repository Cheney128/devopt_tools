"""
Oxidized集成服务
"""
import httpx
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List

from app.config import settings
from app.models.models import Device, Configuration


class OxidizedService:
    """
    Oxidized集成服务类
    """
    
    def __init__(self):
        """
        初始化Oxidized服务
        """
        self.oxidized_url = settings.OXIDIZED_URL
        self.client = httpx.AsyncClient(base_url=self.oxidized_url, timeout=30.0)
    
    async def get_device_config(self, device_id: int, db: Session) -> Optional[str]:
        """
        从Oxidized获取设备配置
        
        Args:
            device_id: 设备ID
            db: 数据库会话
            
        Returns:
            设备配置内容
        """
        # 获取设备信息
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return None
        
        try:
            # 从Oxidized API获取配置
            response = await self.client.get(f"/node/fetch/{device.hostname}")
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            print(f"Error fetching config from Oxidized: {e}")
            return None
    
    async def sync_with_oxidized(self, db: Session) -> Dict[str, Any]:
        """
        与Oxidized同步设备信息
        
        Args:
            db: 数据库会话
            
        Returns:
            同步结果
        """
        try:
            # 获取Oxidized中的设备列表
            response = await self.client.get("/nodes")
            if response.status_code != 200:
                return {"success": False, "message": "Failed to get nodes from Oxidized"}
            
            oxidized_nodes = response.json()
            synced_count = 0
            
            for node in oxidized_nodes:
                # 检查设备是否已存在
                existing_device = db.query(Device).filter(
                    (Device.hostname == node.get("name")) | 
                    (Device.ip_address == node.get("ip"))
                ).first()
                
                if not existing_device:
                    # 创建设备
                    new_device = Device(
                        hostname=node.get("name"),
                        ip_address=node.get("ip", ""),
                        vendor=node.get("model", ""),
                        model=node.get("model", ""),
                        status="active"
                    )
                    db.add(new_device)
                    synced_count += 1
            
            db.commit()
            return {"success": True, "message": f"Synced {synced_count} devices from Oxidized"}
        except Exception as e:
            print(f"Error syncing with Oxidized: {e}")
            return {"success": False, "message": str(e)}
    
    async def get_oxidized_status(self) -> Dict[str, Any]:
        """
        获取Oxidized服务状态
        
        Returns:
            Oxidized服务状态
        """
        try:
            response = await self.client.get("/status")
            if response.status_code == 200:
                return {"success": True, "status": response.json()}
            return {"success": False, "message": "Failed to get Oxidized status"}
        except Exception as e:
            print(f"Error getting Oxidized status: {e}")
            return {"success": False, "message": str(e)}
    
    async def close(self):
        """
        关闭HTTP客户端
        """
        await self.client.aclose()


# 创建Oxidized服务实例
oxidized_service = OxidizedService()


async def get_oxidized_service() -> OxidizedService:
    """
    获取Oxidized服务实例
    
    Returns:
        Oxidized服务实例
    """
    return oxidized_service