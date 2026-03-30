# -*- coding: utf-8 -*-
"""
ARP+MAC 批量采集调度器

功能：
1. 定时批量采集所有设备的 ARP 和 MAC 表
2. 采集完成后自动触发 IP 定位预计算
3. 支持事务保护，采集失败时不污染数据
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.models.models import Device
from app.models.ip_location_current import ARPEntry, MACAddressCurrent
from app.services.netmiko_service import get_netmiko_service
from app.services.ip_location_calculator import get_ip_location_calculator

logger = logging.getLogger(__name__)


class ARPMACScheduler:
    """
    ARP+MAC 批量采集调度器
    """

    def __init__(self, db: Optional[Session] = None, interval_minutes: int = 30):
        """
        初始化调度器

        Args:
            db: 数据库会话（可选，可在 start() 时传入）
            interval_minutes: 采集间隔（分钟），默认 30 分钟
        """
        self.db = db
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self._is_running = False
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None
        self._consecutive_failures: int = 0
        self.netmiko = get_netmiko_service() if db else None

    def collect_all_devices(self) -> dict:
        """
        采集所有活跃设备的 ARP 和 MAC 表

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        logger.info(f"开始批量采集 ARP 和 MAC 表，时间：{start_time}")

        # 获取所有活跃设备
        devices = self.db.query(Device).filter(
            Device.status == 'active'
        ).all()

        if not devices:
            logger.warning("没有活跃设备需要采集")
            return {'success': 0, 'failed': 0, 'error': 'No active devices'}

        logger.info(f"共有 {len(devices)} 台设备需要采集")

        # 采集统计
        stats = {
            'arp_success': 0,
            'arp_failed': 0,
            'mac_success': 0,
            'mac_failed': 0,
            'total_arp_entries': 0,
            'total_mac_entries': 0,
            'devices': []
        }

        # 逐个设备采集
        for device in devices:
            device_stats = self._collect_device(device)
            stats['devices'].append(device_stats)
            
            if device_stats['arp_success']:
                stats['arp_success'] += 1
                stats['total_arp_entries'] += device_stats.get('arp_entries_count', 0)
            else:
                stats['arp_failed'] += 1
            
            if device_stats['mac_success']:
                stats['mac_success'] += 1
                stats['total_mac_entries'] += device_stats.get('mac_entries_count', 0)
            else:
                stats['mac_failed'] += 1

        # 记录总耗时
        end_time = datetime.now()
        stats['start_time'] = start_time.isoformat()
        stats['end_time'] = end_time.isoformat()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()

        logger.info(f"批量采集完成：{stats}")
        return stats

    async def _collect_device_async(self, device: Device) -> dict:
        """
        异步采集单个设备的 ARP 和 MAC 表（使用 asyncio.gather 并行采集）

        注意：此方法在独立事件循环中执行，数据库 Session 操作在 asyncio.run() 内部完成。
        SQLAlchemy Session 在同步上下文中创建，但在此异步方法内部仅执行同步数据库操作，
        不涉及异步数据库驱动，因此线程安全。

        Args:
            device: 设备对象

        Returns:
            采集结果字典
        """
        device_stats = {
            'device_id': device.id,
            'device_hostname': device.hostname,
            'arp_success': False,
            'mac_success': False,
            'arp_entries_count': 0,
            'mac_entries_count': 0,
        }

        try:
            # 并行采集 ARP 和 MAC 表
            arp_task = self.netmiko.collect_arp_table(device)
            mac_task = self.netmiko.collect_mac_table(device)

            arp_table, mac_table = await asyncio.gather(
                arp_task,
                mac_task,
                return_exceptions=True
            )

            # 处理 ARP 表 - 使用 UPSERT 策略避免唯一键冲突
            if arp_table and not isinstance(arp_table, Exception):
                batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                now = datetime.now()

                for entry in arp_table:
                    # 使用 MySQL INSERT ... ON DUPLICATE KEY UPDATE (UPSERT)
                    stmt = mysql_insert(ARPEntry).values(
                        ip_address=entry['ip_address'],
                        mac_address=entry['mac_address'],
                        arp_device_id=device.id,
                        vlan_id=entry.get('vlan_id'),
                        arp_interface=entry.get('interface'),
                        last_seen=now,
                        collection_batch_id=batch_id,
                        created_at=now,
                        updated_at=now
                    )
                    # 唯一键: uq_arp_current_ip_device (ip_address + arp_device_id)
                    stmt = stmt.on_duplicate_key_update(
                        mac_address=stmt.inserted.mac_address,
                        vlan_id=stmt.inserted.vlan_id,
                        arp_interface=stmt.inserted.arp_interface,
                        last_seen=stmt.inserted.last_seen,
                        collection_batch_id=stmt.inserted.collection_batch_id,
                        updated_at=func.now()
                    )
                    self.db.execute(stmt)

                device_stats['arp_success'] = True
                device_stats['arp_entries_count'] = len(arp_table)
                logger.info(f"设备 {device.hostname} ARP 采集成功：{len(arp_table)} 条")
            elif isinstance(arp_table, Exception):
                logger.error(f"设备 {device.hostname} ARP 采集失败：{arp_table}")
                device_stats['error'] = str(arp_table)
            else:
                logger.warning(f"设备 {device.hostname} ARP 采集返回空结果")

            # 处理 MAC 表 - 使用 UPSERT 策略避免唯一键冲突
            if mac_table and not isinstance(mac_table, Exception):
                batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                now = datetime.now()

                for entry in mac_table:
                    # 使用 MySQL INSERT ... ON DUPLICATE KEY UPDATE (UPSERT)
                    stmt = mysql_insert(MACAddressCurrent).values(
                        mac_address=entry['mac_address'],
                        mac_device_id=device.id,
                        vlan_id=entry.get('vlan_id'),
                        mac_interface=entry['interface'],
                        is_trunk=entry.get('is_trunk', False),
                        interface_description=entry.get('description'),
                        last_seen=now,
                        collection_batch_id=batch_id,
                        created_at=now,
                        updated_at=now
                    )
                    # 唯一键假设: (mac_address + mac_device_id + mac_interface)
                    stmt = stmt.on_duplicate_key_update(
                        vlan_id=stmt.inserted.vlan_id,
                        is_trunk=stmt.inserted.is_trunk,
                        interface_description=stmt.inserted.interface_description,
                        last_seen=stmt.inserted.last_seen,
                        collection_batch_id=stmt.inserted.collection_batch_id,
                        updated_at=func.now()
                    )
                    self.db.execute(stmt)

                device_stats['mac_success'] = True
                device_stats['mac_entries_count'] = len(mac_table)
                logger.info(f"设备 {device.hostname} MAC 采集成功：{len(mac_table)} 条")
            elif isinstance(mac_table, Exception):
                logger.error(f"设备 {device.hostname} MAC 采集失败：{mac_table}")
                if 'error' not in device_stats:
                    device_stats['error'] = str(mac_table)
            else:
                logger.warning(f"设备 {device.hostname} MAC 采集返回空结果")

            # 提交事务
            self.db.commit()
            logger.debug(f"设备 {device.hostname} 数据库事务提交成功")

        except Exception as e:
            logger.error(f"设备 {device.hostname} 采集失败：{str(e)}", exc_info=True)
            self.db.rollback()
            logger.warning(f"设备 {device.hostname} 数据库事务已回滚")
            device_stats['error'] = str(e)

        return device_stats

    def _run_async(self, coro):
        """
        异步方法运行辅助方法（支持三层降级策略）

        此方法提供多层降级策略：
        1. 优先使用 asyncio.run() 创建独立事件循环
        2. 若检测到已有事件循环，尝试使用 nest_asyncio
        3. 若 nest_asyncio 不可用，在新线程中运行

        Args:
            coro: 异步协程对象

        Returns:
            协程执行结果

        Raises:
            RuntimeError: 若所有方案均失败
        """
        try:
            # 方案 1: 直接使用 asyncio.run()
            return asyncio.run(coro)
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                logger.warning("检测到已有运行的事件循环，尝试降级方案")

                # 方案 2: 使用 nest_asyncio
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                    loop = asyncio.get_running_loop()
                    logger.debug("使用 nest_asyncio 处理嵌套事件循环")
                    return loop.run_until_complete(coro)
                except ImportError:
                    logger.debug("nest_asyncio 未安装，使用线程降级方案")
                except RuntimeError as thread_error:
                    logger.warning(f"nest_asyncio 方案失败：{thread_error}")

                # 方案 3: 在新线程中运行
                import threading
                result = None
                exception = None

                def run_in_thread():
                    nonlocal result, exception
                    try:
                        result = asyncio.run(coro)
                    except Exception as ex:
                        exception = ex

                thread = threading.Thread(target=run_in_thread, name="async_collector")
                thread.start()
                thread.join(timeout=60)  # 设置超时防止无限等待

                if thread.is_alive():
                    logger.error("异步采集线程超时（60秒），强制终止")
                    raise RuntimeError("Async collection thread timeout")

                if exception:
                    raise exception

                logger.debug("线程降级方案执行成功")
                return result
            else:
                # 非嵌套事件循环的 RuntimeError，直接抛出
                logger.error(f"asyncio.run() 执行失败：{e}", exc_info=True)
                raise

    def _collect_device(self, device: Device) -> dict:
        """
        采集单个设备的 ARP 和 MAC 表（同步包装方法）

        此方法为调度器调用的同步入口，内部通过 asyncio.run() 创建独立事件循环执行异步采集。

        Args:
            device: 设备对象

        Returns:
            采集结果字典
        """
        return self._run_async(self._collect_device_async(device))

    def collect_and_calculate(self) -> dict:
        """
        采集 ARP+MAC 并触发 IP 定位计算

        Returns:
            完整结果统计
        """
        logger.info("开始采集 + 计算流程")

        # 步骤 1: 采集 ARP 和 MAC
        collection_stats = self.collect_all_devices()

        if collection_stats.get('arp_success', 0) == 0:
            logger.error("ARP 采集全部失败，跳过 IP 定位计算")
            return {
                'collection': collection_stats,
                'calculation': {'error': 'ARP collection failed'}
            }

        # 步骤 2: 触发 IP 定位计算
        try:
            calculator = get_ip_location_calculator(self.db)
            calculation_stats = calculator.calculate_batch()
            
            logger.info(f"IP 定位计算完成：{calculation_stats}")
            
            return {
                'collection': collection_stats,
                'calculation': calculation_stats
            }
        except Exception as e:
            logger.error(f"IP 定位计算失败：{str(e)}")
            return {
                'collection': collection_stats,
                'calculation': {'error': str(e)}
            }

    def start(self, db: Session = None):
        """
        启动调度器
        
        Args:
            db: 数据库会话（可选，如果初始化时已提供则不需要）
        """
        from app.config import settings
        
        if not settings.ARP_MAC_COLLECTION_ENABLED:
            logger.info("[ARP/MAC] 采集功能已禁用，跳过启动")
            return
        
        if self._is_running:
            logger.warning("ARP/MAC 调度器已在运行中")
            return
        
        # 如果提供了新的 db，更新它
        if db:
            self.db = db
            self.netmiko = get_netmiko_service()
        
        # 启动时立即采集（可配置）
        if settings.ARP_MAC_COLLECTION_ON_STARTUP:
            try:
                logger.info("[ARP/MAC] 启动立即采集...")
                self._run_collection()
                logger.info("[ARP/MAC] 启动立即采集完成")
            except Exception as e:
                logger.error(f"[ARP/MAC] 启动立即采集失败：{e}", exc_info=True)
        
        # 添加定时任务
        self.scheduler.add_job(
            func=self._run_collection,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='arp_mac_collection',
            name='ARP/MAC 自动采集',
            replace_existing=True,
            misfire_grace_time=600  # 允许 10 分钟的错过执行宽限期
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info(f"[ARP/MAC] 调度器已启动，间隔：{self.interval_minutes} 分钟")

    def shutdown(self):
        """
        关闭调度器
        """
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("ARP/MAC 调度器已关闭")

    def _run_collection(self):
        """
        执行采集（定时任务回调）
        """
        logger.info("开始执行 ARP/MAC 采集...")
        
        try:
            stats = self.collect_and_calculate()
            
            self._last_run = datetime.now()
            self._last_stats = stats
            
            # 更新失败计数
            collection = stats.get('collection', {})
            arp_success = collection.get('arp_success', 0)
            arp_failed = collection.get('arp_failed', 0)
            
            if arp_success == 0 and arp_failed > 0:
                self._consecutive_failures += 1
                logger.warning(f"ARP/MAC 采集失败，连续失败次数：{self._consecutive_failures}")
            else:
                if self._consecutive_failures > 0:
                    logger.info(f"ARP/MAC 采集恢复，之前连续失败 {self._consecutive_failures} 次")
                self._consecutive_failures = 0
            
            logger.info(f"ARP/MAC 采集完成：成功 {arp_success} 台，失败 {arp_failed} 台")
            
        except Exception as e:
            logger.error(f"ARP/MAC 采集异常：{e}", exc_info=True)
            self._consecutive_failures += 1

    def get_status(self) -> dict:
        """
        获取调度器状态

        Returns:
            状态信息字典
        """
        jobs = self.scheduler.get_jobs() if self._is_running else []
        arp_job = next((j for j in jobs if j.id == 'arp_mac_collection'), None)
        
        # 计算健康状态
        health_status = "healthy"
        if not self._is_running:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 3:
            health_status = "unhealthy"
        elif self._consecutive_failures >= 1:
            health_status = "degraded"
        
        return {
            'scheduler': 'arp_mac',
            'is_running': self._is_running,
            'interval_minutes': self.interval_minutes,
            'last_run': self._last_run.isoformat() if self._last_run else None,
            'last_stats': self._last_stats,
            'next_run': arp_job.next_run_time.isoformat() if arp_job and arp_job.next_run_time else None,
            'consecutive_failures': self._consecutive_failures,
            'health_status': health_status,
        }


def get_arp_mac_scheduler(db: Session) -> ARPMACScheduler:
    """
    获取 ARP+MAC 调度器实例

    Args:
        db: 数据库会话

    Returns:
        调度器实例
    """
    return ARPMACScheduler(db)


# 创建全局调度器实例（db 将在 start() 时传入）
arp_mac_scheduler = ARPMACScheduler(db=None, interval_minutes=30)
