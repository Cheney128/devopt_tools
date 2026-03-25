# -*- coding: utf-8 -*-
"""
IP 定位调度器服务

功能：
1. 管理预计算定时任务
2. 每 10 分钟执行一次预计算
3. 支持手动触发
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

from app.models import get_db, SessionLocal
from app.services.ip_location_calculator import IPLocationCalculator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IPLocationScheduler:
    """
    IP 定位调度器服务

    管理预计算定时任务，支持自动和手动触发。
    """

    def __init__(self, interval_minutes: int = 10):
        """
        初始化调度器

        Args:
            interval_minutes: 执行间隔（分钟），默认 10 分钟
        """
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self._is_running = False
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None

    def start(self):
        """
        启动调度器
        """
        if self._is_running:
            logger.warning("IP 定位调度器已在运行中")
            return

        # 添加定时任务
        self.scheduler.add_job(
            func=self._run_calculation,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='ip_location_calculation',
            name='IP 定位预计算',
            replace_existing=True,
            misfire_grace_time=300  # 允许 5 分钟的错过执行宽限期
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(f"IP 定位调度器已启动，间隔: {self.interval_minutes} 分钟")

    def shutdown(self):
        """
        关闭调度器
        """
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("IP 定位调度器已关闭")

    def _run_calculation(self):
        """
        执行预计算（定时任务回调）
        """
        logger.info("开始执行 IP 定位预计算...")

        try:
            db = SessionLocal()
            try:
                calculator = IPLocationCalculator(db)
                stats = calculator.calculate_batch()

                self._last_run = datetime.now()
                self._last_stats = stats

                logger.info(f"IP 定位预计算完成: 匹配 {stats.get('matched', 0)} 条, "
                           f"归档 {stats.get('archived', 0)} 条, "
                           f"耗时 {stats.get('duration_seconds', 0):.2f} 秒")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"IP 定位预计算失败: {e}", exc_info=True)

    def trigger_now(self) -> dict:
        """
        手动触发一次预计算

        Returns:
            计算结果统计
        """
        logger.info("手动触发 IP 定位预计算...")

        db = SessionLocal()
        try:
            calculator = IPLocationCalculator(db)
            stats = calculator.calculate_batch()

            self._last_run = datetime.now()
            self._last_stats = stats

            logger.info(f"手动预计算完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"手动预计算失败: {e}", exc_info=True)
            return {'error': str(e)}
        finally:
            db.close()

    def get_status(self) -> dict:
        """
        获取调度器状态

        Returns:
            状态信息字典
        """
        jobs = self.scheduler.get_jobs() if self._is_running else []
        ip_job = next((j for j in jobs if j.id == 'ip_location_calculation'), None)

        return {
            'is_running': self._is_running,
            'interval_minutes': self.interval_minutes,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'last_stats': self._last_stats,
            'next_run': ip_job.next_run_time.isoformat() if ip_job and ip_job.next_run_time else None,
        }


# 创建全局调度器实例
ip_location_scheduler = IPLocationScheduler(interval_minutes=10)


def get_ip_location_scheduler() -> IPLocationScheduler:
    """
    获取 IP 定位调度器实例

    Returns:
        调度器实例
    """
    return ip_location_scheduler