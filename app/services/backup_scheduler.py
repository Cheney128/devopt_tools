"""
备份调度器服务
负责管理设备配置的自动备份任务

修复说明：
- 将 BackgroundScheduler 替换为 AsyncIOScheduler（支持 async 任务）
- add_schedule() 不再传入 db 参数（避免 Session 生命周期问题）
- _execute_backup() 内部获取 Session，完成后关闭
- __init__ 中不启动调度器，在 lifespan 中启动
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from typing import Optional
import logging
import uuid

from app.models import get_db
from app.models.models import BackupSchedule, Device, Configuration, BackupExecutionLog
from app.services.netmiko_service import NetmikoService
from app.services.git_service import GitService
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupSchedulerService:
    """
    备份调度器服务类
    管理设备配置的自动备份任务

    使用 AsyncIOScheduler：
    - 支持 async 任务执行
    - 与 FastAPI 事件循环兼容
    - 避免 Session 生命周期问题
    """

    def __init__(self):
        """
        初始化备份调度器（不启动）

        使用 AsyncIOScheduler 替代 BackgroundScheduler：
        - BackgroundScheduler 在后台线程运行，无事件循环
        - AsyncIOScheduler 在主事件循环中运行，支持 async 任务

        注意：不在 __init__ 中启动调度器，应在 lifespan 中启动
        """
        self.scheduler = AsyncIOScheduler()
        # 不在 __init__ 中启动，在 lifespan 中启动
        logger.info("Backup scheduler initialized (AsyncIOScheduler, not started)")
    
    def start(self):
        """
        启动调度器
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Backup scheduler started")
    
    def shutdown(self):
        """
        关闭调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Backup scheduler shutdown")
    
    def load_schedules(self, db: Session):
        """
        从数据库加载所有激活的备份任务

        Args:
            db: 数据库 Session（用于查询数据库，但不传给任务）

        注意：
            db 只用于查询数据库，不传递给定时任务
            定时任务在执行时会重新获取 Session
        """
        logger.info("Loading backup schedules from database")
        # 清除现有任务
        self.scheduler.remove_all_jobs()

        # 获取所有激活的备份任务
        schedules = db.query(BackupSchedule).filter(BackupSchedule.is_active == True).all()

        for schedule in schedules:
            self.add_schedule(schedule)  # 不再传 db

        logger.info(f"Loaded {len(schedules)} backup schedules")

    def add_schedule(self, schedule: BackupSchedule):
        """
        添加备份任务到调度器

        Args:
            schedule: 备份计划对象

        注意：
            不再传入 db 参数，避免 Session 生命周期问题
            任务执行时会在内部重新获取 Session
        """
        # 根据备份类型创建触发器
        trigger = self._create_trigger(schedule)
        if not trigger:
            logger.error(f"Invalid schedule type {schedule.schedule_type} for backup schedule {schedule.id}")
            return

        # 添加任务到调度器 - 只传 device_id，不传 db
        self.scheduler.add_job(
            func=self._execute_backup,
            trigger=trigger,
            id=f"backup_{schedule.id}",
            replace_existing=True,
            args=[schedule.device_id],  # 只传 device_id，不传 db
            misfire_grace_time=300  # 允许5分钟的错过执行宽限期
        )

        logger.info(f"Added backup schedule {schedule.id} for device {schedule.device_id}")
    
    def update_schedule(self, schedule: BackupSchedule):
        """
        更新调度器中的备份任务

        Args:
            schedule: 备份计划对象

        注意：
            不再传入 db 参数，与 add_schedule 保持一致
        """
        # 先移除旧任务
        self.remove_schedule(schedule.id)

        # 如果任务是激活的，添加新任务
        if schedule.is_active:
            self.add_schedule(schedule)

    def remove_schedule(self, schedule_id: int):
        """
        从调度器中移除备份任务

        Args:
            schedule_id: 备份计划 ID
        """
        job_id = f"backup_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed backup schedule {schedule_id}")
    
    def _create_trigger(self, schedule: BackupSchedule) -> Optional[CronTrigger]:
        """
        根据备份类型创建Cron触发器
        """
        if schedule.schedule_type == "hourly":
            # 每小时执行一次
            return CronTrigger(minute="0")
        elif schedule.schedule_type == "daily":
            # 每天指定时间执行
            if schedule.time:
                hour, minute = map(int, schedule.time.split(":"))
                return CronTrigger(hour=hour, minute=minute)
            else:
                # 默认每天凌晨1点执行
                return CronTrigger(hour="1", minute="0")
        elif schedule.schedule_type == "monthly":
            # 每月指定日期和时间执行
            day = schedule.day if schedule.day else 1
            if schedule.time:
                hour, minute = map(int, schedule.time.split(":"))
                return CronTrigger(day=day, hour=hour, minute=minute)
            else:
                # 默认每月1号凌晨1点执行
                return CronTrigger(day=day, hour="1", minute="0")
        else:
            return None
    
    async def _execute_backup(self, device_id: int):
        """
        执行设备配置备份

        Args:
            device_id: 设备 ID

        注意：
            在任务内部重新获取 Session，避免 Session 生命周期问题
            任务完成后关闭 Session
        """
        task_id = f"scheduled_{uuid.uuid4().hex[:8]}"
        logger.info(f"Executing backup for device {device_id}, task_id: {task_id}")

        started_at = datetime.now()
        execution_log = None

        # 在任务内部获取 Session
        db = next(get_db())

        try:
            # 获取设备信息
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                logger.error(f"Device {device_id} not found")
                return

            # 导入需要的服务
            from app.services.netmiko_service import NetmikoService
            from app.services.git_service import GitService

            # 创建服务实例
            netmiko_service = NetmikoService()
            git_service = GitService()

            # 调用现有的配置采集函数
            from app.api.endpoints.configurations import collect_config_from_device
            result = await collect_config_from_device(device_id, db, netmiko_service, git_service)

            # 计算执行时间
            execution_time = (datetime.now() - started_at).total_seconds()

            # 查找对应的备份计划
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()

            # 判断配置是否变化
            config_changed = result.get("config_changed", True)

            # 构建备注信息
            error_message = None
            if not config_changed:
                error_message = "配置无变化，已成功登录并验证设备配置"

            # 创建执行日志
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="success",
                execution_time=execution_time,
                trigger_type="scheduled",
                config_id=result.get("config_id"),
                config_size=result.get("config_size", 0),
                git_commit_id=result.get("git_commit_id"),
                error_message=error_message,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)

            # 更新备份计划的最后执行时间
            if schedule:
                schedule.last_run_time = datetime.now()

            db.commit()
            logger.info(f"Backup completed successfully for device {device_id}, task_id: {task_id}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Backup failed for device {device_id}: {error_message}")

            # 查找对应的备份计划
            schedule = db.query(BackupSchedule).filter(
                BackupSchedule.device_id == device_id,
                BackupSchedule.is_active == True
            ).first()

            # 创建失败日志
            execution_log = BackupExecutionLog(
                task_id=task_id,
                device_id=device_id,
                schedule_id=schedule.id if schedule else None,
                status="failed",
                execution_time=(datetime.now() - started_at).total_seconds(),
                trigger_type="scheduled",
                error_message=error_message,
                started_at=started_at,
                completed_at=datetime.now()
            )
            db.add(execution_log)
            db.commit()

        finally:
            # 任务完成后关闭 Session
            db.close()
            logger.debug(f"Session closed for backup task {task_id}")


# 创建全局备份调度器实例
backup_scheduler = BackupSchedulerService()


def get_backup_scheduler() -> BackupSchedulerService:
    """
    获取备份调度器服务实例
    """
    return backup_scheduler
