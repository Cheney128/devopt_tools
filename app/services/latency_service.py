"""
延迟检测服务
提供设备网络延迟检测功能
"""
import socket
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import Device
from app.websocket import manager


class LatencyService:
    """
    设备延迟检测服务
    
    通过TCP连接测试检测设备的网络延迟
    """
    
    MAX_LATENCY = 999
    
    def __init__(
        self, 
        timeout: int = 5,
        retry_count: int = 2
    ):
        """
        初始化延迟检测服务
        
        Args:
            timeout: 单次检测超时时间（秒）
            retry_count: 失败重试次数
        """
        self.timeout = timeout
        self.retry_count = retry_count
    
    def check_device_latency_sync(
        self, 
        device: Device, 
        db: Session
    ) -> Dict[str, Any]:
        """
        同步检测单个设备延迟
        
        Args:
            device: 设备对象
            db: 数据库会话
            
        Returns:
            检测结果字典
        """
        result = {
            "device_id": device.id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "port": device.login_port,
            "latency": None,
            "success": False,
            "error": None,
            "checked_at": datetime.now()
        }
        
        try:
            latency = self._tcp_connect_test(
                device.ip_address, 
                device.login_port
            )
            
            result["latency"] = latency
            result["success"] = latency < self.MAX_LATENCY
            
            self._update_device_latency(db, device, latency, result["success"])
            
        except Exception as e:
            result["latency"] = self.MAX_LATENCY
            result["error"] = str(e)
            self._update_device_latency(db, device, self.MAX_LATENCY, False)
        
        return result
    
    def _tcp_connect_test(
        self, 
        ip_address: str, 
        port: int
    ) -> int:
        """
        TCP连接测试
        
        Args:
            ip_address: IP地址
            port: 端口号
            
        Returns:
            延迟时间(ms)
        """
        last_error = None
        
        for attempt in range(self.retry_count + 1):
            try:
                start_time = time.time()
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                sock.connect((ip_address, port))
                
                end_time = time.time()
                latency = int((end_time - start_time) * 1000)
                
                sock.close()
                
                return latency
                
            except socket.timeout:
                last_error = "Connection timeout"
            except socket.error as e:
                last_error = f"Socket error: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
        
        return self.MAX_LATENCY
    
    def _update_device_latency(
        self, 
        db: Session, 
        device: Device, 
        latency: int, 
        success: bool
    ):
        """
        更新设备延迟和状态，并广播WebSocket消息
        
        Args:
            db: 数据库会话
            device: 设备对象
            latency: 延迟时间
            success: 是否成功
        """
        device.latency = latency
        device.last_latency_check = datetime.now()
        
        if success:
            if device.status == "offline":
                device.status = "active"
        else:
            if device.status != "maintenance":
                device.status = "offline"
        
        db.commit()
        db.refresh(device)
        
        self._broadcast_latency_update(device, latency)
    
    def _broadcast_latency_update(self, device: Device, latency: int):
        """
        广播延迟更新到WebSocket客户端
        
        Args:
            device: 设备对象
            latency: 延迟时间
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    manager.broadcast_latency_update(
                        device_id=device.id,
                        latency=latency,
                        last_check=device.last_latency_check.isoformat(),
                        status=device.status
                    )
                )
        except RuntimeError:
            pass
    
    def check_devices_batch(
        self, 
        devices: List[Device], 
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        批量检测设备延迟
        
        Args:
            devices: 设备列表
            db: 数据库会话
            
        Returns:
            检测结果列表
        """
        results = []
        
        for device in devices:
            result = self.check_device_latency_sync(device, db)
            results.append(result)
        
        return results
    
    def check_all_enabled_devices(
        self, 
        db: Session,
        exclude_statuses: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检测所有启用延迟检测的设备
        
        Args:
            db: 数据库会话
            exclude_statuses: 排除的状态列表
            
        Returns:
            检测结果列表
        """
        if exclude_statuses is None:
            exclude_statuses = ["maintenance"]
        
        query = db.query(Device).filter(
            Device.latency_check_enabled == True
        )
        
        if exclude_statuses:
            query = query.filter(Device.status.notin_(exclude_statuses))
        
        devices = query.all()
        
        return self.check_devices_batch(devices, db)


latency_service = LatencyService()
