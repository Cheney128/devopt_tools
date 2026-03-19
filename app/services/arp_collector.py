"""
ARP 表收集器
支持华为、思科、H3C、锐捷等厂商
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.models.models import Device
from app.services.netmiko_service import NetmikoService

logger = logging.getLogger(__name__)


class ARPCollector:
    """ARP 表收集器"""

    # 各厂商的 ARP 命令
    ARP_COMMANDS = {
        "huawei": "display arp",
        "华为": "display arp",
        "cisco": "show arp",
        "cisco_ios": "show arp",
        "cisco_nxos": "show arp",
        "h3c": "display arp",
        "华三": "display arp",
        "hp_comware": "display arp",
        "ruijie": "show arp",
        "锐捷": "show arp",
        "ruijie_os": "show arp",
    }

    def __init__(self, netmiko_service: NetmikoService):
        self.netmiko = netmiko_service

    def get_command(self, vendor: str) -> str:
        """获取对应厂商的 ARP 命令"""
        vendor_lower = vendor.lower().strip()
        return self.ARP_COMMANDS.get(vendor_lower, "show arp")

    async def collect_from_device(self, device: Device) -> List[Dict[str, Any]]:
        """
        从单台设备收集 ARP 表

        Returns:
            ARP 条目列表，每个条目包含:
            {
                "ip_address": "10.23.2.74",
                "mac_address": "2053-83a5-5949",
                "vlan_id": 2,
                "interface": "GE1/0/24",
                "arp_type": "dynamic",
                "age_minutes": 12
            }
        """
        command = self.get_command(device.vendor)
        logger.info(f"从设备 {device.hostname} 收集 ARP 表，命令: {command}")

        try:
            output = await self.netmiko.execute_command(device, command)
            if not output or output.strip() == "":
                logger.warning(f"设备 {device.hostname} ARP 表输出为空")
                return []

            # 根据厂商选择解析器
            entries = self._parse_output(output, device.vendor)
            logger.info(f"从设备 {device.hostname} 解析到 {len(entries)} 条 ARP 记录")
            return entries

        except Exception as e:
            logger.error(f"从设备 {device.hostname} 收集 ARP 表失败: {e}")
            raise

    def _parse_output(self, output: str, vendor: str) -> List[Dict[str, Any]]:
        """根据厂商选择解析器"""
        vendor_lower = vendor.lower().strip()

        if any(keyword in vendor_lower for keyword in ["huawei", "华为"]):
            return self._parse_huawei_arp(output)
        elif any(keyword in vendor_lower for keyword in ["cisco"]):
            return self._parse_cisco_arp(output)
        elif any(keyword in vendor_lower for keyword in ["h3c", "华三", "hp_comware"]):
            return self._parse_h3c_arp(output)
        elif any(keyword in vendor_lower for keyword in ["ruijie", "锐捷"]):
            return self._parse_ruijie_arp(output)
        else:
            logger.warning(f"未知厂商 {vendor}，尝试通用解析")
            return self._parse_generic_arp(output)

    def _parse_huawei_arp(self, output: str) -> List[Dict[str, Any]]:
        """
        解析华为 ARP 表输出格式:

        IP ADDRESS      MAC ADDRESS    EXP(M) TYPE/VLAN       INTERFACE        VPN-INSTANCE
        ----------------------------------------------------------------------------------------
        10.23.2.74      2053-83a5-5949        I               Vlanif2          _management_vpn_
        10.23.2.1       609b-b431-d2c3   12   D/2             GE1/0/24         _management_vpn_
        10.23.2.3       7439-89e2-2558    2   D/2             GE1/0/24         _management_vpn_
        """
        entries = []
        lines = output.strip().split("\n")

        # 找到表头分隔线之后的内容
        data_started = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测分隔线（多个连字符）
            if re.match(r"^-+$", line.replace(" ", "")):
                data_started = True
                continue

            if not data_started:
                continue

            # 跳过汇总行
            if any(keyword in line for keyword in ["Total", "------"]):
                continue

            # 解析数据行
            # 按空白字符分割，但保留字段完整性
            parts = re.split(r"\s{2,}", line)
            if len(parts) < 5:
                continue

            try:
                ip_address = parts[0].strip()
                mac_address = parts[1].strip()
                exp_or_type_vlan = parts[2].strip() if len(parts) > 2 else ""
                type_vlan = parts[3].strip() if len(parts) > 3 else exp_or_type_vlan
                interface = parts[4].strip() if len(parts) > 4 else ""

                # 验证 IP 地址
                if not self._is_valid_ip(ip_address):
                    continue

                # 标准化 MAC 地址格式
                mac_address = self._normalize_mac(mac_address)
                if not mac_address:
                    continue

                # 解析 TYPE/VLAN
                vlan_id = None
                arp_type = None
                if "/" in type_vlan:
                    type_parts = type_vlan.split("/")
                    arp_type = type_parts[0].strip()
                    if len(type_parts) > 1:
                        try:
                            vlan_id = int(type_parts[1].strip())
                        except ValueError:
                            pass
                else:
                    arp_type = type_vlan

                # 解析老化时间
                age_minutes = None
                if exp_or_type_vlan and exp_or_type_vlan.isdigit():
                    try:
                        age_minutes = int(exp_or_type_vlan)
                    except ValueError:
                        pass

                entry = {
                    "ip_address": ip_address,
                    "mac_address": mac_address,
                    "vlan_id": vlan_id,
                    "interface": interface,
                    "arp_type": arp_type,
                    "age_minutes": age_minutes
                }
                entries.append(entry)

            except Exception as e:
                logger.debug(f"解析华为 ARP 行失败: {line}, 错误: {e}")
                continue

        return entries

    def _parse_cisco_arp(self, output: str) -> List[Dict[str, Any]]:
        """
        解析思科 ARP 表输出格式:

        Protocol  Address          Age (min)  Hardware Addr   Type   Interface
        Internet  10.23.2.22              -   64e9.5055.ce41  ARPA   Vlan2
        Internet  10.23.2.3               2   7439.89e2.2558  ARPA   Vlan2
        Internet  10.23.2.1               2   609b.b431.d2c3  ARPA   Vlan2
        """
        entries = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 跳过表头
            if line.startswith("Protocol") or line.startswith("------"):
                continue

            parts = re.split(r"\s+", line)
            if len(parts) < 6:
                continue

            try:
                protocol = parts[0]
                ip_address = parts[1]
                age_str = parts[2]
                mac_address = parts[3]
                arp_type = parts[4]
                interface = parts[5]

                if protocol != "Internet":
                    continue

                if not self._is_valid_ip(ip_address):
                    continue

                mac_address = self._normalize_mac(mac_address)
                if not mac_address:
                    continue

                # 解析老化时间
                age_minutes = None
                if age_str != "-":
                    try:
                        age_minutes = int(age_str)
                    except ValueError:
                        pass

                # 从接口解析 VLAN（如 Vlan2 → VLAN 2）
                vlan_id = None
                if interface.lower().startswith("vlan"):
                    vlan_match = re.search(r"vlan[-\s]?(\d+)", interface, re.IGNORECASE)
                    if vlan_match:
                        vlan_id = int(vlan_match.group(1))

                entry = {
                    "ip_address": ip_address,
                    "mac_address": mac_address,
                    "vlan_id": vlan_id,
                    "interface": interface,
                    "arp_type": arp_type,
                    "age_minutes": age_minutes
                }
                entries.append(entry)

            except Exception as e:
                logger.debug(f"解析思科 ARP 行失败: {line}, 错误: {e}")
                continue

        return entries

    def _parse_h3c_arp(self, output: str) -> List[Dict[str, Any]]:
        """解析 H3C ARP 表（与华为类似）"""
        # H3C 格式与华为基本一致，复用华为解析器
        return self._parse_huawei_arp(output)

    def _parse_ruijie_arp(self, output: str) -> List[Dict[str, Any]]:
        """解析锐捷 ARP 表"""
        # 锐捷格式与思科类似，复用思科解析器
        return self._parse_cisco_arp(output)

    def _parse_generic_arp(self, output: str) -> List[Dict[str, Any]]:
        """通用 ARP 解析器（后备方案）"""
        # 尝试同时匹配华为和思科格式
        entries = self._parse_huawei_arp(output)
        if not entries:
            entries = self._parse_cisco_arp(output)
        return entries

    def _is_valid_ip(self, ip: str) -> bool:
        """简单验证 IP 地址格式"""
        if not ip:
            return False
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True

    def _normalize_mac(self, mac: str) -> Optional[str]:
        """
        标准化 MAC 地址格式
        支持输入: 2053-83a5-5949, 2053.83a5.5949, 20:53:83:a5:59:49
        统一输出: 20:53:83:a5:59:49 或 2053-83a5-5949（保持原样）
        """
        if not mac:
            return None

        # 移除所有分隔符
        clean = re.sub(r"[-:\.]", "", mac.lower())
        if len(clean) != 12:
            return mac  # 格式不对，返回原样

        # 标准化为 xx:xx:xx:xx:xx:xx 格式
        return ":".join([clean[i:i+2] for i in range(0, 12, 2)])
