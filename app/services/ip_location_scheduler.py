"""
IP 定位调度器服务
负责管理 IP 地址定位数据的定期采集任务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from app.models import get_db
from app.config import settings
from app.services.ip_location_service import get_ip_location_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IPLocationSchedulerService:
    """
    IP 定位调度器服务类
    管理 ARP 和 MAC 地址表的定期采集任务
    """

    def __init__(self):
        """
        初始化 IP 定位调度器
        """
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("IP Location scheduler initialized")

    def start(self):
        """
        启动调度器
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("IP Location scheduler started")

    def shutdown(self):
        """
        关闭调度器
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("IP Location scheduler shutdown")

    def load_schedules(self, db: Session):
        """
        加载 IP 定位采集任务
        """
        if not settings.IP_LOCATION_COLLECTION_ENABLED:
            logger.info("IP Location collection is disabled, skipping schedule loading")
            return

        logger.info("Loading IP Location collection schedules")
        # 清除现有任务
        self.scheduler.remove_all_jobs()

        # 创建间隔触发器
        trigger = IntervalTrigger(
            hours=settings.IP_LOCATION_COLLECTION_INTERVAL_HOURS,
            jitter=300  # 5分钟抖动，避免固定时间点执行
        )

        # 添加任务到调度器
        self.scheduler.add_job(
            func=self._execute_collection,
            trigger=trigger,
            id="ip_location_collection",
            replace_existing=True,
            misfire_grace_time=3600  # 允许1小时的错过执行宽限期
        )

        logger.info(f"IP Location collection scheduled to run every {settings.IP_LOCATION_COLLECTION_INTERVAL_HOURS} hours")

    def _is_silent_hour(self) -> bool:
        """
        检查当前时间是否在静默时段内
        """
        if not settings.IP_LOCATION_SILENT_HOURS:
            return False

        current_hour = datetime.now().hour
        return current_hour in settings.IP_LOCATION_SILENT_HOURS

    async def _execute_collection(self):
        """
        执行 IP 定位数据采集
        """
        if self._is_silent_hour():
            logger.info("Current time is in silent hours, skipping IP location collection")
            return

        logger.info("Starting scheduled IP location collection")

        try:
            # 获取数据库会话
            db = next(get_db())

            # 创建 IP 定位服务实例
            ip_location_service = get_ip_location_service(db)

            # 执行采集
            result = await ip_location_service.collect_from_all_devices()

            if result["success"]:
                logger.info(
                    f"Scheduled IP location collection completed successfully: "
                    f"ARP entries: {result['arp_entries_collected']}, "
                    f"MAC entries: {result['mac_entries_collected']}, "
                    f"Devices: {result['devices_success']} success, {result['devices_failed']} failed"
                )
            else:
                logger.error(f"Scheduled IP location collection failed: {result['message']}")

        except Exception as e:
            logger.error(f"Scheduled IP location collection failed with exception: {str(e)}", exc_info=True)


# 创建全局 IP 定位调度器实例
ip_location_scheduler = IPLocationSchedulerService()


def get_ip_location_scheduler() -> IPLocationSchedulerService:
    """
    获取 IP 定位调度器服务实例
    """
    return ip_location_scheduler
