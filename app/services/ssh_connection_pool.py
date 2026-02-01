"""
SSH连接池管理模块
提供高效的SSH连接管理功能，包括连接创建、获取、释放和回收
"""

import asyncio
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from app.models.models import Device
from app.services.netmiko_service import get_netmiko_service


class SSHConnection:
    """
    SSH连接类，封装Netmiko连接对象和连接元数据
    """
    def __init__(self, device: Device, connection: Any):
        self.device = device
        self.connection = connection
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self.is_active = True
        self.use_count = 0

    def mark_used(self):
        """标记连接为已使用"""
        self.last_used_at = datetime.now()
        self.use_count += 1

    def is_expired(self, timeout: int = 300) -> bool:
        """
        检查连接是否过期
        
        Args:
            timeout: 连接超时时间（秒）
            
        Returns:
            bool: 连接是否过期
        """
        return (datetime.now() - self.last_used_at).total_seconds() > timeout

    def close(self):
        """关闭连接"""
        if self.is_active:
            try:
                self.connection.disconnect()
                self.is_active = False
            except Exception:
                pass


class SSHConnectionPool:
    """
    SSH连接池管理类
    提供高效的SSH连接管理功能
    """
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        初始化SSH连接池
        
        Args:
            max_connections: 最大连接数
            connection_timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}
        self.lock = asyncio.Lock()
        self.netmiko_service = get_netmiko_service()
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        """定期清理过期连接"""
        while True:
            await asyncio.sleep(60)  # 每分钟清理一次
            await self._cleanup_expired_connections()

    async def _cleanup_expired_connections(self):
        """清理过期连接"""
        async with self.lock:
            for device_id, conn_list in list(self.connections.items()):
                expired_conns = [conn for conn in conn_list if conn.is_expired(self.connection_timeout)]
                for conn in expired_conns:
                    conn.close()
                    conn_list.remove(conn)
                
                # 如果设备的连接列表为空，从字典中移除
                if not conn_list:
                    del self.connections[device_id]

    async def get_connection(self, device: Device) -> Optional[SSHConnection]:
        """
        获取设备的SSH连接
        
        Args:
            device: 设备对象
            
        Returns:
            Optional[SSHConnection]: SSH连接对象，失败返回None
        """
        async with self.lock:
            # 检查是否已有可用连接
            if device.id in self.connections:
                # 查找活跃的连接
                for conn in self.connections[device.id]:
                    if conn.is_active and not conn.is_expired(self.connection_timeout):
                        conn.mark_used()
                        return conn

            # 如果没有可用连接，且连接数未达到上限，创建新连接
            current_connections = len(self.connections.get(device.id, []))
            if current_connections < self.max_connections:
                try:
                    # 创建新连接
                    connection = await self.netmiko_service.connect_to_device(device)
                    if connection:
                        ssh_conn = SSHConnection(device, connection)
                        ssh_conn.mark_used()
                        
                        # 添加到连接池
                        if device.id not in self.connections:
                            self.connections[device.id] = []
                        self.connections[device.id].append(ssh_conn)
                        
                        return ssh_conn
                except Exception:
                    pass
        
        return None

    async def release_connection(self, connection: SSHConnection):
        """
        释放连接回连接池
        
        Args:
            connection: 要释放的连接
        """
        # 连接不需要显式释放，只需要标记为已使用
        connection.mark_used()

    async def close_connection(self, connection: SSHConnection):
        """
        关闭并移除连接
        
        Args:
            connection: 要关闭的连接
        """
        async with self.lock:
            connection.close()
            if connection.device.id in self.connections:
                if connection in self.connections[connection.device.id]:
                    self.connections[connection.device.id].remove(connection)
                
                # 如果设备的连接列表为空，从字典中移除
                if not self.connections[connection.device.id]:
                    del self.connections[connection.device.id]

    async def close_all_connections(self):
        """
        关闭所有连接
        """
        async with self.lock:
            for conn_list in self.connections.values():
                for conn in conn_list:
                    conn.close()
            self.connections.clear()
        
        # 取消清理任务
        self.cleanup_task.cancel()

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息
        
        Returns:
            Dict[str, Any]: 连接池统计信息
        """
        stats = {
            "total_devices": len(self.connections),
            "total_connections": sum(len(conns) for conns in self.connections.values()),
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "device_stats": {}
        }
        
        for device_id, conn_list in self.connections.items():
            stats["device_stats"][device_id] = {
                "active_connections": len([conn for conn in conn_list if conn.is_active]),
                "total_connections": len(conn_list),
                "avg_use_count": sum(conn.use_count for conn in conn_list) / len(conn_list) if conn_list else 0
            }
        
        return stats


# 创建全局SSH连接池实例
ssh_connection_pool = SSHConnectionPool()


def get_ssh_connection_pool() -> SSHConnectionPool:
    """
    获取SSH连接池实例
    
    Returns:
        SSHConnectionPool: SSH连接池实例
    """
    return ssh_connection_pool
