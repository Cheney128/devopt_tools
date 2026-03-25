# -*- coding: utf-8 -*-
"""
IP 定位快照服务

提供 IP 定位结果的批次管理功能，支持批次激活、回滚和查询。

功能：
- 批次管理：创建新批次、激活候选批次、回滚到历史批次
- 快照构建：基于 ARP 和 MAC 数据构建 IP 定位快照
- 增量更新：支持全量和增量快照构建
- 查询服务：按 IP 地址查询定位结果，支持分页和筛选
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.models.models import ARPEntry, MACAddress, Device, IPLocationCurrent
from app.services.confidence_calculator import ConfidenceCalculator
from app.services.interface_recognizer import InterfaceRecognizer
from app.services.core_switch_recognizer import CoreSwitchRecognizer
from app.services.ip_location_config_manager import IPLocationConfigManager


class IPLocationSnapshotService:
    """
    IP 定位快照服务

    管理 IP 定位结果的批次，支持事务性的批次切换操作。
    """

    def __init__(self, db: Session):
        """
        初始化快照服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.config_manager = IPLocationConfigManager(db)
        self.config = self.config_manager.get_config_dict_for_service()

    def _new_batch_id(self) -> str:
        """
        生成新的批次 ID

        Returns:
            批次 ID，格式：batch_YYYYMMDDHHMMSS_<8 位随机 hex>
        """
        return f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

    def get_active_batch_id(self) -> Optional[str]:
        """
        获取当前激活的批次 ID

        Returns:
            激活的批次 ID，如果没有则返回 None
        """
        row = self.db.query(IPLocationCurrent.calculate_batch_id).filter(
            IPLocationCurrent.batch_status == "active"
        ).order_by(desc(IPLocationCurrent.calculated_at)).first()
        return row[0] if row else None

    def activate_batch(self, batch_id: str) -> None:
        """
        激活候选批次，同时将旧批次标记为回滚

        使用事务确保两次 UPDATE 操作的原子性：
        1. 将当前 active 批次标记为 rolled_back
        2. 将指定批次标记为 active

        如果过程中发生异常，事务会自动回滚，保证数据一致性。

        Args:
            batch_id: 要激活的批次 ID

        Raises:
            Exception: 数据库操作异常时会抛出，事务自动回滚

        Examples:
            >>> service = IPLocationSnapshotService(db)
            >>> service.activate_batch("batch_20260326120000_abc123")
        """
        # 使用上下文管理器确保事务性：异常自动回滚，成功自动提交
        with self.db.begin():
            # 第一次 UPDATE：将旧批次设为 rolled_back
            self.db.query(IPLocationCurrent).filter(
                and_(
                    IPLocationCurrent.batch_status == "active",
                    IPLocationCurrent.calculate_batch_id != batch_id
                )
            ).update({"batch_status": "rolled_back"}, synchronize_session=False)

            # 第二次 UPDATE：将新批次设为 active
            self.db.query(IPLocationCurrent).filter(
                IPLocationCurrent.calculate_batch_id == batch_id
            ).update({"batch_status": "active"}, synchronize_session=False)

    def rollback_to_batch(self, batch_id: str) -> bool:
        """
        回滚到指定的历史批次

        Args:
            batch_id: 目标批次 ID（必须是已存在的历史批次）

        Returns:
            是否成功回滚

        Examples:
            >>> success = service.rollback_to_batch("batch_20260326100000_xyz789")
            >>> if success:
            ...     print(f"已回滚到批次：{batch_id}")
        """
        exists = self.db.query(IPLocationCurrent.id).filter(
            IPLocationCurrent.calculate_batch_id == batch_id
        ).first()
        if not exists:
            return False
        self.activate_batch(batch_id)
        return True

    def _latest_arp_entries(self, changed_ips: Optional[List[str]] = None) -> List[ARPEntry]:
        """
        获取最新的 ARP 条目（每个 IP 地址一条最新记录）

        Args:
            changed_ips: 可选，限定只获取指定 IP 列表的最新记录

        Returns:
            最新 ARP 条目列表
        """
        subquery = self.db.query(
            ARPEntry.ip_address,
            func.max(ARPEntry.last_seen).label("max_last_seen")
        ).group_by(ARPEntry.ip_address)
        if changed_ips:
            subquery = subquery.filter(ARPEntry.ip_address.in_(changed_ips))
        subquery = subquery.subquery()
        return self.db.query(ARPEntry).join(
            subquery,
            and_(
                ARPEntry.ip_address == subquery.c.ip_address,
                ARPEntry.last_seen == subquery.c.max_last_seen
            )
        ).all()

    def _build_candidates(self, arp_entry: ARPEntry, max_candidates: int = 3) -> List[Dict[str, Any]]:
        """
        为单个 ARP 条目构建定位候选列表

        Args:
            arp_entry: ARP 条目
            max_candidates: 最大返回候选数，默认 3

        Returns:
            定位候选列表，按可信度降序排序
        """
        candidates = self.db.query(MACAddress).filter(
            MACAddress.mac_address == arp_entry.mac_address
        ).order_by(desc(MACAddress.last_seen)).limit(10).all()
        arp_device = self.db.query(Device).filter(Device.id == arp_entry.device_id).first()
        results: List[Dict[str, Any]] = []
        if not candidates:
            interface_name = arp_entry.interface or "Unknown"
            is_uplink = InterfaceRecognizer.is_uplink_interface(
                interface_name=interface_name,
                interface_description=None,
                is_trunk=None,
                vlan_id=arp_entry.vlan_id
            )
            confidence = ConfidenceCalculator.calculate_confidence(
                interface_name=interface_name,
                is_uplink=is_uplink,
                has_mac_match=False,
                arp_vlan_id=arp_entry.vlan_id,
                mac_vlan_id=None
            )
            results.append({
                "ip_address": arp_entry.ip_address,
                "mac_address": arp_entry.mac_address,
                "arp_source_device_id": arp_entry.device_id,
                "mac_hit_device_id": None,
                "access_interface": interface_name,
                "vlan_id": arp_entry.vlan_id,
                "confidence": confidence,
                "is_uplink": is_uplink,
                "is_core_switch": CoreSwitchRecognizer.is_core_switch(arp_device, self.config) if arp_device else False,
                "match_type": "arp_only",
                "last_seen": arp_entry.last_seen
            })
            return results
        for mac_entry in candidates:
            hit_device = self.db.query(Device).filter(Device.id == mac_entry.device_id).first()
            is_uplink = InterfaceRecognizer.is_uplink_interface(
                interface_name=mac_entry.interface,
                interface_description=None,
                is_trunk=mac_entry.is_trunk,
                vlan_id=mac_entry.vlan_id
            )
            confidence = ConfidenceCalculator.calculate_confidence(
                interface_name=mac_entry.interface,
                is_uplink=is_uplink,
                has_mac_match=True,
                arp_vlan_id=arp_entry.vlan_id,
                mac_vlan_id=mac_entry.vlan_id
            )
            results.append({
                "ip_address": arp_entry.ip_address,
                "mac_address": arp_entry.mac_address,
                "arp_source_device_id": arp_entry.device_id,
                "mac_hit_device_id": mac_entry.device_id,
                "access_interface": mac_entry.interface,
                "vlan_id": mac_entry.vlan_id if mac_entry.vlan_id is not None else arp_entry.vlan_id,
                "confidence": confidence,
                "is_uplink": is_uplink,
                "is_core_switch": CoreSwitchRecognizer.is_core_switch(hit_device, self.config) if hit_device else False,
                "match_type": "same_device" if mac_entry.device_id == arp_entry.device_id else "cross_device",
                "last_seen": max(arp_entry.last_seen, mac_entry.last_seen)
            })
        results.sort(key=lambda item: (item["confidence"], item["last_seen"]), reverse=True)
        return results[:max_candidates]

    def build_snapshot_for_ips(self, changed_ips: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        为指定 IP 列表构建快照

        Args:
            changed_ips: 可选，限定只处理指定 IP 列表

        Returns:
            构建结果字典，包含批次 ID、输入 ARP 数、输出定位数
        """
        batch_id = self._new_batch_id()
        now = datetime.now()
        arp_entries = self._latest_arp_entries(changed_ips)
        output_count = 0
        seen_keys = set()

        with self.db.no_autoflush:
            for arp_entry in arp_entries:
                candidates = self._build_candidates(arp_entry)
                for candidate in candidates:
                    key = (
                        candidate["ip_address"],
                        candidate["mac_hit_device_id"],
                        candidate["access_interface"]
                    )
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    row = IPLocationCurrent(
                        ip_address=candidate["ip_address"],
                        mac_address=candidate["mac_address"],
                        arp_source_device_id=candidate["arp_source_device_id"],
                        mac_hit_device_id=candidate["mac_hit_device_id"],
                        access_interface=candidate["access_interface"],
                        vlan_id=candidate["vlan_id"],
                        confidence=float(candidate["confidence"]),
                        is_uplink=bool(candidate["is_uplink"]),
                        is_core_switch=bool(candidate["is_core_switch"]),
                        match_type=candidate["match_type"],
                        last_seen=candidate["last_seen"],
                        calculated_at=now,
                        calculate_batch_id=batch_id,
                        batch_status="calculating"
                    )
                    self.db.add(row)
                    output_count += 1

        self.db.commit()
        self.activate_batch(batch_id)
        return {
            "batch_id": batch_id,
            "input_arp_count": len(arp_entries),
            "output_location_count": output_count
        }

    def build_full_snapshot(self) -> Dict[str, Any]:
        """
        构建全量快照

        Returns:
            构建结果字典
        """
        return self.build_snapshot_for_ips()

    def build_incremental_snapshot(self, changed_ips: List[str]) -> Dict[str, Any]:
        """
        构建增量快照

        Args:
            changed_ips: 变化的 IP 地址列表

        Returns:
            构建结果字典
        """
        if not changed_ips:
            return {"batch_id": None, "input_arp_count": 0, "output_location_count": 0}
        return self.build_snapshot_for_ips(changed_ips=changed_ips)

    def get_locations(
        self,
        ip_address: str,
        filter_uplink: bool = True,
        sort_by_confidence: bool = True,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        查询指定 IP 地址的定位结果

        Args:
            ip_address: IP 地址
            filter_uplink: 是否过滤上联端口，默认 True
            sort_by_confidence: 是否按可信度排序，默认 True
            location: 可选，按位置筛选

        Returns:
            定位结果列表
        """
        active_batch = self.get_active_batch_id()
        if not active_batch:
            return []
        query = self.db.query(IPLocationCurrent).filter(
            and_(
                IPLocationCurrent.calculate_batch_id == active_batch,
                IPLocationCurrent.ip_address == ip_address
            )
        )
        rows = query.order_by(desc(IPLocationCurrent.confidence), desc(IPLocationCurrent.last_seen)).all()
        results: List[Dict[str, Any]] = []
        for row in rows:
            hit_device_id = row.mac_hit_device_id or row.arp_source_device_id
            device = self.db.query(Device).filter(Device.id == hit_device_id).first()
            results.append({
                "ip_address": row.ip_address,
                "mac_address": row.mac_address,
                "device_id": hit_device_id,
                "device_hostname": device.hostname if device else "Unknown",
                "device_ip": device.ip_address if device else "Unknown",
                "device_location": device.location if device else None,
                "interface": row.access_interface or "Unknown",
                "vlan_id": row.vlan_id,
                "last_seen": row.last_seen,
                "confidence": row.confidence,
                "is_uplink": row.is_uplink,
                "is_core_switch": row.is_core_switch,
                "retained_on_core_switch": True,
                "match_type": row.match_type,
                "arp_source_device": row.arp_source_device_id,
                "mac_hit_device": row.mac_hit_device_id,
                "calculated_at": row.calculated_at,
                "calculate_batch_id": row.calculate_batch_id
            })
        if filter_uplink:
            results = [item for item in results if not item.get("is_uplink", False)]
        if location:
            results = [item for item in results if location.lower() in (item.get("device_location") or "").lower()]
        if sort_by_confidence:
            results.sort(key=lambda item: (item["confidence"], item["last_seen"]), reverse=True)
        return results

    def get_ip_list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        filter_uplink: bool = True,
        sort_by_confidence: bool = True,
        location: Optional[str] = None
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        获取 IP 列表（分页）

        Args:
            page: 页码，默认 1
            page_size: 每页数量，默认 50
            search: 可选，IP 地址搜索关键词
            filter_uplink: 是否过滤上联端口，默认 True
            sort_by_confidence: 是否按可信度排序，默认 True
            location: 可选，按位置筛选

        Returns:
            (总数，当前页数据列表)
        """
        active_batch = self.get_active_batch_id()
        if not active_batch:
            return 0, []
        query = self.db.query(IPLocationCurrent).filter(
            IPLocationCurrent.calculate_batch_id == active_batch
        )
        if search:
            query = query.filter(IPLocationCurrent.ip_address.like(f"%{search}%"))
        rows = query.order_by(desc(IPLocationCurrent.confidence), desc(IPLocationCurrent.last_seen)).all()
        items: List[Dict[str, Any]] = []
        for row in rows:
            hit_device_id = row.mac_hit_device_id or row.arp_source_device_id
            device = self.db.query(Device).filter(Device.id == hit_device_id).first()
            items.append({
                "ip_address": row.ip_address,
                "mac_address": row.mac_address,
                "device_id": hit_device_id,
                "device_hostname": device.hostname if device else "Unknown",
                "device_ip": device.ip_address if device else "Unknown",
                "device_location": device.location if device else None,
                "interface": row.access_interface or "Unknown",
                "vlan_id": row.vlan_id,
                "last_seen": row.last_seen,
                "confidence": row.confidence,
                "is_uplink": row.is_uplink,
                "is_core_switch": row.is_core_switch,
                "retained_on_core_switch": True,
                "match_type": row.match_type,
                "calculated_at": row.calculated_at,
                "calculate_batch_id": row.calculate_batch_id
            })
        if filter_uplink:
            items = [item for item in items if not item.get("is_uplink", False)]
        if location:
            items = [item for item in items if location.lower() in (item.get("device_location") or "").lower()]
        if sort_by_confidence:
            items.sort(key=lambda item: (item["confidence"], item["last_seen"]), reverse=True)
        total = len(items)
        offset = (page - 1) * page_size
        return total, items[offset:offset + page_size]
