# -*- coding: utf-8 -*-
"""
IP 定位调度器服务

功能：
1. 管理预计算定时任务
2. 每 10 分钟执行一次预计算
3. 支持手动触发

修复说明（M5）：
- 将 BackgroundScheduler 替换为 AsyncIOScheduler（支持 async 任务）
- 在任务内部重新获取 Session，不再复用全局 Session
- 使用 asyncio.to_thread() 包装同步数据库操作
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

from app.models import SessionLocal
from app.services.ip_location_calculator import IPLocationCalculator

# 使用模块级 logger（logging.basicConfig 应在应用入口统一配置）
logger = logging.getLogger(__name__)


class IPLocationScheduler:
    """
    IP 定位调度器服务

    使用 AsyncIOScheduler：
    - 支持 async 任务执行
    - 与 FastAPI 事件循环兼容
    - 避免 Session 生命周期问题
    """

    def __init__(self, interval_minutes: int = 10):
        """
        初始化调度器（不启动）

        Args:
            interval_minutes: 执行间隔（分钟），默认 10 分钟

        注意：不在 __init__ 中启动调度器，应在 lifespan 中启动
        """
        self.interval_minutes = interval_minutes
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None
        self._consecutive_failures: int = 0

        logger.info("IP location scheduler initialized (AsyncIOScheduler, not started)")

    def start(self):
        """
        启动调度器
        """
        if self._is_running:
            logger.warning("IP 定位调度器已在运行中")
            return

        # 添加定时任务（使用 async 方法）
        self.scheduler.add_job(
            func=self._run_calculation_async,  # 直接使用 async 方法
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

    async def _run_calculation_async(self):
        """
        执行预计算（定时任务回调 - 异步版本）

        在任务内部重新获取 Session，完成后关闭
        """
        logger.info("开始执行 IP 定位预计算...")

        # 在任务内部获取 Session
        db = SessionLocal()

        try:
            calculator = IPLocationCalculator(db)
            # 使用 asyncio.to_thread 包装同步操作
            stats = await asyncio.to_thread(calculator.calculate_batch)

            self._last_run = datetime.now()
            self._last_stats = stats

            # 更新失败计数
            matched = stats.get('matched', 0)
            archived = stats.get('archived', 0)

            if matched == 0 and archived == 0:
                self._consecutive_failures += 1
                logger.warning(f"IP 定位预计算无结果，连续失败次数：{self._consecutive_failures}")
            else:
                if self._consecutive_failures > 0:
                    logger.info(f"IP 定位预计算恢复，之前连续失败 {self._consecutive_failures} 次")
                self._consecutive_failures = 0

            logger.info(f"IP 定位预计算完成: 匹配 {matched} 条, "
                       f"归档 {archived} 条, "
                       f"耗时 {stats.get('duration_seconds', 0):.2f} 秒")

        except Exception as e:
            logger.error(f"IP 定位预计算失败: {e}", exc_info=True)
            self._consecutive_failures += 1

        finally:
            # 任务完成后关闭 Session
            db.close()
            logger.debug("Session closed for IP location calculation task")

    async def trigger_now_async(self) -> dict:
        """
        手动触发一次预计算（异步版本）

        Returns:
            计算结果统计
        """
        logger.info("手动触发 IP 定位预计算...")

        # 在任务内部获取 Session
        db = SessionLocal()

        try:
            calculator = IPLocationCalculator(db)
            # 使用 asyncio.to_thread 包装同步操作
            stats = await asyncio.to_thread(calculator.calculate_batch)

            self._last_run = datetime.now()
            self._last_stats = stats

            logger.info(f"手动预计算完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"手动预计算失败: {e}", exc_info=True)
            return {'error': str(e)}

        finally:
            db.close()
            logger.debug("Session closed for manual IP location calculation")

    def trigger_now(self) -> dict:
        """
        手动触发一次预计算（同步兼容接口）

        注意：此方法为向后兼容保留，推荐使用 trigger_now_async

        Returns:
            计算结果统计或错误信息
        """
        logger.warning("trigger_now() 是同步兼容接口，推荐使用 trigger_now_async()")

        # 如果没有运行中的事件循环，直接同步执行
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的事件循环，创建任务
            task = asyncio.create_task(self.trigger_now_async())
            # 注意：无法在同步上下文中等待异步任务完成
            # 调用方应使用 trigger_now_async()
            return {'status': 'scheduled', 'message': '请使用 trigger_now_async() 获取结果'}
        except RuntimeError:
            # 没有运行中的事件循环，使用 asyncio.run
            return asyncio.run(self.trigger_now_async())

    def get_status(self) -> dict:
        """
        获取调度器状态

        Returns:
            状态信息字典
        """
        jobs = self.scheduler.get_jobs() if self._is_running else []
        ip_job = next((j for j in jobs if j.id == 'ip_location_calculation'), None)

        # 计算健康状态
        health_status = "healthy"
        if not self._is_running:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 3:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 1:
            health_status = "degraded"

        return {
            'scheduler': 'ip_location',
            'is_running': self._is_running,
            'interval_minutes': self.interval_minutes,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'last_stats': self._last_stats,
            'next_run': ip_job.next_run_time.isoformat() if ip_job and ip_job.next_run_time else None,
            'consecutive_failures': self._consecutive_failures,
            'health_status': health_status,
            'scheduler_type': 'AsyncIOScheduler',  # 新增：标识调度器类型
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