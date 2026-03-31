"""
SSH连接池管理模块
提供高效的SSH连接管理功能，包括连接创建、获取、释放和回收

修复说明：
- 使用懒初始化模式，避免模块导入时创建 asyncio 对象
- 在 __init__ 中不调用 asyncio.Lock() 和 asyncio.create_task()
- 在 _ensure_initialized() 方法中延迟创建这些对象
- 所有使用 _lock 和 _cleanup_task 的方法都需要调用 _ensure_initialized()
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from app.models.models import Device
from app.services.netmiko_service import get_netmiko_service

# 配置日志
logger = logging.getLogger(__name__)


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
            except Exception as e:
                logger.warning(f"Failed to close SSH connection for device {self.device.hostname}: {e}")
                # 连接关闭失败时仍标记为非活跃，避免重复尝试
                self.is_active = False


class SSHConnectionPool:
    """
    SSH连接池管理类
    提供高效的SSH连接管理功能

    使用懒初始化模式：
    - __init__ 中不创建 asyncio 对象（Lock、Task）
    - _ensure_initialized() 中延迟创建
    - 所有使用 asyncio 对象的方法调用 _ensure_initialized()
    """

    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        初始化SSH连接池（懒初始化模式）

        Args:
            max_connections: 最大连接数
            connection_timeout: 连接超时时间（秒）

        注意：
            不在 __init__ 中创建 asyncio.Lock() 和 asyncio.create_task()
            因为模块导入时可能没有运行的事件循环
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}

        # 懒初始化属性：延迟创建 asyncio 对象
        self._lock: Optional[asyncio.Lock] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._initialized: bool = False

        # 非 asyncio 对象可以在 __init__ 中创建
        self.netmiko_service = get_netmiko_service()

        logger.debug("SSHConnectionPool instance created (lazy initialization)")

    def _ensure_initialized(self):
        """
        确保 asyncio 对象已初始化

        在首次使用 _lock 或 _cleanup_task 时调用此方法
        必须在有运行事件循环的环境中调用

        此方法会：
        1. 创建 asyncio.Lock
        2. 创建定期清理任务 asyncio.Task
        3. 设置 _initialized 标志为 True

        Raises:
            RuntimeError: 如果在没有运行事件循环的环境中调用，
                          asyncio.Lock() 和 asyncio.create_task() 会抛出此异常
        """
        if self._initialized:
            return

        logger.info("Initializing SSH connection pool asyncio objects")
        self._lock = asyncio.Lock()
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self._initialized = True
        logger.info("SSH connection pool initialized successfully")

    async def _periodic_cleanup(self):
        """
        定期清理过期连接

        每分钟执行一次清理，检查所有连接是否过期
        """
        while True:
            await asyncio.sleep(60)  # 每分钟清理一次
            try:
                await self._cleanup_expired_connections()
            except Exception as e:
                logger.error(f"Periodic cleanup error: {e}")

    async def _cleanup_expired_connections(self):
        """
        清理过期连接

        检查所有连接是否过期，关闭并移除过期连接
        """
        # 调用 _ensure_initialized 确保 _lock 已创建
        self._ensure_initialized()

        async with self._lock:
            for device_id, conn_list in list(self.connections.items()):
                expired_conns = [conn for conn in conn_list if conn.is_expired(self.connection_timeout)]
                for conn in expired_conns:
                    conn.close()
                    conn_list.remove(conn)
                    logger.debug(f"Closed expired connection for device {device_id}")

                # 如果设备的连接列表为空，从字典中移除
                if not conn_list:
                    del self.connections[device_id]
                    logger.debug(f"Removed empty connection list for device {device_id}")

    async def get_connection(self, device: Device) -> Optional[SSHConnection]:
        """
        获取设备的SSH连接

        Args:
            device: 设备对象

        Returns:
            Optional[SSHConnection]: SSH连接对象，失败返回None
        """
        # 调用 _ensure_initialized 确保 _lock 已创建
        self._ensure_initialized()

        async with self._lock:
            # 检查是否已有可用连接
            if device.id in self.connections:
                # 查找活跃的连接
                for conn in self.connections[device.id]:
                    if conn.is_active and not conn.is_expired(self.connection_timeout):
                        conn.mark_used()
                        logger.debug(f"Reusing existing connection for device {device.hostname}")
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

                        logger.info(f"Created new connection for device {device.hostname}")
                        return ssh_conn
                except Exception as e:
                    logger.error(f"Failed to create connection for device {device.hostname}: {e}")

        return None

    async def release_connection(self, connection: SSHConnection):
        """
        释放连接回连接池

        Args:
            connection: 要释放的连接
        """
        # 连接不需要显式释放，只需要标记为已使用
        connection.mark_used()
        logger.debug(f"Released connection for device {connection.device.hostname}")

    async def close_connection(self, connection: SSHConnection):
        """
        关闭并移除连接

        Args:
            connection: 要关闭的连接
        """
        # 调用 _ensure_initialized 确保 _lock 已创建
        self._ensure_initialized()

        async with self._lock:
            connection.close()
            if connection.device.id in self.connections:
                if connection in self.connections[connection.device.id]:
                    self.connections[connection.device.id].remove(connection)
                    logger.info(f"Closed connection for device {connection.device.hostname}")

                # 如果设备的连接列表为空，从字典中移除
                if not self.connections[connection.device.id]:
                    del self.connections[connection.device.id]
                    logger.debug(f"Removed empty connection list for device {connection.device.id}")

    async def close_all_connections(self):
        """
        关闭所有连接

        清理所有活跃连接，取消清理任务
        """
        # 调用 _ensure_initialized 确保 _lock 和 _cleanup_task 已创建
        self._ensure_initialized()

        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Cleanup task cancelled")

        async with self._lock:
            for conn_list in self.connections.values():
                for conn in conn_list:
                    conn.close()
            self.connections.clear()
            logger.info("All connections closed")

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
