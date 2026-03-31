"""
SSHConnectionPool 懒初始化测试

测试目的：验证模块导入时不抛异常，懒初始化正常工作

问题分析：
- 当前代码在 __init__ 中直接创建 asyncio.Lock() 和 asyncio.create_task()
- 模块导入时没有事件循环会导致 RuntimeError: no running event loop

修复方案：
- 使用懒初始化模式，延迟创建 asyncio 对象
- 在 _ensure_initialized() 方法中检查并初始化
- 所有使用 _lock 和 _cleanup_task 的方法都需要调用 _ensure_initialized()

测试用例：
1. 模块导入不应抛异常
2. 初始化前 _lock 应为 None
3. 初始化前 _cleanup_task 应为 None
4. 初始化前 _initialized 应为 False
5. 首次调用方法后触发初始化
6. 初始化后 _lock 应已创建
7. 初始化后 _cleanup_task 应已创建
8. 初始化后 _initialized 应为 True
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestSSHConnectionPoolLazyInitialization:
    """测试 SSH 连接池懒初始化"""

    def test_module_import_no_exception(self):
        """
        测试模块导入时不抛异常

        验证点：
        - 导入 ssh_connection_pool 模块不应该抛出 RuntimeError
        - 当前代码在 __init__ 中直接调用 asyncio.create_task()，会导致错误
        """
        # 这一行应该在修复前抛出 RuntimeError: no running event loop
        # 修复后应该正常导入
        from app.services.ssh_connection_pool import ssh_connection_pool

        # 验证导入成功
        assert ssh_connection_pool is not None

    def test_lazy_init_lock_none_before_init(self):
        """
        测试初始化前 _lock 应为 None

        验证点：
        - 模块导入后 _lock 应该尚未创建（None）
        - 当前代码在 __init__ 中直接创建 Lock，会导致错误
        """
        from app.services.ssh_connection_pool import ssh_connection_pool

        # 修复后应该返回 None（未初始化）
        # 修复前可能返回一个 Lock 对象或抛异常
        assert ssh_connection_pool._lock is None

    def test_lazy_init_cleanup_task_none_before_init(self):
        """
        测试初始化前 _cleanup_task 应为 None

        验证点：
        - 模块导入后 _cleanup_task 应该尚未创建（None）
        - 当前代码在 __init__ 中直接创建 task，会导致错误
        """
        from app.services.ssh_connection_pool import ssh_connection_pool

        # 修复后应该返回 None（未初始化）
        # 修复前可能抛异常
        assert ssh_connection_pool._cleanup_task is None

    def test_lazy_init_initialized_false_before_init(self):
        """
        测试初始化前 _initialized 应为 False

        验证点：
        - 模块导入后 _initialized 应为 False
        - 表示尚未初始化 asyncio 对象
        """
        from app.services.ssh_connection_pool import ssh_connection_pool

        # 修复后应该返回 False（未初始化）
        assert ssh_connection_pool._initialized is False

    @pytest.mark.asyncio
    async def test_ensure_initialized_called_on_get_connection(self):
        """
        测试 get_connection 调用 _ensure_initialized

        验证点：
        - get_connection 应该调用 _ensure_initialized()
        - 调用后 _initialized 应为 True
        - 调用后 _lock 应已创建
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        # 创建新的连接池实例（不使用全局实例）
        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._initialized is False
        assert pool._lock is None

        # Mock device 和 netmiko_service
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-switch"

        # Mock netmiko_service.connect_to_device
        with patch.object(pool, 'netmiko_service') as mock_netmiko:
            mock_netmiko.connect_to_device = AsyncMock(return_value=MagicMock())

            # 调用 get_connection 触发初始化
            await pool.get_connection(mock_device)

            # 验证初始化状态
            assert pool._initialized is True
            assert pool._lock is not None
            assert isinstance(pool._lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_ensure_initialized_called_on_cleanup_expired_connections(self):
        """
        测试 _cleanup_expired_connections 调用 _ensure_initialized

        验证点：
        - _cleanup_expired_connections 应该调用 _ensure_initialized()
        - 因为它使用 self._lock
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._initialized is False

        # 调用清理方法触发初始化
        await pool._cleanup_expired_connections()

        # 验证初始化状态
        assert pool._initialized is True
        assert pool._lock is not None

    @pytest.mark.asyncio
    async def test_ensure_initialized_called_on_close_connection(self):
        """
        测试 close_connection 调用 _ensure_initialized

        验证点：
        - close_connection 应该调用 _ensure_initialized()
        - 因为它使用 self._lock
        """
        from app.services.ssh_connection_pool import SSHConnectionPool, SSHConnection

        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._initialized is False

        # Mock SSHConnection
        mock_conn = MagicMock(spec=SSHConnection)
        mock_conn.device = MagicMock()
        mock_conn.device.id = 1
        mock_conn.is_active = True
        mock_conn.close = MagicMock()

        # 调用关闭连接方法触发初始化
        await pool.close_connection(mock_conn)

        # 验证初始化状态
        assert pool._initialized is True
        assert pool._lock is not None

    @pytest.mark.asyncio
    async def test_ensure_initialized_called_on_close_all_connections(self):
        """
        测试 close_all_connections 调用 _ensure_initialized

        验证点：
        - close_all_connections 应该调用 _ensure_initialized()
        - 因为它使用 self._lock 和 self._cleanup_task
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._initialized is False
        assert pool._cleanup_task is None

        # 调用关闭所有连接方法触发初始化
        await pool.close_all_connections()

        # 验证初始化状态
        assert pool._initialized is True
        assert pool._lock is not None


class TestSSHConnectionPoolEnsureInitializedMethod:
    """测试 _ensure_initialized 方法"""

    def test_ensure_initialized_method_exists(self):
        """
        测试 _ensure_initialized 方法是否存在

        验证点：
        - SSHConnectionPool 类应该有 _ensure_initialized 方法
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 检查方法是否存在
        assert hasattr(pool, '_ensure_initialized')
        assert callable(pool._ensure_initialized)

    @pytest.mark.asyncio
    async def test_ensure_initialized_creates_lock(self):
        """
        测试 _ensure_initialized 创建 Lock

        验证点：
        - 调用 _ensure_initialized 后，_lock 应为 asyncio.Lock 实例
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._lock is None

        # 调用初始化方法
        pool._ensure_initialized()

        # 验证 Lock 已创建
        assert pool._lock is not None
        assert isinstance(pool._lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_ensure_initialized_creates_cleanup_task(self):
        """
        测试 _ensure_initialized 创建清理任务

        验证点：
        - 调用 _ensure_initialized 后，_cleanup_task 应为 asyncio.Task 实例
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 验证初始状态
        assert pool._cleanup_task is None

        # 调用初始化方法
        pool._ensure_initialized()

        # 验证 Task 已创建
        assert pool._cleanup_task is not None
        assert isinstance(pool._cleanup_task, asyncio.Task)

    @pytest.mark.asyncio
    async def test_ensure_initialized_idempotent(self):
        """
        测试 _ensure_initialized 多次调用是幂等的

        验证点：
        - 多次调用 _ensure_initialized 不应该重复创建对象
        - _initialized 标志位应该正确控制

        注意：需要在异步上下文中调用，因为 _ensure_initialized 会创建 asyncio.Task
        """
        from app.services.ssh_connection_pool import SSHConnectionPool

        pool = SSHConnectionPool()

        # 第一次调用（在异步上下文中）
        pool._ensure_initialized()
        first_lock = pool._lock
        first_initialized = pool._initialized

        # 第二次调用
        pool._ensure_initialized()
        second_lock = pool._lock
        second_initialized = pool._initialized

        # 验证幂等性
        assert first_lock == second_lock  # 同一个 Lock 对象
        assert first_initialized == second_initialized == True


class TestSSHConnectionCloseLogsException:
    """测试 SSHConnection.close() 异常时记录日志（I4 修复验证）"""

    def test_ssh_connection_close_logs_exception(self):
        """
        验证 SSHConnection.close() 异常时记录日志

        测试步骤：
        1. Mock connection.disconnect() 抛出异常
        2. 调用 close()
        3. 验证 logger.warning 被调用
        4. 验证 is_active 设置为 False
        """
        from app.services.ssh_connection_pool import SSHConnection

        device = MagicMock(hostname="test-device")
        connection = MagicMock()
        connection.disconnect.side_effect = Exception("Connection error")

        ssh_conn = SSHConnection(device, connection)

        with patch('app.services.ssh_connection_pool.logger') as mock_logger:
            ssh_conn.close()

            # 验证日志被记录
            assert mock_logger.warning.called, "logger.warning 应被调用"
            call_args = mock_logger.warning.call_args[0][0]
            assert "test-device" in call_args, "日志应包含设备名称"

            # 验证 is_active 为 False
            assert ssh_conn.is_active is False, "is_active 应设置为 False"

    def test_ssh_connection_close_success_no_warning(self):
        """
        验证 SSHConnection.close() 成功时不记录警告日志
        """
        from app.services.ssh_connection_pool import SSHConnection

        device = MagicMock(hostname="test-device")
        connection = MagicMock()
        # disconnect 成功

        ssh_conn = SSHConnection(device, connection)

        with patch('app.services.ssh_connection_pool.logger') as mock_logger:
            ssh_conn.close()

            # 验证 warning 不被调用
            assert not mock_logger.warning.called, "成功关闭不应记录 warning"

            # 验证 is_active 为 False
            assert ssh_conn.is_active is False, "is_active 应设置为 False"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])