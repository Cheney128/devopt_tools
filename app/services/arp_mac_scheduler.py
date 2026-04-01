# -*- coding: utf-8 -*-
"""
ARP+MAC 批量采集调度器

功能：
1. 定时批量采集所有设备的 ARP 和 MAC 表
2. 采集完成后自动触发 IP 定位预计算
3. 支持事务保护，采集失败时不污染数据

修复说明（M3）：
- 将 BackgroundScheduler 替换为 AsyncIOScheduler（支持 async 任务）
- 移除 _run_async 三层降级逻辑，直接使用 async 方法
- 在任务内部重新获取 Session，不再复用全局 Session
- 使用 asyncio.to_thread() 包装同步数据库操作
- start() 方法不再需要 db 参数
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.models import SessionLocal
from app.models.models import Device
from app.models.ip_location_current import ARPEntry, MACAddressCurrent
from app.services.netmiko_service import get_netmiko_service
from app.services.ip_location_calculator import get_ip_location_calculator

logger = logging.getLogger(__name__)

# 二次验证正则（标准化后的格式）
IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
MAC_PATTERN = re.compile(r'^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$')


def validate_arp_entry(entry: dict) -> bool:
    """
    二次验证 ARP 条目数据完整性

    Args:
        entry: ARP 条目字典

    Returns:
        True: 数据有效，False: 数据无效
    """
    required_fields = ['ip_address', 'mac_address']
    for field in required_fields:
        if not entry.get(field):
            logger.warning(f"[ARP 验证] 缺少必要字段: {field}")
            return False

    # IP 格式检查
    if not IP_PATTERN.match(entry['ip_address']):
        logger.warning(f"[ARP 验证] 无效 IP 格式: {entry['ip_address']}")
        return False

    # MAC 格式检查（冒号分隔，已标准化）
    if not MAC_PATTERN.match(entry['mac_address']):
        logger.warning(f"[ARP 验证] 无效 MAC 格式: {entry['mac_address']}")
        return False

    return True




def validate_arp_entry(entry: dict) -> bool:
    """
    二次验证 ARP 条目数据完整性

    Args:
        entry: ARP 条目字典

    Returns:
        True: 数据有效，False: 数据无效
    """
    from loguru import logger
    
    required_fields = ['ip_address', 'mac_address']
    for field in required_fields:
        if not entry.get(field):
            logger.warning(f"[ARP 验证] 缺少必要字段：{field}")
            return False

    # IP 格式检查
    IP_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    if not IP_PATTERN.match(entry['ip_address']):
        logger.warning(f"[ARP 验证] 无效 IP 格式：{entry['ip_address']}")
        return False

    # MAC 格式检查（冒号分隔，已标准化）
    MAC_PATTERN = re.compile(r'^[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}$')
    if not MAC_PATTERN.match(entry['mac_address']):
        logger.warning(f"[ARP 验证] 无效 MAC 格式：{entry['mac_address']}")
        return False

    return True


class ARPMACScheduler:
    """
    ARP+MAC 批量采集调度器

    使用 AsyncIOScheduler：
    - 支持 async 任务执行
    - 与 FastAPI 事件循环兼容
    - 避免 Session 生命周期问题
    """

    def __init__(self, interval_minutes: int = 30):
        """
        初始化调度器（不启动）

        Args:
            interval_minutes: 采集间隔（分钟），默认 30 分钟

        注意：不在 __init__ 中启动调度器，应在 lifespan 中启动
        """
        self.interval_minutes = interval_minutes
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        self._last_run: Optional[datetime] = None
        self._last_stats: Optional[dict] = None
        self._consecutive_failures: int = 0

        logger.info("ARP/MAC scheduler initialized (AsyncIOScheduler, not started)")

    def start(self, db: Optional[Session] = None):
        """
        启动调度器

        Args:
            db: 数据库会话（已废弃参数，保留用于兼容性）

        注意：
            不再使用 db 参数，任务执行时会在内部重新获取 Session
        """
        from app.config import settings

        if not settings.ARP_MAC_COLLECTION_ENABLED:
            logger.info("[ARP/MAC] 采集功能已禁用，跳过启动")
            return

        if self._is_running:
            logger.warning("ARP/MAC 调度器已在运行中")
            return

        # 启动时立即采集（可配置）
        if settings.ARP_MAC_COLLECTION_ON_STARTUP:
            try:
                logger.info("[ARP/MAC] 启动立即采集...")
                # 直接调用 async 方法
                asyncio.create_task(self._run_collection_async())
                logger.info("[ARP/MAC] 启动立即采集已触发")
            except Exception as e:
                logger.error(f"[ARP/MAC] 启动立即采集失败：{e}", exc_info=True)

        # 添加定时任务（使用 async 方法）
        self.scheduler.add_job(
            func=self._run_collection_async,  # 直接使用 async 方法
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

    async def _run_collection_async(self):
        """
        执行采集（定时任务回调 - 异步版本）

        在任务内部重新获取 Session，完成后关闭
        """
        logger.info("开始执行 ARP/MAC 采集...")

        try:
            stats = await self.collect_and_calculate_async()

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

    async def collect_and_calculate_async(self) -> dict:
        """
        采集 ARP+MAC 并触发 IP 定位计算（异步版本）

        在任务内部获取 Session，完成后关闭

        Returns:
            完整结果统计
        """
        logger.info("开始采集 + 计算流程")

        # 在任务内部获取 Session
        db = SessionLocal()

        try:
            # 步骤 1: 采集 ARP 和 MAC
            collection_stats = await self.collect_all_devices_async(db)

            if collection_stats.get('arp_success', 0) == 0:
                logger.error("ARP 采集全部失败，跳过 IP 定位计算")
                return {
                    'collection': collection_stats,
                    'calculation': {'error': 'ARP collection failed'}
                }

            # 步骤 2: 触发 IP 定位计算（使用 asyncio.to_thread 包装同步操作）
            try:
                calculator = get_ip_location_calculator(db)
                calculation_stats = await asyncio.to_thread(calculator.calculate_batch)

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

        finally:
            # 任务完成后关闭 Session
            db.close()
            logger.debug("Session closed for ARP/MAC collection task")

    async def collect_all_devices_async(self, db: Session) -> dict:
        """
        异步采集所有活跃设备的 ARP 和 MAC 表

        Args:
            db: 数据库会话（由调用方提供）

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        logger.info(f"开始批量采集 ARP 和 MAC 表，时间：{start_time}")

        # 获取所有活跃设备（使用 asyncio.to_thread 包装同步查询）
        devices = await asyncio.to_thread(
            lambda: db.query(Device).filter(Device.status == 'active').all()
        )

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

        # 获取 netmiko 服务
        netmiko = get_netmiko_service()

        # 逐个设备采集
        for device in devices:
            device_stats = await self._collect_device_async(device, db, netmiko)
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

    async def _collect_device_async(self, device: Device, db: Session, netmiko) -> dict:
        """
        异步采集单个设备的 ARP 和 MAC 表

        Args:
            device: 设备对象
            db: 数据库会话
            netmiko: Netmiko 服务实例

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
            arp_task = netmiko.collect_arp_table(device)
            mac_task = netmiko.collect_mac_table(device)

            arp_table, mac_table = await asyncio.gather(
                arp_task,
                mac_task,
                return_exceptions=True
            )

            # 处理 ARP 表 - 使用 UPSERT 策略避免唯一键冲突
            if arp_table and not isinstance(arp_table, Exception):
                batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
                now = datetime.now()

                # 二次数据验证
                valid_entries = [e for e in arp_table if validate_arp_entry(e)]
                invalid_count = len(arp_table) - len(valid_entries)
                if invalid_count > 0:
                    logger.warning(f"[ARP 采集] 设备 {device.hostname} 过滤无效条目：{invalid_count} 条")
                logger.info(f"[ARP 采集] 设备 {device.hostname} 有效条目：{len(valid_entries)}/{len(arp_table)}")

                for entry in valid_entries:
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
                    db.execute(stmt)

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
                    db.execute(stmt)

                device_stats['mac_success'] = True
                device_stats['mac_entries_count'] = len(mac_table)
                logger.info(f"设备 {device.hostname} MAC 采集成功：{len(mac_table)} 条")
            elif isinstance(mac_table, Exception):
                logger.error(f"设备 {device.hostname} MAC 采集失败：{mac_table}")
                if 'error' not in device_stats:
                    device_stats['error'] = str(mac_table)
            else:
                logger.warning(f"设备 {device.hostname} MAC 采集返回空结果")

            # 提交事务（使用 asyncio.to_thread 包装同步操作）
            await asyncio.to_thread(db.commit)
            logger.debug(f"设备 {device.hostname} 数据库事务提交成功")

        except Exception as e:
            logger.error(f"设备 {device.hostname} 采集失败：{str(e)}", exc_info=True)
            await asyncio.to_thread(db.rollback)
            logger.warning(f"设备 {device.hostname} 数据库事务已回滚")
            device_stats['error'] = str(e)

        return device_stats

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
            'scheduler_type': 'AsyncIOScheduler',  # 新增：标识调度器类型
        }


# 创建全局调度器实例（不再传 db）
arp_mac_scheduler = ARPMACScheduler(interval_minutes=30)