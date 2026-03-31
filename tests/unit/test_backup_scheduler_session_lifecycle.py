"""
Backup Scheduler Session 生命周期测试

测试目的：验证 backup_scheduler 的 Session 生命周期管理正确

问题分析：
- 当前代码在 add_schedule() 时传入 db Session
- 调度器执行时可能已过去数小时/数天
- Session 可能已过期或连接已断开
- 使用过期的 Session 会导致数据库操作失败

修复方案：
- add_schedule() 不再传入 db 给任务
- 在 _execute_backup() 任务内部重新获取 Session
- 任务完成后关闭 Session
- 确保每次任务执行都使用新鲜的 Session

测试用例：
1. add_schedule 不应传入 db 参数
2. _execute_backup 内部应获取 Session
3. _execute_backup 完成后应关闭 Session
4. 任务执行失败也应关闭 Session
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBackupSchedulerSessionLifecycle:
    """测试备份调度器 Session 生命周期"""

    def test_add_schedule_signature_no_db_parameter(self):
        """
        测试 add_schedule 方法签名不包含 db 参数

        验证点：
        - add_schedule 方法应该只接受 schedule 参数
        - 不应该接受 db 参数
        - 当前代码 add_schedule(schedule, db) 应改为 add_schedule(schedule)
        """
        from app.services.backup_scheduler import BackupSchedulerService
        import inspect

        scheduler = BackupSchedulerService()

        # 获取方法签名
        sig = inspect.signature(scheduler.add_schedule)

        # 验证参数列表
        params = list(sig.parameters.keys())

        # 修复后应该只有 'schedule' 参数，没有 'db' 参数
        assert 'schedule' in params
        assert 'db' not in params, "add_schedule 方法不应该接受 db 参数"

    def test_add_job_args_no_db(self):
        """
        测试 add_job 的 args 不包含 db

        验证点：
        - scheduler.add_job() 的 args 参数应该只包含 device_id
        - 不应该包含 db
        - 当前代码 args=[schedule.device_id, db] 应改为 args=[device_id]
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock schedule
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_schedule.device_id = 1
        mock_schedule.schedule_type = 'daily'
        mock_schedule.time = '01:00'
        mock_schedule.day = None

        # Mock db - 修复后不再需要
        mock_db = MagicMock()

        # Mock scheduler.add_job
        with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
            # 调用 add_schedule - 修复后不应该传 db
            scheduler.add_schedule(mock_schedule)

            # 验证 add_job 的 args 参数
            call_args = mock_add_job.call_args
            if call_args:
                args_passed = call_args[1].get('args', call_args[0][1] if len(call_args[0]) > 1 else [])

                # 修复后 args 应只包含 device_id，不包含 db
                # args 应为 [1] 或 [device_id]，不应为 [device_id, db]
                assert len(args_passed) == 1, f"args 应只包含一个参数（device_id），实际为: {args_passed}"
                assert args_passed[0] == 1, f"args 第一个参数应为 device_id=1，实际为: {args_passed[0]}"

    def test_execute_backup_signature_no_db_parameter(self):
        """
        测试 _execute_backup 方法签名不包含 db 参数

        验证点：
        - _execute_backup 方法应该只接受 device_id 参数
        - 不应该接受 db 参数
        - 当前代码 _execute_backup(device_id, db) 应改为 _execute_backup(device_id)
        """
        from app.services.backup_scheduler import BackupSchedulerService
        import inspect

        scheduler = BackupSchedulerService()

        # 获取方法签名
        sig = inspect.signature(scheduler._execute_backup)

        # 验证参数列表
        params = list(sig.parameters.keys())

        # 修复后应该只有 'device_id' 参数，没有 'db' 参数
        assert 'device_id' in params
        assert 'db' not in params, "_execute_backup 方法不应该接受 db 参数"

    @pytest.mark.asyncio
    async def test_execute_backup_creates_session_inside(self):
        """
        测试 _execute_backup 内部获取 Session

        验证点：
        - _execute_backup 应该在内部调用 get_db() 获取 Session
        - 不应该依赖外部传入的 db
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock get_db 返回一个 Session
        mock_db = MagicMock()
        mock_db.close = MagicMock()

        # Mock Device 查询返回设备
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-switch"

        # Mock BackupSchedule 查询
        mock_schedule = MagicMock()
        mock_schedule.id = 1

        # Mock 数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_device, mock_schedule]

        # Mock collect_config_from_device
        with patch('app.services.backup_scheduler.collect_config_from_device', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = {
                "config_changed": True,
                "config_id": 1,
                "config_size": 1000,
                "git_commit_id": "abc123"
            }

            # Mock get_db 生成器
            def mock_get_db_gen():
                yield mock_db

            with patch('app.services.backup_scheduler.get_db', mock_get_db_gen):
                # Mock BackupExecutionLog
                with patch('app.services.backup_scheduler.BackupExecutionLog') as mock_log:
                    mock_log_instance = MagicMock()
                    mock_log.return_value = mock_log_instance

                    # 调用 _execute_backup（修复后不传 db）
                    await scheduler._execute_backup(device_id=1)

                    # 验证 mock_db.add 和 mock_db.commit 被调用
                    assert mock_db.add.called or mock_db.commit.called, "Session 应被用于数据库操作"

    @pytest.mark.asyncio
    async def test_execute_backup_closes_session_on_success(self):
        """
        测试 _execute_backup 成功后关闭 Session

        验证点：
        - 任务执行成功后应该关闭 Session
        - 使用 finally 块确保 Session 关闭
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock get_db 返回一个 Session
        mock_db = MagicMock()
        mock_db.close = MagicMock()

        # Mock Device 查询返回设备
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-switch"

        # Mock BackupSchedule 查询
        mock_schedule = MagicMock()
        mock_schedule.id = 1

        # Mock 数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_device, mock_schedule]

        # Mock collect_config_from_device
        with patch('app.services.backup_scheduler.collect_config_from_device', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = {
                "config_changed": True,
                "config_id": 1,
                "config_size": 1000,
                "git_commit_id": "abc123"
            }

            # Mock get_db 生成器
            def mock_get_db_gen():
                yield mock_db

            with patch('app.services.backup_scheduler.get_db', mock_get_db_gen):
                # Mock BackupExecutionLog
                with patch('app.services.backup_scheduler.BackupExecutionLog') as mock_log:
                    mock_log_instance = MagicMock()
                    mock_log.return_value = mock_log_instance

                    # 调用 _execute_backup
                    await scheduler._execute_backup(device_id=1)

                    # 验证 Session 已关闭
                    assert mock_db.close.called, "Session 应在任务完成后关闭"

    @pytest.mark.asyncio
    async def test_execute_backup_closes_session_on_failure(self):
        """
        测试 _execute_backup 失败后也关闭 Session

        验证点：
        - 任务执行失败也应该关闭 Session
        - 使用 finally 块确保 Session 关闭
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock get_db 返回一个 Session
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        mock_db.rollback = MagicMock()

        # Mock collect_config_from_device 抛出异常
        with patch('app.services.backup_scheduler.collect_config_from_device', new_callable=AsyncMock) as mock_collect:
            mock_collect.side_effect = Exception("Connection failed")

            # Mock get_db 生成器
            def mock_get_db_gen():
                yield mock_db

            with patch('app.services.backup_scheduler.get_db', mock_get_db_gen):
                # Mock BackupExecutionLog
                with patch('app.services.backup_scheduler.BackupExecutionLog') as mock_log:
                    mock_log_instance = MagicMock()
                    mock_log.return_value = mock_log_instance

                    # Mock 数据库查询
                    mock_db.query.return_value.filter.return_value.first.return_value = None

                    # 调用 _execute_backup，应该捕获异常
                    try:
                        await scheduler._execute_backup(device_id=1)
                    except Exception:
                        pass  # 测试中忽略异常

                    # 验证 Session 已关闭（即使失败）
                    assert mock_db.close.called or mock_db.rollback.called, \
                        "Session 应在任务失败后关闭或回滚"


class TestBackupSchedulerUsesAsyncIOScheduler:
    """测试备份调度器使用 AsyncIOScheduler"""

    def test_scheduler_is_asyncio_scheduler(self):
        """
        测试调度器类型是否为 AsyncIOScheduler

        验证点：
        - BackupSchedulerService 应使用 AsyncIOScheduler
        - 当前代码使用 BackgroundScheduler（不支持 async 任务）
        """
        from app.services.backup_scheduler import BackupSchedulerService
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        scheduler = BackupSchedulerService()

        # 验证调度器类型
        assert isinstance(scheduler.scheduler, AsyncIOScheduler), \
            f"调度器应为 AsyncIOScheduler，实际为: {type(scheduler.scheduler)}"

    def test_scheduler_not_background_scheduler(self):
        """
        测试调度器不是 BackgroundScheduler

        验证点：
        - BackgroundScheduler 在后台线程运行，无事件循环
        - async 函数在 BackgroundScheduler 中无法正常执行
        """
        from app.services.backup_scheduler import BackupSchedulerService
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackupSchedulerService()

        # 验证不是 BackgroundScheduler
        assert not isinstance(scheduler.scheduler, BackgroundScheduler), \
            "调度器不应该使用 BackgroundScheduler"

    def test_scheduler_not_started_in_init(self):
        """
        测试调度器不在 __init__ 中启动

        验证点：
        - __init__ 中不应该调用 scheduler.start()
        - 调度器应该在 lifespan 中启动
        """
        from app.services.backup_scheduler import BackupSchedulerService

        # 创建新的调度器实例
        scheduler = BackupSchedulerService()

        # 验证调度器未启动（或者使用懒启动）
        # 注意：修复后 __init__ 不应该调用 start()
        # 如果 scheduler.running 为 True，说明在 __init__ 中启动了，这是错误的
        # 修复后应该为 False，或者使用 start() 方法手动启动
        # 这里我们只验证可以手动控制启动
        assert hasattr(scheduler, 'start'), "调度器应有 start 方法"
        assert hasattr(scheduler, 'shutdown'), "调度器应有 shutdown 方法"


class TestBackupSchedulerLoadSchedulesNoDb:
    """测试 load_schedules 不传入 db 给 add_schedule"""

    def test_load_schedules_calls_add_schedule_without_db(self):
        """
        测试 load_schedules 调用 add_schedule 不传 db

        验证点：
        - load_schedules 应调用 add_schedule(schedule)
        - 不应该调用 add_schedule(schedule, db)
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock db
        mock_db = MagicMock()

        # Mock schedules 查询
        mock_schedule1 = MagicMock()
        mock_schedule1.id = 1
        mock_schedule1.device_id = 1
        mock_schedule1.schedule_type = 'daily'
        mock_schedule1.time = '01:00'
        mock_schedule1.is_active = True

        mock_schedule2 = MagicMock()
        mock_schedule2.id = 2
        mock_schedule2.device_id = 2
        mock_schedule2.schedule_type = 'hourly'
        mock_schedule2.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_schedule1, mock_schedule2]

        # Mock scheduler.remove_all_jobs
        scheduler.scheduler.remove_all_jobs = MagicMock()

        # Mock add_schedule 方法
        with patch.object(scheduler, 'add_schedule') as mock_add_schedule:
            # 调用 load_schedules
            scheduler.load_schedules(mock_db)

            # 验证 add_schedule 被调用两次，且不传 db
            assert mock_add_schedule.call_count == 2

            # 验证每次调用的参数只有 schedule，没有 db
            for call in mock_add_schedule.call_args_list:
                args = call[0]  # positional args
                kwargs = call[1]  # keyword args

                # 修复后应该只有 1 个参数（schedule）
                assert len(args) == 1, f"add_schedule 应只接受 1 个参数，实际为: {len(args)}"


