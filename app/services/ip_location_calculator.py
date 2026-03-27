# -*- coding: utf-8 -*-
"""
IP 定位预计算服务

功能：
1. 批量加载 ARP、MAC、设备数据
2. 预计算 IP 定位结果
3. 冗余设备信息避免 N+1 查询
4. 下线检测与历史归档
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from decimal import Decimal
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.models import Device
from app.models.ip_location import IPLocationCurrent, IPLocationHistory, IPLocationSettings

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ARPEntry:
    """ARP 条目数据类"""
    ip_address: str
    mac_address: str
    arp_device_id: int
    vlan_id: Optional[int] = None
    arp_interface: Optional[str] = None
    last_seen: Optional[datetime] = None


@dataclass
class MACEntry:
    """MAC 条目数据类"""
    mac_address: str
    mac_device_id: int
    mac_interface: str
    vlan_id: Optional[int] = None
    is_trunk: bool = False
    interface_description: Optional[str] = None
    last_seen: Optional[datetime] = None


@dataclass
class DeviceInfo:
    """设备信息数据类（用于缓存）"""
    id: int
    hostname: str
    ip_address: str
    location: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None


@dataclass
class CalculationResult:
    """计算结果数据类"""
    ip_address: str
    mac_address: str
    arp_source_device_id: int
    mac_hit_device_id: Optional[int]
    access_interface: Optional[str]
    vlan_id: Optional[int]
    confidence: Decimal
    is_uplink: bool
    is_core_switch: bool
    match_type: str
    last_seen: datetime

    # 冗余设备信息
    arp_device_hostname: Optional[str] = None
    arp_device_ip: Optional[str] = None
    arp_device_location: Optional[str] = None
    mac_device_hostname: Optional[str] = None
    mac_device_ip: Optional[str] = None
    mac_device_location: Optional[str] = None


class IPLocationCalculator:
    """
    IP 定位预计算服务

    通过批量加载和预计算，将查询从 O(N) 优化到 O(1)。
    """

    # 核心交换机标识关键词
    CORE_SWITCH_KEYWORDS = ['core', '核心', 'CORE', 'Core']
    # 上行链路接口关键词
    UPLINK_KEYWORDS = ['uplink', '上行', 'Uplink', 'Eth-Trunk', 'Aggregate']

    def __init__(self, db: Session):
        """
        初始化计算器

        Args:
            db: 数据库会话
        """
        self.db = db
        self._device_cache: Dict[int, DeviceInfo] = {}
        self._arp_entries: List[ARPEntry] = []
        self._mac_entries: List[MACEntry] = []
        self._batch_id: str = ""
        self._settings: Dict[str, str] = {}

    def _load_settings(self) -> Dict[str, str]:
        """
        加载系统配置

        Returns:
            配置字典
        """
        settings = {}

        # 从数据库加载
        db_settings = self.db.query(IPLocationSettings).all()
        for s in db_settings:
            settings[s.key] = s.value

        # 使用默认值填充缺失配置
        for key, default in IPLocationSettings.DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = default

        self._settings = settings
        return settings

    def _load_devices(self) -> Dict[int, DeviceInfo]:
        """
        批量加载设备信息到缓存

        Returns:
            设备 ID -> 设备信息的映射
        """
        logger.info("加载设备信息...")

        devices = self.db.query(Device).all()
        cache = {}

        for d in devices:
            cache[d.id] = DeviceInfo(
                id=d.id,
                hostname=d.hostname,
                ip_address=d.ip_address,
                location=d.location,
                vendor=d.vendor,
                model=d.model
            )

        self._device_cache = cache
        logger.info(f"已加载 {len(cache)} 台设备信息")
        return cache

    def _load_arp_entries(self) -> List[ARPEntry]:
        """
        批量加载 ARP 当前数据

        Returns:
            ARP 条目列表
        """
        logger.info("加载 ARP 数据...")

        sql = text("""
            SELECT ip_address, mac_address, arp_device_id, vlan_id,
                   arp_interface, last_seen
            FROM arp_current
            WHERE mac_address IS NOT NULL AND mac_address != ''
            ORDER BY last_seen DESC
        """)

        result = self.db.execute(sql)
        entries = []

        seen_ips = set()  # 去重：每个 IP 只保留最新记录

        for row in result:
            ip = row.ip_address
            if ip in seen_ips:
                continue
            seen_ips.add(ip)

            entries.append(ARPEntry(
                ip_address=row.ip_address,
                mac_address=row.mac_address,
                arp_device_id=row.arp_device_id,
                vlan_id=row.vlan_id,
                arp_interface=row.arp_interface,
                last_seen=row.last_seen
            ))

        self._arp_entries = entries
        logger.info(f"已加载 {len(entries)} 条 ARP 记录")
        return entries

    def _load_mac_entries(self) -> Dict[str, List[MACEntry]]:
        """
        批量加载 MAC 当前数据

        Returns:
            MAC 地址 -> MAC 条目列表的映射
        """
        logger.info("加载 MAC 数据...")

        sql = text("""
            SELECT mac_address, mac_device_id, mac_interface, vlan_id,
                   is_trunk, interface_description, last_seen
            FROM mac_current
            ORDER BY last_seen DESC
        """)

        result = self.db.execute(sql)
        mac_map: Dict[str, List[MACEntry]] = {}

        for row in result:
            mac = row.mac_address.upper()
            if mac not in mac_map:
                mac_map[mac] = []

            mac_map[mac].append(MACEntry(
                mac_address=mac,
                mac_device_id=row.mac_device_id,
                mac_interface=row.mac_interface,
                vlan_id=row.vlan_id,
                is_trunk=bool(row.is_trunk),
                interface_description=row.interface_description,
                last_seen=row.last_seen
            ))

        self._mac_entries = []
        for entries in mac_map.values():
            self._mac_entries.extend(entries)

        logger.info(f"已加载 {len(mac_map)} 个 MAC 地址，共 {len(self._mac_entries)} 条记录")
        return mac_map

    def _is_core_switch(self, device_info: Optional[DeviceInfo]) -> bool:
        """
        判断是否为核心交换机

        Args:
            device_info: 设备信息

        Returns:
            是否为核心交换机
        """
        if not device_info:
            return False

        hostname = device_info.hostname or ''
        for keyword in self.CORE_SWITCH_KEYWORDS:
            if keyword in hostname:
                return True

        return False

    def _is_uplink_interface(self, interface: Optional[str]) -> bool:
        """
        判断是否为上行链路接口

        Args:
            interface: 接口名称

        Returns:
            是否为上行链路
        """
        if not interface:
            return False

        for keyword in self.UPLINK_KEYWORDS:
            if keyword in interface:
                return True

        return False

    def _calculate_confidence(
        self,
        arp_entry: ARPEntry,
        mac_entry: MACEntry,
        is_same_vlan: bool
    ) -> Decimal:
        """
        计算定位置信度

        Args:
            arp_entry: ARP 条目
            mac_entry: MAC 条目
            is_same_vlan: VLAN 是否一致

        Returns:
            置信度 (0.00 - 1.00)
        """
        confidence = Decimal('0.50')  # 基础置信度

        # VLAN 匹配加分
        if is_same_vlan and arp_entry.vlan_id and mac_entry.vlan_id:
            if arp_entry.vlan_id == mac_entry.vlan_id:
                confidence += Decimal('0.20')

        # 非 trunk 接口加分
        if not mac_entry.is_trunk:
            confidence += Decimal('0.15')

        # 有接口描述加分
        if mac_entry.interface_description:
            confidence += Decimal('0.10')

        # 时间新鲜度加分
        if mac_entry.last_seen and arp_entry.last_seen:
            time_diff = abs((mac_entry.last_seen - arp_entry.last_seen).total_seconds())
            if time_diff < 3600:  # 1 小时内
                confidence += Decimal('0.05')

        # 限制最大值
        return min(confidence, Decimal('1.00'))

    def _match_mac_to_arp(
        self,
        arp_entry: ARPEntry,
        mac_map: Dict[str, List[MACEntry]]
    ) -> Tuple[Optional[MACEntry], str]:
        """
        匹配 MAC 地址表条目

        Args:
            arp_entry: ARP 条目
            mac_map: MAC 地址映射

        Returns:
            (匹配的 MAC 条目, 匹配类型)
        """
        mac = arp_entry.mac_address.upper()
        mac_entries = mac_map.get(mac, [])

        if not mac_entries:
            return None, 'no_mac_found'

        if len(mac_entries) == 1:
            return mac_entries[0], 'single_match'

        # 多个匹配：选择最佳匹配
        best_entry = None
        best_score = -1

        for entry in mac_entries:
            score = 0

            # VLAN 匹配优先
            if arp_entry.vlan_id and entry.vlan_id:
                if arp_entry.vlan_id == entry.vlan_id:
                    score += 10

            # 非 trunk 接口优先
            if not entry.is_trunk:
                score += 5

            # 最新记录优先
            if entry.last_seen:
                score += 1

            if score > best_score:
                best_score = score
                best_entry = entry

        return best_entry, 'cross_device'

    def _fill_device_redundancy(
        self,
        result: CalculationResult,
        arp_entry: ARPEntry,
        mac_entry: Optional[MACEntry]
    ) -> None:
        """
        填充冗余设备信息

        Args:
            result: 计算结果
            arp_entry: ARP 条目
            mac_entry: MAC 条目
        """
        # ARP 来源设备信息
        arp_device = self._device_cache.get(arp_entry.arp_device_id)
        if arp_device:
            result.arp_device_hostname = arp_device.hostname
            result.arp_device_ip = arp_device.ip_address
            result.arp_device_location = arp_device.location

        # MAC 命中设备信息
        if mac_entry and mac_entry.mac_device_id:
            mac_device = self._device_cache.get(mac_entry.mac_device_id)
            if mac_device:
                result.mac_device_hostname = mac_device.hostname
                result.mac_device_ip = mac_device.ip_address
                result.mac_device_location = mac_device.location

    def calculate_batch(self) -> Dict:
        """
        执行批量预计算

        Returns:
            计算结果统计
        """
        start_time = datetime.now()
        self._batch_id = f"batch_{start_time.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(f"开始 IP 定位预计算，批次 ID: {self._batch_id}")

        # 加载配置
        self._load_settings()

        # 批量加载数据
        device_cache = self._load_devices()
        arp_entries = self._load_arp_entries()
        mac_map = self._load_mac_entries()

        # 计算结果
        results: List[CalculationResult] = []
        stats = {
            'total_arp': len(arp_entries),
            'matched': 0,
            'no_mac_found': 0,
            'single_match': 0,
            'cross_device': 0,
        }

        # 遍历 ARP 条目进行匹配
        for arp_entry in arp_entries:
            mac_entry, match_type = self._match_mac_to_arp(arp_entry, mac_map)

            if not mac_entry:
                stats['no_mac_found'] += 1
                continue

            # 计算置信度
            is_same_vlan = (
                arp_entry.vlan_id and mac_entry.vlan_id and
                arp_entry.vlan_id == mac_entry.vlan_id
            )
            confidence = self._calculate_confidence(arp_entry, mac_entry, is_same_vlan)

            # 判断设备和接口属性
            mac_device = device_cache.get(mac_entry.mac_device_id) if mac_entry else None
            is_core = self._is_core_switch(mac_device)
            is_uplink = self._is_uplink_interface(mac_entry.mac_interface)

            # 确定最后发现时间
            last_seen = arp_entry.last_seen or start_time
            if mac_entry.last_seen and mac_entry.last_seen > last_seen:
                last_seen = mac_entry.last_seen

            # 创建结果
            result = CalculationResult(
                ip_address=arp_entry.ip_address,
                mac_address=arp_entry.mac_address,
                arp_source_device_id=arp_entry.arp_device_id,
                mac_hit_device_id=mac_entry.mac_device_id if mac_entry else None,
                access_interface=mac_entry.mac_interface if mac_entry else None,
                vlan_id=arp_entry.vlan_id or (mac_entry.vlan_id if mac_entry else None),
                confidence=confidence,
                is_uplink=is_uplink,
                is_core_switch=is_core,
                match_type=match_type,
                last_seen=last_seen
            )

            # 填充冗余设备信息
            self._fill_device_redundancy(result, arp_entry, mac_entry)

            results.append(result)
            stats['matched'] += 1
            stats[match_type] = stats.get(match_type, 0) + 1

        # 保存到数据库
        self._save_results(results)

        # 归档下线 IP
        archived = self._archive_offline_ips()

        # 清理过期历史
        cleaned = self._cleanup_history()

        # 更新统计
        end_time = datetime.now()
        stats.update({
            'batch_id': self._batch_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'archived': archived,
            'history_cleaned': cleaned,
        })

        logger.info(f"预计算完成: {stats}")
        return stats

    def _save_results(self, results: List[CalculationResult]) -> int:
        """
        保存计算结果到数据库

        Args:
            results: 计算结果列表

        Returns:
            保存的记录数
        """
        if not results:
            return 0

        logger.info(f"保存 {len(results)} 条计算结果...")

        # 使用批量 upsert
        for result in results:
            # 检查是否已存在
            existing = self.db.query(IPLocationCurrent).filter(
                IPLocationCurrent.ip_address == result.ip_address,
                IPLocationCurrent.mac_address == result.mac_address
            ).first()

            if existing:
                # 更新现有记录
                existing.arp_source_device_id = result.arp_source_device_id
                existing.mac_hit_device_id = result.mac_hit_device_id
                existing.access_interface = result.access_interface
                existing.vlan_id = result.vlan_id
                existing.confidence = result.confidence
                existing.is_uplink = result.is_uplink
                existing.is_core_switch = result.is_core_switch
                existing.match_type = result.match_type
                existing.last_seen = result.last_seen
                existing.calculated_at = datetime.now()
                existing.calculate_batch_id = self._batch_id
                existing.batch_status = 'active'

                # 更新冗余字段
                existing.arp_device_hostname = result.arp_device_hostname
                existing.arp_device_ip = result.arp_device_ip
                existing.arp_device_location = result.arp_device_location
                existing.mac_device_hostname = result.mac_device_hostname
                existing.mac_device_ip = result.mac_device_ip
                existing.mac_device_location = result.mac_device_location
            else:
                # 创建新记录
                new_record = IPLocationCurrent(
                    ip_address=result.ip_address,
                    mac_address=result.mac_address,
                    arp_source_device_id=result.arp_source_device_id,
                    mac_hit_device_id=result.mac_hit_device_id,
                    access_interface=result.access_interface,
                    vlan_id=result.vlan_id,
                    confidence=result.confidence,
                    is_uplink=result.is_uplink,
                    is_core_switch=result.is_core_switch,
                    match_type=result.match_type,
                    last_seen=result.last_seen,
                    calculated_at=datetime.now(),
                    calculate_batch_id=self._batch_id,
                    batch_status='active',
                    arp_device_hostname=result.arp_device_hostname,
                    arp_device_ip=result.arp_device_ip,
                    arp_device_location=result.arp_device_location,
                    mac_device_hostname=result.mac_device_hostname,
                    mac_device_ip=result.mac_device_ip,
                    mac_device_location=result.mac_device_location
                )
                self.db.add(new_record)

        self.db.commit()
        logger.info(f"已保存 {len(results)} 条记录")
        return len(results)

    def _archive_offline_ips(self) -> int:
        """
        归档下线的 IP

        两级验证逻辑：
        1. calculated_at 超过阈值（30 分钟未重新计算）
        2. 且不在当前 ARP 表中（设备真正下线）

        注意：此方法在 _save_results() 之后调用，刚计算的记录
        calculated_at 为当前时间，不会被步骤 1 筛选。

        Returns:
            归档的记录数
        """
        threshold_minutes = int(self._settings.get('offline_threshold_minutes', '30'))
        threshold_time = datetime.now() - timedelta(minutes=threshold_minutes)

        logger.info(f"检测下线 IP，阈值: {threshold_minutes} 分钟，截止时间: {threshold_time}")

        # 步骤 1：按 calculated_at 筛选候选记录（修正：使用 calculated_at 替代 last_seen）
        candidate_records = self.db.query(IPLocationCurrent).filter(
            IPLocationCurrent.calculated_at < threshold_time
        ).all()

        if not candidate_records:
            logger.info("没有需要归档的候选记录")
            return 0

        # 步骤 2：获取当前 ARP 表中的所有 IP
        # 优化：复用已加载的 self._arp_entries，避免重复查询数据库
        # 注意：_load_arp_entries() 在 calculate_batch() 中已调用
        current_ips = {entry.ip_address for entry in self._arp_entries}

        # 步骤 3：筛选出真正下线的 IP（不在当前 ARP 表中）
        offline_records = [
            record for record in candidate_records
            if record.ip_address not in current_ips
        ]

        if not offline_records:
            logger.info(f"候选记录 {len(candidate_records)} 条均在 ARP 表中，无需归档")
            return 0

        logger.info(f"发现 {len(offline_records)} 条下线 IP 记录，开始归档...")

        # 步骤 4：移动到历史表
        for record in offline_records:
            history = IPLocationHistory(
                ip_address=record.ip_address,
                mac_address=record.mac_address,
                arp_source_device_id=record.arp_source_device_id,
                arp_device_hostname=record.arp_device_hostname,
                arp_device_ip=record.arp_device_ip,
                arp_device_location=record.arp_device_location,
                mac_hit_device_id=record.mac_hit_device_id,
                mac_device_hostname=record.mac_device_hostname,
                mac_device_ip=record.mac_device_ip,
                mac_device_location=record.mac_device_location,
                access_interface=record.access_interface,
                vlan_id=record.vlan_id,
                confidence=record.confidence,
                is_uplink=record.is_uplink,
                is_core_switch=record.is_core_switch,
                match_type=record.match_type,
                first_seen=record.calculated_at,  # 使用 calculated_at 作为 first_seen
                last_seen=record.last_seen,
                archived_at=datetime.now()
            )
            self.db.add(history)
            self.db.delete(record)

        self.db.commit()
        logger.info(f"已归档 {len(offline_records)} 条下线 IP 记录")
        return len(offline_records)

    def _cleanup_history(self) -> int:
        """
        清理过期的历史记录

        Returns:
            删除的记录数
        """
        retention_days = int(self._settings.get('history_retention_days', '30'))
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        logger.info(f"清理历史记录，保留天数: {retention_days}，截止日期: {cutoff_date}")

        deleted = self.db.query(IPLocationHistory).filter(
            IPLocationHistory.archived_at < cutoff_date
        ).delete()

        self.db.commit()
        logger.info(f"已清理 {deleted} 条过期历史记录")
        return deleted


def get_ip_location_calculator(db: Session) -> IPLocationCalculator:
    """
    获取 IP 定位计算器实例

    Args:
        db: 数据库会话

    Returns:
        计算器实例
    """
    return IPLocationCalculator(db)