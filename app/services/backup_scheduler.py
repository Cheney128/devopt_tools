"""
备份调度器服务
负责管理设备配置的自动备份任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models import get_db
from app.models.models import BackupSchedule, Device, Configuration
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
    """
    
    def __init__(self):
        """
        初始化备份调度器
        """
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Backup scheduler initialized")
    
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
        """
        logger.info("Loading backup schedules from database")
        # 清除现有任务
        self.scheduler.remove_all_jobs()
        
        # 获取所有激活的备份任务
        schedules = db.query(BackupSchedule).filter(BackupSchedule.is_active == True).all()
        
        for schedule in schedules:
            self.add_schedule(schedule, db)
        
        logger.info(f"Loaded {len(schedules)} backup schedules")
    
    def add_schedule(self, schedule: BackupSchedule, db: Session):
        """
        添加备份任务到调度器
        """
        # 获取设备信息
        device = db.query(Device).filter(Device.id == schedule.device_id).first()
        if not device:
            logger.error(f"Device {schedule.device_id} not found for backup schedule {schedule.id}")
            return
        
        # 根据备份类型创建触发器
        trigger = self._create_trigger(schedule)
        if not trigger:
            logger.error(f"Invalid schedule type {schedule.schedule_type} for backup schedule {schedule.id}")
            return
        
        # 添加任务到调度器
        self.scheduler.add_job(
            func=self._execute_backup,
            trigger=trigger,
            id=f"backup_{schedule.id}",
            replace_existing=True,
            args=[schedule.device_id, db],
            misfire_grace_time=300  # 允许5分钟的错过执行宽限期
        )
        
        logger.info(f"Added backup schedule {schedule.id} for device {device.hostname}")
    
    def update_schedule(self, schedule: BackupSchedule, db: Session):
        """
        更新调度器中的备份任务
        """
        # 先移除旧任务
        self.remove_schedule(schedule.id)
        
        # 如果任务是激活的，添加新任务
        if schedule.is_active:
            self.add_schedule(schedule, db)
    
    def remove_schedule(self, schedule_id: int):
        """
        从调度器中移除备份任务
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
    
    async def _execute_backup(self, device_id: int, db: Session):
        """
        执行设备配置备份
        """
        logger.info(f"Executing backup for device {device_id}")
        
        try:
            # 导入需要的服务
            from app.services.netmiko_service import NetmikoService
            from app.services.git_service import GitService
            
            # 创建服务实例
            netmiko_service = NetmikoService()
            git_service = GitService()
            
            # 调用现有的配置采集函数
            from app.api.endpoints.configurations import collect_config_from_device
            await collect_config_from_device(device_id, db, netmiko_service, git_service)
            
            logger.info(f"Backup completed successfully for device {device_id}")
        except Exception as e:
            logger.error(f"Backup failed for device {device_id}: {str(e)}")


# 创建全局备份调度器实例
backup_scheduler = BackupSchedulerService()


def get_backup_scheduler() -> BackupSchedulerService:
    """
    获取备份调度器服务实例
    """
    return backup_scheduler
