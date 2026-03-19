"""
MAC 地址表收集器
支持华为、思科、H3C、锐捷等厂商
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.models import Device
from app.services.netmiko_service import NetmikoService

logger = logging.getLogger(__name__)


class MACCollector:
    """MAC 地址表收集器"""

    # 各厂商的 MAC 地址表命令
    MAC_COMMANDS = {
        "huawei": "display mac-address",
        "华为": "display mac-address",
        "cisco": "show mac address-table",
        "cisco_ios": "show mac address-table",
        "cisco_nxos": "show mac address-table",
        "h3c": "display mac-address",
        "华三": "display mac-address",
        "hp_comware": "display mac-address",
        "ruijie": "show mac-address-table",
        "锐捷": "show mac-address-table",
        "ruijie_os": "show mac-address-table",
    }

    def __init__(self, netmiko_service: NetmikoService):
        self.netmiko = netmiko_service

    def get_command(self, vendor: str) -> str:
        """获取对应厂商的 MAC 地址表命令"""
        vendor_lower = vendor.lower().strip()
        return self.MAC_COMMANDS.get(vendor_lower, "show mac address-table")

    async def collect_from_device(self, device: Device) -> List[Dict[str, Any]]:
        """
        从单台设备收集 MAC 地址表

        Returns:
            MAC 地址条目列表
        """
        command = self.get_command(device.vendor)
        logger.info(f"从设备 {device.hostname} 收集 MAC 地址表，命令: {command}")

        try:
            output = await self.netmiko.execute_command(device, command)
            if not output or output.strip() == "":
                logger.warning(f"设备 {device.hostname} MAC 地址表输出为空")
                return []

            # 根据厂商选择解析器
            entries = self._parse_output(output, device.vendor)
            logger.info(f"从设备 {device.hostname} 解析到 {len(entries)} 条 MAC 记录")
            return entries

        except Exception as e:
            logger.error(f"从设备 {device.hostname} 收集 MAC 地址表失败: {e}")
            raise

    def _parse_output(self, output: str, vendor: str) -> List[Dict[str, Any]]:
        """根据厂商选择解析器"""
        vendor_lower = vendor.lower().strip()

        if any(keyword in vendor_lower for keyword in ["huawei", "华为"]):
            return self._parse_huawei_mac(output)
        elif any(keyword in vendor_lower for keyword in ["cisco"]):
            return self._parse_cisco_mac(output)
        elif any(keyword in vendor_lower for keyword in ["h3c", "华三", "hp_comware"]):
            return self._parse_h3c_mac(output)
        elif any(keyword in vendor_lower for keyword in ["ruijie", "锐捷"]):
            return self._parse_ruijie_mac(output)
        else:
            logger.warning(f"未知厂商 {vendor}，尝试通用解析")
            return self._parse_generic_mac(output)

    def _parse_huawei_mac(self, output: str) -> List[Dict[str, Any]]:
        """解析华为 MAC 地址表"""
        entries = []
        lines = output.strip().split("\n")

        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.match(r"^-+$", line.replace(" ", "")):
                data_started = True
                continue

            if not data_started:
                continue

            if any(keyword in line for keyword in ["Total", "------", "MAC Address"]):
                continue

            # 华为格式: MAC Address    VLAN/VSI    Learned-From        Type
            # 示例: 0011-2233-4455 1/-         GE1/0/1             dynamic
            # 使用更灵活的分割，匹配任意空白字符
            parts = re.split(r"\s+", line.strip())
            if len(parts) < 3:
                continue

            try:
                mac_address = parts[0].strip()
                vlan_part = parts[1].strip() if len(parts) > 1 else ""
                interface = parts[2].strip() if len(parts) > 2 else ""
                address_type = parts[3].strip() if len(parts) > 3 else "dynamic"

                # 解析 VLAN
                vlan_id = None
                if "/" in vlan_part:
                    vlan_str = vlan_part.split("/")[0].strip()
                    if vlan_str.isdigit():
                        vlan_id = int(vlan_str)
                elif vlan_part.isdigit():
                    vlan_id = int(vlan_part)

                # 标准化 MAC 地址
                mac_address = self._normalize_mac(mac_address)
                if not mac_address:
                    continue

                entry = {
                    "mac_address": mac_address,
                    "vlan_id": vlan_id,
                    "interface": interface,
                    "address_type": address_type,
                    "learned_from": None,
                    "is_trunk": None,
                    "aging_time": None
                }
                entries.append(entry)

            except Exception as e:
                logger.debug(f"解析华为 MAC 行失败: {line}, 错误: {e}")
                continue

        return entries

    def _parse_cisco_mac(self, output: str) -> List[Dict[str, Any]]:
        """解析思科 MAC 地址表"""
        entries = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.match(r"^(Vlan|Mac|----)", line, re.IGNORECASE):
                continue

            # 思科格式: Vlan    Mac Address       Type        Ports
            # 示例:   1    0011.2233.4455    DYNAMIC     Gi1/0/1
            parts = re.split(r"\s+", line)
            if len(parts) < 4:
                continue

            try:
                vlan_str = parts[0].strip()
                mac_address = parts[1].strip()
                address_type = parts[2].strip()
                interface = parts[3].strip()

                vlan_id = int(vlan_str) if vlan_str.isdigit() else None

                mac_address = self._normalize_mac(mac_address)
                if not mac_address:
                    continue

                entry = {
                    "mac_address": mac_address,
                    "vlan_id": vlan_id,
                    "interface": interface,
                    "address_type": address_type.lower(),
                    "learned_from": None,
                    "is_trunk": None,
                    "aging_time": None
                }
                entries.append(entry)

            except Exception as e:
                logger.debug(f"解析思科 MAC 行失败: {line}, 错误: {e}")
                continue

        return entries

    def _parse_h3c_mac(self, output: str) -> List[Dict[str, Any]]:
        """解析 H3C MAC 地址表（与华为类似）"""
        return self._parse_huawei_mac(output)

    def _parse_ruijie_mac(self, output: str) -> List[Dict[str, Any]]:
        """解析锐捷 MAC 地址表"""
        return self._parse_cisco_mac(output)

    def _parse_generic_mac(self, output: str) -> List[Dict[str, Any]]:
        """通用 MAC 解析器"""
        entries = self._parse_huawei_mac(output)
        if not entries:
            entries = self._parse_cisco_mac(output)
        return entries

    def _normalize_mac(self, mac: str) -> Optional[str]:
        """标准化 MAC 地址格式"""
        if not mac:
            return None

        clean = re.sub(r"[-:\.]", "", mac.lower())
        if len(clean) != 12:
            return mac

        return ":".join([clean[i:i+2] for i in range(0, 12, 2)])