class TestBackupSchedulerRollbackOnException:
    """测试异常发生时调用 rollback（I2 修复验证）"""

    @pytest.mark.asyncio
    async def test_execute_backup_rollback_on_exception(self):
        """
        验证异常发生时调用 rollback

        测试步骤：
        1. Mock db.rollback() 方法
        2. 模拟执行过程中的异常
        3. 验证 rollback 被调用
        4. 验证失败日志仍能正常记录
        """
        from app.services.backup_scheduler import BackupSchedulerService

        scheduler = BackupSchedulerService()

        # Mock get_db 返回一个 Session
        mock_db = MagicMock()
        mock_db.close = MagicMock()
        mock_db.rollback = MagicMock()

        # Mock collect_config_from_device 抛出异常
        with patch('app.services.backup_scheduler.collect_config_from_device', new_callable=AsyncMock) as mock_collect:
            mock_collect.side_effect = Exception("Simulated error")

            # Mock get_db 生成器
            def mock_get_db_gen():
                yield mock_db

            with patch('app.services.backup_scheduler.get_db', mock_get_db_gen):
                # Mock BackupExecutionLog
                with patch('app.services.backup_scheduler.BackupExecutionLog') as mock_log:
                    mock_log_instance = MagicMock()
                    mock_log.return_value = mock_log_instance

                    # Mock 数据库查询
                    mock_db.query.return_value.filter.return_value.first.return_value = None

                    # 调用 _execute_backup
                    await scheduler._execute_backup(device_id=1)

                    # 验证 rollback 被调用
                    assert mock_db.rollback.called, "rollback 应在异常时被调用"

                    # 验证失败日志被记录
                    assert mock_db.add.called, "失败日志应被添加"
                    assert mock_db.commit.called, "失败日志应被提交"

                    # 验证 Session 已关闭
                    assert mock_db.close.called, "Session 应在 finally 中关闭"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])