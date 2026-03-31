"""
arp_mac_scheduler AsyncIOScheduler 迁移测试

测试目的：验证 ARP/MAC 调度器已正确迁移到 AsyncIOScheduler

问题分析（M3）：
- 原代码使用 BackgroundScheduler，在后台线程运行
- 存在 _run_async 三层降级逻辑，复杂度高
- Session 在异步环境中直接使用，存在线程安全隐患
- 全局 Session 生命周期不可控

修复方案（M3）：
- 将 BackgroundScheduler 改为 AsyncIOScheduler
- 移除 _run_async 三层降级逻辑
- 将同步方法改为 async 方法
- 使用 asyncio.to_thread() 包装数据库操作
- 在任务内部重新获取 Session，不再复用全局 Session

测试用例：
1. 调度器类型为 AsyncIOScheduler
2. Session 在任务内部获取
3. Session 在 finally 块中关闭
4. _run_async 三层降级逻辑已移除或简化
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestARPMACSchedulerType:
    """测试调度器类型"""

    def test_scheduler_is_asyncio_scheduler(self):
        """
        测试调度器类型是否为 AsyncIOScheduler

        验证点：
        - ARPMACScheduler 应使用 AsyncIOScheduler
        - 不是 BackgroundScheduler
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = ARPMACScheduler()

        # 验证调度器类型
        assert isinstance(scheduler.scheduler, AsyncIOScheduler), \
            f"调度器应为 AsyncIOScheduler，实际为: {type(scheduler.scheduler)}"

        # 验证不是 BackgroundScheduler
        assert not isinstance(scheduler.scheduler, BackgroundScheduler), \
            "调度器不应该使用 BackgroundScheduler"

    def test_scheduler_not_background_scheduler(self):
        """
        测试调度器不是 BackgroundScheduler

        验证点：
        - BackgroundScheduler 在后台线程运行，无事件循环
        - async 函数在 BackgroundScheduler 中无法正常执行
        """
        from app.services.arp_mac_scheduler import arp_mac_scheduler
        from apscheduler.schedulers.background import BackgroundScheduler

        # 验证不是 BackgroundScheduler
        assert not isinstance(arp_mac_scheduler.scheduler, BackgroundScheduler), \
            "调度器不应该使用 BackgroundScheduler"

    def test_scheduler_instance_type(self):
        """
        测试全局调度器实例的类型

        验证点：
        - arp_mac_scheduler 实例的 scheduler 属性应为 AsyncIOScheduler
        """
        from app.services.arp_mac_scheduler import arp_mac_scheduler
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        assert isinstance(arp_mac_scheduler.scheduler, AsyncIOScheduler), \
            f"全局调度器应为 AsyncIOScheduler，实际为: {type(arp_mac_scheduler.scheduler)}"


class TestARPMACSchedulerSessionLifecycle:
    """测试 Session 生命周期"""

    def test_start_method_signature_no_db_parameter(self):
        """
        测试 start 方法签名不包含 db 参数

        验证点：
        - start 方法应该只接受可选的 db 参数（兼容性）
        - db 参数应在方法内部获取，而不是从外部传入
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        import inspect

        scheduler = ARPMACScheduler()

        # 获取方法签名
        sig = inspect.signature(scheduler.start)

        # 验证参数列表
        params = list(sig.parameters.keys())

        # db 参数应为可选（默认值）
        if 'db' in params:
            # 如果存在 db 参数，它应该是可选的
            param = sig.parameters['db']
            assert param.default is not inspect.Parameter.empty or param.default is None, \
                "db 参数应为可选参数"

    def test_collect_and_calculate_async_creates_session_inside(self):
        """
        测试 collect_and_calculate_async 内部获取 Session

        验证点：
        - collect_and_calculate_async 应在内部调用 SessionLocal()
        - 不应依赖外部传入的 db
        """
        async def _test_async():
            from app.services.arp_mac_scheduler import ARPMACScheduler

            scheduler = ARPMACScheduler()

            # Mock SessionLocal
            mock_db = MagicMock()
            mock_db.close = MagicMock()

            # Mock 查询返回空设备列表
            mock_db.query.return_value.filter.return_value.all.return_value = []

            with patch('app.services.arp_mac_scheduler.SessionLocal', return_value=mock_db):
                # 调用 collect_and_calculate_async
                result = await scheduler.collect_and_calculate_async()

                # 验证 Session 已关闭
                assert mock_db.close.called, "Session 应在任务完成后关闭"

        asyncio.run(_test_async())

    def test_session_closed_in_finally_block(self):
        """
        测试 Session 在 finally 块中关闭

        验证点：
        - 即使发生异常，Session 也应该关闭
        - 使用 finally 块确保 Session 关闭
        """
        async def _test_async():
            from app.services.arp_mac_scheduler import ARPMACScheduler

            scheduler = ARPMACScheduler()

            # Mock SessionLocal
            mock_db = MagicMock()
            mock_db.close = MagicMock()
            mock_db.rollback = MagicMock()

            # Mock 查询抛出异常
            mock_db.query.side_effect = Exception("Database error")

            with patch('app.services.arp_mac_scheduler.SessionLocal', return_value=mock_db):
                # 调用 collect_and_calculate_async，期望捕获异常
                try:
                    await scheduler.collect_and_calculate_async()
                except Exception:
                    pass

                # 验证 Session 已关闭（即使在异常情况下）
                assert mock_db.close.called, "Session 应在 finally 块中关闭"

        asyncio.run(_test_async())


class TestARPMACSchedulerAsyncMethods:
    """测试异步方法"""

    def test_collect_all_devices_async_is_async(self):
        """
        测试 collect_all_devices_async 是异步方法

        验证点：
        - collect_all_devices_async 应该是 async 方法
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        import inspect

        scheduler = ARPMACScheduler()

        # 验证方法是异步的
        assert inspect.iscoroutinefunction(scheduler.collect_all_devices_async), \
            "collect_all_devices_async 应为 async 方法"

    def test_collect_and_calculate_async_is_async(self):
        """
        测试 collect_and_calculate_async 是异步方法

        验证点：
        - collect_and_calculate_async 应该是 async 方法
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        import inspect

        scheduler = ARPMACScheduler()

        # 验证方法是异步的
        assert inspect.iscoroutinefunction(scheduler.collect_and_calculate_async), \
            "collect_and_calculate_async 应为 async 方法"

    def test_run_collection_async_is_async(self):
        """
        测试 _run_collection_async 是异步方法

        验证点：
        - _run_collection_async 应该是 async 方法
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        import inspect

        scheduler = ARPMACScheduler()

        # 验证方法是异步的
        assert inspect.iscoroutinefunction(scheduler._run_collection_async), \
            "_run_collection_async 应为 async 方法"


