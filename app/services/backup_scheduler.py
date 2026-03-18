
"""
备份调度器服务
负责管理设备配置的自动备份任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
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
        self.scheduler.remove_all_jobs()
        
        schedules = db.query(BackupSchedule).filter(BackupSchedule.is_active == True).all()
        
        for schedule in schedules:
            self.add_schedule(schedule, db)
        
        logger.info(f"Loaded {len(schedules)} backup schedules")
    
    def add_schedule(self, schedule: BackupSchedule, db: Session):
        """
        添加备份任务到调度器
        """
        device = db.query(Device).filter(Device.id == schedule.device_id).first()
        if not device:
            logger.error(f"Device {schedule.device_id} not found for backup schedule {schedule.id}")
            return
        
        trigger = self._create_trigger(schedule)
        if not trigger:
            logger.error(f"Invalid schedule type {schedule.schedule_type} for backup schedule {schedule.id}")
            return
        
        self.scheduler.add_job(
            func=self._execute_backup,
            trigger=trigger,
            id=f"backup_{schedule.id}",
            replace_existing=True,
            args=[schedule.device_id],
            misfire_grace_time=300
        )
        
        logger.info(f"Added backup schedule {schedule.id} for device {device.hostname}")
    
    def update_schedule(self, schedule: BackupSchedule, db: Session):
        """
        更新调度器中的备份任务
        """
        self.remove_schedule(schedule.id)
        
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
            return CronTrigger(minute="0")
        elif schedule.schedule_type == "daily":
            if schedule.time:
                hour, minute = map(int, schedule.time.split(":"))
                return CronTrigger(hour=hour, minute=minute)
            else:
                return CronTrigger(hour="1", minute="0")
        elif schedule.schedule_type == "monthly":
            day = schedule.day if schedule.day else 1
            if schedule.time:
                hour, minute = map(int, schedule.time.split(":"))
                return CronTrigger(day=day, hour=hour, minute=minute)
            else:
                return CronTrigger(day=day, hour="1", minute="0")
        else:
            return None
    
    def _execute_backup(self, device_id: int):
        """
        执行设备配置备份（同步函数）
        """
        import asyncio
        from app.models import SessionLocal
        from app.services.backup_service import BackupService
        
        task_id = f"scheduled_{uuid.uuid4().hex[:8]}"
        logger.info(f"[ScheduledBackup] Starting backup for device {device_id}, task_id={task_id}")
        
        retry_count = 1
        retry_delay = 5
        
        for attempt in range(retry_count + 1):
            db = None
            try:
                logger.info(f"[ScheduledBackup] Creating database session... (attempt {attempt + 1}/{retry_count + 1})")
                db = SessionLocal()
                
                backup_service = BackupService()
                
                logger.info(f"[ScheduledBackup] Calling BackupService.execute_scheduled_backup()...")
                result = asyncio.run(
                    backup_service.execute_scheduled_backup(device_id, db, task_id)
                )
                
                if result.get("success"):
                    logger.info(f"[ScheduledBackup] Backup completed successfully for device {device_id}")
                    return
                else:
                    logger.warning(f"[ScheduledBackup] Backup failed for device {device_id}: {result.get('message')}")
                    
            except Exception as e:
                error_message = str(e)
                logger.error(f"[ScheduledBackup] Backup failed for device {device_id}: {error_message} (attempt {attempt + 1}/{retry_count + 1})")
                
                if attempt < retry_count:
                    logger.info(f"[ScheduledBackup] Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    logger.error(f"[ScheduledBackup] Max retries exceeded for device {device_id}")
            finally:
                if db:
                    db.close()
                    logger.debug(f"[ScheduledBackup] Database session closed")


backup_scheduler = BackupSchedulerService()


def get_backup_scheduler() -> BackupSchedulerService:
    """
    获取备份调度器服务实例
    """
    return backup_scheduler

