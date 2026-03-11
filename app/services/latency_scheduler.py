"""
延迟检测调度器服务
负责管理设备延迟的定时检测任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.models import get_db
from app.services.latency_service import latency_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LatencySchedulerService:
    """
    延迟检测调度器服务类
    管理设备延迟的定时检测任务
    """
    
    def __init__(
        self,
        enabled: bool = True,
        interval_minutes: int = 5,
        exclude_statuses: list = None
    ):
        """
        初始化延迟检测调度器
        
        Args:
            enabled: 是否启用定时检测
            interval_minutes: 检测间隔（分钟）
            exclude_statuses: 排除的状态列表
        """
        self.enabled = enabled
        self.interval_minutes = interval_minutes
        self.exclude_statuses = exclude_statuses or ["maintenance"]
        self.scheduler = BackgroundScheduler()
        self._running = False
        
        logger.info(f"Latency scheduler initialized (enabled={enabled}, interval={interval_minutes}min)")
    
    def start(self):
        """
        启动调度器
        """
        if not self.enabled:
            logger.info("Latency scheduler is disabled")
            return
        
        if self._running:
            logger.info("Latency scheduler is already running")
            return
        
        self.scheduler.add_job(
            func=self._check_all_devices,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='latency_check_job',
            replace_existing=True,
            misfire_grace_time=60
        )
        
        self.scheduler.start()
        self._running = True
        logger.info("Latency scheduler started")
    
    def shutdown(self):
        """
        关闭调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Latency scheduler shutdown")
    
    def _check_all_devices(self):
        """
        检测所有启用延迟检测的设备
        """
        logger.info("Starting scheduled latency check for all devices")
        db = next(get_db())
        
        try:
            results = latency_service.check_all_enabled_devices(
                db, 
                self.exclude_statuses
            )
            
            success_count = sum(1 for r in results if r["success"])
            failed_count = len(results) - success_count
            
            logger.info(
                f"Latency check completed: {success_count} success, {failed_count} failed, "
                f"total {len(results)} devices"
            )
            
        except Exception as e:
            logger.error(f"Latency check task failed: {str(e)}")
        finally:
            db.close()
    
    def trigger_check_now(self):
        """
        立即触发一次延迟检测
        """
        logger.info("Triggering immediate latency check")
        self._check_all_devices()
    
    def get_status(self) -> dict:
        """
        获取调度器状态
        
        Returns:
            状态信息字典
        """
        return {
            "enabled": self.enabled,
            "running": self._running,
            "interval_minutes": self.interval_minutes,
            "exclude_statuses": self.exclude_statuses,
            "next_run_time": self._get_next_run_time()
        }
    
    def _get_next_run_time(self):
        """
        获取下次运行时间
        """
        job = self.scheduler.get_job('latency_check_job')
        if job:
            return job.next_run_time.isoformat() if job.next_run_time else None
        return None


latency_scheduler = None


def init_latency_scheduler(
    enabled: bool = True,
    interval_minutes: int = 5,
    exclude_statuses: list = None
) -> LatencySchedulerService:
    """
    初始化并返回延迟检测调度器实例
    
    Args:
        enabled: 是否启用定时检测
        interval_minutes: 检测间隔（分钟）
        exclude_statuses: 排除的状态列表
        
    Returns:
        延迟检测调度器实例
    """
    global latency_scheduler
    latency_scheduler = LatencySchedulerService(
        enabled=enabled,
        interval_minutes=interval_minutes,
        exclude_statuses=exclude_statuses
    )
    return latency_scheduler


def get_latency_scheduler() -> LatencySchedulerService:
    """
    获取延迟检测调度器服务实例
    """
    global latency_scheduler
    if latency_scheduler is None:
        latency_scheduler = LatencySchedulerService()
    return latency_scheduler
