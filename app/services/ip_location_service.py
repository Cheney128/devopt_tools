"""
IP 定位核心服务
整合 ARP 表和 MAC 地址表，实现 IP 地址定位功能
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.models import Device, ARPEntry, MACAddress
from app.config import settings
from app.services.batch_scheduler import BatchScheduler, randomize_order
from app.services.arp_collector import ARPCollector
from app.services.mac_collector import MACCollector
from app.services.netmiko_service import netmiko_service

logger = logging.getLogger(__name__)


class IPLocationService:
    """IP 定位核心服务"""

    def __init__(self, db: Session):
        self.db = db
        self.arp_collector = ARPCollector(netmiko_service)
        self.mac_collector = MACCollector(netmiko_service)
        self.scheduler = BatchScheduler(
            batch_size=settings.IP_LOCATION_BATCH_SIZE,
            batch_interval=settings.IP_LOCATION_BATCH_INTERVAL_SECONDS,
            max_concurrent=settings.IP_LOCATION_MAX_CONCURRENT
        )
        self._collection_status = {
            "is_running": False,
            "last_run_at": None,
            "last_run_success": True,
            "last_run_message": None,
            "devices_total": 0,
            "devices_completed": 0,
            "devices_failed": 0,
            "arp_entries_collected": 0,
            "mac_entries_collected": 0
        }

    @property
    def collection_status(self) -> Dict[str, Any]:
        return self._collection_status.copy()

    async def collect_from_all_devices(self) -> Dict[str, Any]:
        """从所有设备收集 ARP 和 MAC 表"""
        if self._collection_status["is_running"]:
            return {
                "success": False,
                "message": "收集任务已在运行中"
            }

        # 获取所有活跃设备
        devices = self.db.query(Device).filter(Device.status == "active").all()
        if not devices:
            return {
                "success": False,
                "message": "没有活跃设备"
            }

        self._collection_status.update({
            "is_running": True,
            "devices_total": len(devices),
            "devices_completed": 0,
            "devices_failed": 0,
            "arp_entries_collected": 0,
            "mac_entries_collected": 0
        })

        try:
            # 随机打乱设备顺序
            shuffled_devices = randomize_order(devices)

            async def process_device(device: Device) -> Tuple[int, int]:
                """处理单台设备"""
                try:
                    arp_count = await self._collect_and_save_arp(device)
                    mac_count = await self._collect_and_save_mac(device)
                    return arp_count, mac_count
                except Exception as e:
                    logger.error(f"处理设备 {device.hostname} 失败: {e}")
                    raise

            def progress_callback(completed: int, total: int):
                self._collection_status["devices_completed"] = completed

            # 分批执行
            results, errors = await self.scheduler.run_tasks(
                shuffled_devices,
                process_device,
                progress_callback
            )

            # 统计结果
            total_arp = sum(r[0] for r in results)
            total_mac = sum(r[1] for r in results)

            self._collection_status.update({
                "is_running": False,
                "last_run_at": datetime.now(),
                "last_run_success": len(errors) == 0,
                "last_run_message": f"成功: {len(results)}, 失败: {len(errors)}" if errors else "全部成功",
                "devices_failed": len(errors),
                "arp_entries_collected": total_arp,
                "mac_entries_collected": total_mac
            })

            # 清理旧数据
            self._cleanup_old_data()

            return {
                "success": True,
                "message": "收集完成",
                "arp_entries_collected": total_arp,
                "mac_entries_collected": total_mac,
                "devices_success": len(results),
                "devices_failed": len(errors)
            }

        except Exception as e:
            self._collection_status.update({
                "is_running": False,
                "last_run_at": datetime.now(),
                "last_run_success": False,
                "last_run_message": str(e)
            })
            raise

    async def _collect_and_save_arp(self, device: Device) -> int:
        """收集并保存 ARP 表"""
        entries = await self.arp_collector.collect_from_device(device)
        if not entries:
            return 0

        # 删除该设备的旧 ARP 记录
        self.db.query(ARPEntry).filter(ARPEntry.device_id == device.id).delete()

        # 保存新记录
        now = datetime.now()
        for entry in entries:
            arp_entry = ARPEntry(
                device_id=device.id,
                ip_address=entry["ip_address"],
                mac_address=entry["mac_address"],
                vlan_id=entry.get("vlan_id"),
                interface=entry.get("interface"),
                arp_type=entry.get("arp_type"),
                age_minutes=entry.get("age_minutes"),
                last_seen=now
            )
            self.db.add(arp_entry)

        self.db.commit()
        return len(entries)

    async def _collect_and_save_mac(self, device: Device) -> int:
        """收集并保存 MAC 地址表"""
        entries = await self.mac_collector.collect_from_device(device)
        if not entries:
            return 0

        # 删除该设备的旧 MAC 记录
        self.db.query(MACAddress).filter(MACAddress.device_id == device.id).delete()

        # 保存新记录
        now = datetime.now()
        for entry in entries:
            mac_entry = MACAddress(
                device_id=device.id,
                mac_address=entry["mac_address"],
                vlan_id=entry.get("vlan_id"),
                interface=entry["interface"],
                address_type=entry.get("address_type", "dynamic"),
                is_trunk=entry.get("is_trunk"),
                learned_from=entry.get("learned_from"),
                aging_time=entry.get("aging_time"),
                last_seen=now
            )
            self.db.add(mac_entry)

        self.db.commit()
        return len(entries)

    def _cleanup_old_data(self):
        """清理超过保留期的数据"""
        cutoff_date = datetime.now() - timedelta(days=settings.IP_LOCATION_DATA_RETENTION_DAYS)

        # 清理旧的 ARP 记录
        deleted_arp = self.db.query(ARPEntry).filter(
            ARPEntry.last_seen < cutoff_date
        ).delete()

        # 清理旧的 MAC 记录
        deleted_mac = self.db.query(MACAddress).filter(
            MACAddress.last_seen < cutoff_date
        ).delete()

        self.db.commit()
        logger.info(f"清理旧数据: ARP {deleted_arp} 条, MAC {deleted_mac} 条")

    def locate_ip(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        定位 IP 地址

        逻辑:
        1. 查找最新的 ARP 记录 (IP → MAC)
        2. 查找最新的 MAC 记录 (MAC → 接口)
        3. 组合结果返回
        """
        # 查找该 IP 的最新 ARP 记录
        arp_entries = self.db.query(ARPEntry).filter(
            ARPEntry.ip_address == ip_address
        ).order_by(desc(ARPEntry.last_seen)).limit(10).all()

        if not arp_entries:
            return []

        results = []
        for arp_entry in arp_entries:
            # 查找该 MAC 的最新记录
            mac_entries = self.db.query(MACAddress).filter(
                and_(
                    MACAddress.mac_address == arp_entry.mac_address,
                    MACAddress.device_id == arp_entry.device_id
                )
            ).order_by(desc(MACAddress.last_seen)).limit(5).all()

            device = self.db.query(Device).filter(Device.id == arp_entry.device_id).first()

            if mac_entries:
                for mac_entry in mac_entries:
                    results.append({
                        "ip_address": ip_address,
                        "mac_address": arp_entry.mac_address,
                        "device_id": arp_entry.device_id,
                        "device_hostname": device.hostname if device else "Unknown",
                        "device_ip": device.ip_address if device else "Unknown",
                        "interface": mac_entry.interface,
                        "vlan_id": mac_entry.vlan_id or arp_entry.vlan_id,
                        "last_seen": max(arp_entry.last_seen, mac_entry.last_seen),
                        "confidence": 1.0
                    })
            else:
                # 只有 ARP 记录，没有 MAC 记录
                results.append({
                    "ip_address": ip_address,
                    "mac_address": arp_entry.mac_address,
                    "device_id": arp_entry.device_id,
                    "device_hostname": device.hostname if device else "Unknown",
                    "device_ip": device.ip_address if device else "Unknown",
                    "interface": arp_entry.interface or "Unknown",
                    "vlan_id": arp_entry.vlan_id,
                    "last_seen": arp_entry.last_seen,
                    "confidence": 0.5
                })

        return results

    def get_ip_list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """获取 IP 列表"""
        # 获取最新的 ARP 记录（去重，每个 IP 只保留最新的）
        subquery = self.db.query(
            ARPEntry.ip_address,
            func.max(ARPEntry.last_seen).label("max_last_seen")
        ).group_by(ARPEntry.ip_address).subquery()

        query = self.db.query(ARPEntry).join(
            subquery,
            and_(
                ARPEntry.ip_address == subquery.c.ip_address,
                ARPEntry.last_seen == subquery.c.max_last_seen
            )
        )

        if search:
            query = query.filter(ARPEntry.ip_address.like(f"%{search}%"))

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        arp_entries = query.order_by(desc(ARPEntry.last_seen)).offset(offset).limit(page_size).all()

        # 获取设备信息
        items = []
        for arp_entry in arp_entries:
            device = self.db.query(Device).filter(Device.id == arp_entry.device_id).first()
            items.append({
                "ip_address": arp_entry.ip_address,
                "mac_address": arp_entry.mac_address,
                "device_id": arp_entry.device_id,
                "device_hostname": device.hostname if device else "Unknown",
                "interface": arp_entry.interface or "Unknown",
                "vlan_id": arp_entry.vlan_id,
                "last_seen": arp_entry.last_seen
            })

        return total, items


# 全局服务实例（需要时创建）
_ip_location_service: Optional[IPLocationService] = None


def get_ip_location_service(db: Session) -> IPLocationService:
    """获取 IP 定位服务实例"""
    global _ip_location_service
    # 每次都创建新实例，因为 db session 可能变化
    return IPLocationService(db)