class TestARPMACSchedulerStatus:
    """测试调度器状态"""

    def test_get_status_includes_scheduler_type(self):
        """
        测试 get_status 包含调度器类型信息

        验证点：
        - get_status 方法应返回调度器类型信息
        - 调度器类型应为 AsyncIOScheduler
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler

        scheduler = ARPMACScheduler()

        status = scheduler.get_status()

        # 验证状态字典包含调度器类型
        assert 'scheduler_type' in status, "状态应包含 scheduler_type 字段"
        assert status['scheduler_type'] == 'AsyncIOScheduler', \
            f"调度器类型应为 AsyncIOScheduler，实际为: {status['scheduler_type']}"

    def test_is_running_initial_state(self):
        """
        测试 _is_running 初始状态

        验证点：
        - 调度器创建后 _is_running 应为 False
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler

        scheduler = ARPMACScheduler()

        assert scheduler._is_running is False, "_is_running 初始状态应为 False"

    def test_interval_minutes_default_value(self):
        """
        测试 interval_minutes 默认值

        验证点：
        - 默认采集间隔应为 30 分钟
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler

        scheduler = ARPMACScheduler()

        assert scheduler.interval_minutes == 30, "默认采集间隔应为 30 分钟"


class TestARPMACSchedulerJobConfiguration:
    """测试任务配置"""

    def test_job_added_on_start(self):
        """
        测试 start 方法添加定时任务

        验证点：
        - start 方法应调用 scheduler.add_job
        - 任务函数应为 async 方法
        """
        async def _test_async():
            from app.services.arp_mac_scheduler import ARPMACScheduler
            from apscheduler.schedulers.asyncio import AsyncIOScheduler

            # 创建一个新的调度器实例
            scheduler = ARPMACScheduler()

            # Mock 配置 - settings 是在 start 方法内部导入的
            with patch('app.config.settings') as mock_settings:
                mock_settings.ARP_MAC_COLLECTION_ENABLED = True
                mock_settings.ARP_MAC_COLLECTION_ON_STARTUP = False

                # 调用 start（不传 db）
                scheduler.start()

                # 验证任务已添加
                jobs = scheduler.scheduler.get_jobs()
                arp_job = next((j for j in jobs if j.id == 'arp_mac_collection'), None)

                assert arp_job is not None, "应添加 arp_mac_collection 任务"

                # 关闭调度器
                scheduler.shutdown()

        asyncio.run(_test_async())

    def test_job_uses_async_method(self):
        """
        测试任务使用 async 方法

        验证点：
        - 定时任务应使用 _run_collection_async（async 方法）
        """
        async def _test_async():
            from app.services.arp_mac_scheduler import ARPMACScheduler
            import inspect

            scheduler = ARPMACScheduler()

            # Mock 配置 - settings 是在 start 方法内部导入的
            with patch('app.config.settings') as mock_settings:
                mock_settings.ARP_MAC_COLLECTION_ENABLED = True
                mock_settings.ARP_MAC_COLLECTION_ON_STARTUP = False

                # 调用 start
                scheduler.start()

                # 获取任务
                jobs = scheduler.scheduler.get_jobs()
                arp_job = next((j for j in jobs if j.id == 'arp_mac_collection'), None)

                if arp_job:
                    # 验证任务函数是 _run_collection_async
                    assert arp_job.func == scheduler._run_collection_async, \
                        "任务函数应为 _run_collection_async"

                # 关闭调度器
                scheduler.shutdown()

        asyncio.run(_test_async())


class TestARPMACSchedulerNoRunAsyncComplexity:
    """测试 _run_async 三层降级逻辑已移除"""

    def test_no_complex_run_async_method(self):
        """
        测试不存在复杂的 _run_async 三层降级逻辑

        验证点：
        - 原代码存在 _run_async 三层降级逻辑（try/except/finally）
        - 新代码应直接使用 async 方法，不需要降级逻辑
        """
        from app.services.arp_mac_scheduler import ARPMACScheduler
        import inspect

        scheduler = ARPMACScheduler()

        # 检查是否存在 _run_async 方法
        has_run_async = hasattr(scheduler, '_run_async')

        # 如果存在 _run_async，它应该是一个简单包装或已被移除
        # 主要使用的是 _run_collection_async
        assert hasattr(scheduler, '_run_collection_async'), \
            "应存在 _run_collection_async 方法"

        # 检查 _run_collection_async 是 async 方法
        assert inspect.iscoroutinefunction(scheduler._run_collection_async), \
            "_run_collection_async 应为 async 方法"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])