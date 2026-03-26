"""
IP 定位服务
提供 IP 地址定位功能
"""
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.models import Device, MACAddress
from app.schemas.ip_location_schemas import CollectionStatus

logger = logging.getLogger(__name__)


class IPLocationService:
    """IP 定位服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self._collection_status = CollectionStatus(
            is_running=False,
            last_run_at=None,
            last_run_success=True,
            devices_total=0,
            devices_completed=0,
            devices_failed=0
        )
    
    @property
    def collection_status(self) -> Dict[str, Any]:
        """获取收集状态"""
        return {
            "is_running": self._collection_status.is_running,
            "last_run_at": self._collection_status.last_run_at,
            "last_run_success": self._collection_status.last_run_success,
            "last_run_message": self._collection_status.last_run_message,
            "devices_total": self._collection_status.devices_total,
            "devices_completed": self._collection_status.devices_completed,
            "devices_failed": self._collection_status.devices_failed,
            "arp_entries_collected": self._collection_status.arp_entries_collected,
            "mac_entries_collected": self._collection_status.mac_entries_collected
        }
    
    def locate_ip(self, ip_address: str) -> List[Dict[str, Any]]:
        """
        定位 IP 地址
        
        从 ip_location_current 表查询预计算结果
        """
        from app.models.ip_location import IPLocationCurrent
        
        try:
            # 查询预计算结果
            entries = self.db.query(IPLocationCurrent).filter(
                IPLocationCurrent.ip_address == ip_address
            ).order_by(IPLocationCurrent.confidence.desc()).all()
            
            results = []
            for entry in entries:
                results.append({
                    "ip_address": entry.ip_address,
                    "mac_address": entry.mac_address,
                    "device_id": entry.mac_hit_device_id,
                    "device_hostname": entry.mac_device_hostname,
                    "device_ip": entry.mac_device_ip,
                    "device_location": entry.mac_device_location,
                    "interface": entry.access_interface,
                    "vlan_id": entry.vlan_id,
                    "last_seen": entry.last_seen,
                    "confidence": float(entry.confidence),
                    "is_uplink": bool(entry.is_uplink),
                    "is_core_switch": bool(entry.is_core_switch),
                    "match_type": entry.match_type
                })
            
            return results
        except Exception as e:
            logger.error(f"IP 定位失败 {ip_address}: {e}", exc_info=True)
            return []
    
    def get_ip_list(self, page: int = 1, page_size: int = 50, search: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
        """
        获取 IP 列表
        
        从 ip_location_current 表查询预计算结果
        
        返回：(总数，列表项)
        """
        from app.models.ip_location import IPLocationCurrent
        
        try:
            query = self.db.query(IPLocationCurrent)
            
            if search:
                query = query.filter(
                    (IPLocationCurrent.ip_address.like(f"%{search}%")) |
                    (IPLocationCurrent.mac_address.like(f"%{search}%")) |
                    (IPLocationCurrent.mac_device_hostname.like(f"%{search}%"))
                )
            
            total = query.count()
            entries = query.order_by(IPLocationCurrent.last_seen.desc()) \
                          .offset((page - 1) * page_size) \
                          .limit(page_size) \
                          .all()
            
            results = []
            for entry in entries:
                results.append({
                    "ip_address": entry.ip_address,  # ✅ 终端 IP（不是交换机管理 IP）
                    "mac_address": entry.mac_address,
                    "device_id": entry.mac_hit_device_id,
                    "device_hostname": entry.mac_device_hostname,
                    "device_ip": entry.mac_device_ip,
                    "device_location": entry.mac_device_location,
                    "interface": entry.access_interface,
                    "vlan_id": entry.vlan_id,
                    "last_seen": entry.last_seen,
                    "confidence": float(entry.confidence),
                    "is_uplink": bool(entry.is_uplink),
                    "is_core_switch": bool(entry.is_core_switch),
                    "match_type": entry.match_type
                })
            
            return total, results
        except Exception as e:
            logger.error(f"获取 IP 列表失败：{e}", exc_info=True)
            return 0, []
    
    async def collect_from_all_devices(self) -> Dict[str, Any]:
        """
        从所有设备收集 IP 定位数据
        
        调用 IPLocationCalculator 执行预计算
        """
        try:
            from app.services.ip_location_calculator import IPLocationCalculator
            
            self._collection_status.is_running = True
            logger.info("开始执行 IP 定位预计算...")
            
            # 使用计算器执行预计算
            calculator = IPLocationCalculator(self.db)
            result = calculator.calculate_batch()
            
            self._collection_status.is_running = False
            from datetime import datetime
            self._collection_status.last_run_at = datetime.now()
            self._collection_status.last_run_success = True
            self._collection_status.last_run_message = f"预计算完成：{result.get('matched', 0)} 条记录"
            self._collection_status.arp_entries_collected = result.get('total_arp', 0)
            self._collection_status.mac_entries_collected = result.get('matched', 0)
            
            logger.info(f"预计算完成：{result}")
            
            return {
                "success": True,
                "message": f"预计算完成，找到 {result.get('matched', 0)} 条 IP 定位记录"
            }
        except Exception as e:
            self._collection_status.is_running = False
            self._collection_status.last_run_success = False
            self._collection_status.last_run_message = str(e)
            logger.error(f"收集任务失败：{e}", exc_info=True)
            return {
                "success": False,
                "message": f"收集任务失败：{str(e)}"
            }


# 全局服务实例缓存
_service_cache: Dict[int, IPLocationService] = {}


def get_ip_location_service(db: Session) -> IPLocationService:
    """
    获取 IP 定位服务实例
    
    使用依赖注入模式，每个请求使用同一个服务实例
    """
    db_id = id(db)
    if db_id not in _service_cache:
        _service_cache[db_id] = IPLocationService(db)
    return _service_cache[db_id]
