"""
Netmiko服务模块
提供基于Netmiko的网络设备操作服务
"""
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
    NETMIKO_AVAILABLE = True
except ImportError:
    NETMIKO_AVAILABLE = False
    ConnectHandler = None

from app.models.models import Device


class NetmikoService:
    """
    Netmiko设备操作服务类
    提供设备连接、命令执行和数据采集功能
    """

    # 设备类型映射（支持中英文厂商名称）
    DEVICE_TYPE_MAPPING = {
        "cisco": "cisco_ios",
        "cisco_ios": "cisco_ios",
        "cisco_nxos": "cisco_nxos",
        "cisco_asa": "cisco_asa",
        "huawei": "huawei",
        "华为": "huawei",  # 添加中文厂商名称映射
        "h3c": "hp_comware",
        "hp_comware": "hp_comware",
        "华三": "hp_comware",  # 添加中文厂商名称映射
        "ruijie": "ruijie_os",
        "锐捷": "ruijie_os",  # 添加中文厂商名称映射
        "juniper": "juniper_junos",
        "arista": "arista_eos",
        "中兴": "huawei",  # 添加中文厂商名称映射
        "zte": "huawei",
    }

    # 命令映射
    COMMAND_MAPPING = {
        "cisco": {
            "version": "show version",
            "interfaces": "show interfaces",
            "interfaces_status": "show interfaces status",
            "mac_table": "show mac address-table",
            "inventory": "show inventory",
            "running_config": "show running-config",
        },
        "huawei": {
            "version": "display version",
            "interfaces": "display interface",
            "interfaces_status": "display interface brief",
            "mac_table": "display mac-address",
            "inventory": "display elabel",
            "running_config": "display current-configuration",
        },
        "h3c": {
            "version": "display version",
            "interfaces": "display interface",
            "interfaces_status": "display interface brief",
            "mac_table": "display mac-address",
            "inventory": "display device",
            "running_config": "display current-configuration",
        },
        "ruijie": {
            "version": "show version",
            "interfaces": "show interface",
            "interfaces_status": "show interface status",
            "mac_table": "show mac-address-table",
            "inventory": "show inventory",
            "running_config": "show running-config",
        },
    }

    def __init__(self):
        """初始化Netmiko服务"""
        self.timeout = 60  # 增加默认超时时间到60秒
        self.max_retries = 3
        self.conn_timeout = 30  # 增加连接超时时间到30秒

    def get_device_type(self, vendor: str) -> str:
        """
        获取Netmiko设备类型

        Args:
            vendor: 设备厂商

        Returns:
            Netmiko设备类型字符串
        """
        if not vendor:
            return "cisco_ios"  # 默认返回Cisco IOS

        vendor_lower = vendor.lower().strip()
        return self.DEVICE_TYPE_MAPPING.get(vendor_lower, "cisco_ios")

    def get_commands(self, vendor: str, command_type: str) -> str:
        """
        获取对应厂商的命令

        Args:
            vendor: 设备厂商
            command_type: 命令类型

        Returns:
            命令字符串
        """
        if not vendor or not command_type:
            return ""

        vendor_lower = vendor.lower().strip()
        vendor_commands = self.COMMAND_MAPPING.get(vendor_lower, self.COMMAND_MAPPING["cisco"])
        return vendor_commands.get(command_type, "")

    async def connect_to_device(self, device: Device, retry_count: int = None) -> Optional[Any]:
        """
        连接到设备（带重试机制）

        Args:
            device: 设备对象
            retry_count: 重试次数，None表示使用默认值

        Returns:
            Netmiko连接对象，失败返回None
        """
        if not NETMIKO_AVAILABLE:
            print("[ERROR] Netmiko is not installed")
            return None

        device_type = self.get_device_type(device.vendor)
        max_retries = retry_count if retry_count is not None else self.max_retries

        print(f"[INFO] Attempting to connect to device {device.hostname} ({device.ip_address})")
        print(f"[INFO] Device type: {device_type}, Max retries: {max_retries}")

        for attempt in range(1, max_retries + 1):
            try:
                device_params = self._build_device_params(device, device_type)
                
                print(f"[INFO] Connection attempt {attempt}/{max_retries} for device {device.hostname}")
                
                # 在异步环境中运行同步的netmiko连接
                loop = asyncio.get_event_loop()
                connection = await loop.run_in_executor(
                    None,
                    lambda: ConnectHandler(**device_params)
                )
                
                print(f"[SUCCESS] Successfully connected to device {device.hostname} on attempt {attempt}")
                return connection
                
            except NetmikoAuthenticationException as e:
                print(f"[ERROR] Authentication failed for device {device.hostname} on attempt {attempt}: {e}")
                print(f"[ERROR] Common causes: 1) Invalid username/password, 2) Incorrect SSH key, 3) Wrong device")
                
                # 认证失败不需要重试
                if attempt == max_retries:
                    print(f"[ERROR] All {max_retries} authentication attempts failed for device {device.hostname}")
                return None
                
            except NetmikoTimeoutException as e:
                print(f"[ERROR] Connection timeout for device {device.hostname} on attempt {attempt}: {e}")
                print(f"[ERROR] Common causes: 1) Network unreachable, 2) Firewall blocking, 3) Wrong IP/port")
                
                # 最后一次尝试失败
                if attempt == max_retries:
                    print(f"[ERROR] All {max_retries} connection attempts timed out for device {device.hostname}")
                    return None
                
                # 等待一段时间后重试（指数退避）
                wait_time = min(2 ** attempt, 10)  # 最多等待10秒
                print(f"[INFO] Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                print(f"[ERROR] Unexpected error connecting to device {device.hostname} on attempt {attempt}: {e}")
                print(f"[ERROR] Error type: {type(e).__name__}")
                
                # 最后一次尝试失败
                if attempt == max_retries:
                    print(f"[ERROR] All {max_retries} connection attempts failed for device {device.hostname}")
                    import traceback
                    traceback.print_exc()
                    return None
                
                # 等待一段时间后重试
                wait_time = min(2 ** attempt, 10)
                print(f"[INFO] Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
        
        return None

    def _build_device_params(self, device: Device, device_type: str) -> dict:
        """
        构建设备连接参数

        Args:
            device: 设备对象
            device_type: 设备类型

        Returns:
            设备连接参数字典
        """
        device_params = {
            "device_type": device_type,
            "host": device.ip_address,
            "username": device.username,
            "port": device.login_port,
            "timeout": self.timeout,
            "conn_timeout": self.conn_timeout,
            "session_log": None,  # 禁用会话日志以提高性能
            "allow_agent": False,  # 禁用SSH代理
            "global_delay_factor": 2,  # 增加全局延迟因子
            "fast_cli": False,  # 禁用快速CLI模式
        }

        # 根据认证方式设置不同的参数
        if device.password:
            device_params["password"] = device.password
        
        # 支持密钥认证（如果设备对象有private_key属性）
        if hasattr(device, 'private_key') and device.private_key:
            device_params["use_keys"] = True
            device_params["key_file"] = device.private_key
        
        # 支持passphrase（如果设备对象有passphrase属性）
        if hasattr(device, 'passphrase') and device.passphrase:
            device_params["passphrase"] = device.passphrase
        
        # 如果是telnet连接
        if device.login_method.lower() == "telnet":
            device_params["device_type"] = device_type.replace("ssh", "telnet")
        # 如果是console连接
        elif device.login_method.lower() == "console":
            device_params["device_type"] = f"{device_type}_console"
        
        return device_params

    def _is_config_command(self, command: str, vendor: str) -> bool:
        """
        判断命令是否为配置命令（需要进入配置模式）

        Args:
            command: 命令字符串
            vendor: 设备厂商

        Returns:
            bool: 是否为配置命令
        """
        config_keywords = [
            'system-view', 'sysname', 'interface', 'vlan', 'ip address',
            'route', 'acl', 'commit', 'quit', 'return', 'undo',
            'description', 'shutdown', 'undo shutdown'
        ]
        command_lower = command.lower().strip()
        return any(keyword in command_lower for keyword in config_keywords)

    def _get_vendor_expect_strings(self, vendor: str) -> dict:
        """
        获取厂商特定的expect字符串

        Args:
            vendor: 设备厂商

        Returns:
            dict: 包含各种模式的expect字符串
        """
        vendor_lower = vendor.lower().strip() if vendor else "cisco"

        if vendor_lower in ['huawei', 'h3c', '华为', '华三']:
            return {
                'user_view': r'<.*>',           # 用户视图: <hostname>
                'system_view': r'\[.*\]',       # 系统视图: [~hostname] 或 [hostname]
                'config_view': r'\[.*\]',       # 配置视图
                'any_view': r'[<>\[].*[>\]]'    # 任意视图
            }
        elif vendor_lower in ['cisco', 'ruijie', '锐捷']:
            return {
                'user_view': r'.*#',            # 特权模式: hostname#
                'config_view': r'\(config.*\)#', # 配置模式: hostname(config)#
                'any_view': r'.*[#>]'
            }
        else:
            # 默认使用Cisco风格
            return {
                'user_view': r'.*#',
                'config_view': r'\(config.*\)#',
                'any_view': r'.*[#>]'
            }

    async def execute_command(self, device: Device, command: str, expect_string: Optional[str] = None, read_timeout: int = 20) -> Optional[str]:
        """
        在设备上执行命令（带增强的错误处理）

        Args:
            device: 设备对象
            command: 要执行的命令
            expect_string: 预期的提示符字符串，用于判断命令执行完成
            read_timeout: 命令执行超时时间（秒）

        Returns:
            命令输出，失败返回None
        """
        from app.services.ssh_connection_pool import get_ssh_connection_pool

        print(f"[INFO] Executing command '{command}' on device {device.hostname} ({device.ip_address})")
        print(f"[INFO] Command timeout: {read_timeout}s, Expect string: {expect_string}")

        ssh_conn_pool = get_ssh_connection_pool()
        connection = None
        ssh_connection = None

        try:
            # 从连接池获取连接
            ssh_connection = await ssh_conn_pool.get_connection(device)
            if ssh_connection:
                connection = ssh_connection.connection
                print(f"[INFO] Got connection from pool for device {device.hostname}")
            else:
                # 连接池获取失败，尝试直接连接
                print(f"[INFO] Failed to get connection from pool, trying direct connection")
                connection = await self.connect_to_device(device)

            if not connection:
                print(f"[ERROR] Failed to connect to device {device.hostname} ({device.ip_address}) for command execution")
                print(f"[ERROR] Please check:")
                print(f"[ERROR]   1. Device IP address: {device.ip_address}")
                print(f"[ERROR]   2. Device SSH port: {device.login_port}")
                print(f"[ERROR]   3. Device username: {device.username}")
                print(f"[ERROR]   4. Device password: {'*' * len(device.password) if device.password else 'Not set'}")
                print(f"[ERROR]   5. Network connectivity (try: ping {device.ip_address})")
                print(f"[ERROR]   6. Device SSH service status")
                print(f"[ERROR]   7. Firewall rules")
                return None

            loop = asyncio.get_event_loop()

            # 获取厂商特定的expect字符串
            vendor_expects = self._get_vendor_expect_strings(device.vendor)

            # 判断是否为配置命令
            is_config_cmd = self._is_config_command(command, device.vendor)

            try:
                # 如果用户提供了expect_string，使用用户提供的
                if expect_string:
                    print(f"[INFO] Sending command with user-provided expect_string: {expect_string}")
                    output = await loop.run_in_executor(
                        None,
                        lambda: connection.send_command(command, expect_string=expect_string, read_timeout=read_timeout)
                    )
                elif is_config_cmd:
                    # 对于配置命令，使用send_config_set方法
                    print(f"[INFO] Detected config command, using send_config_set")
                    try:
                        # 尝试使用send_config_set执行配置命令
                        output = await loop.run_in_executor(
                            None,
                            lambda: connection.send_config_set(
                                [command],
                                exit_config_mode=False,  # 不自动退出配置模式
                                read_timeout=read_timeout
                            )
                        )
                    except Exception as config_e:
                        print(f"[WARNING] send_config_set failed: {config_e}, trying send_command with expect_string")
                        # 如果send_config_set失败，回退到send_command
                        output = await loop.run_in_executor(
                            None,
                            lambda: connection.send_command(
                                command,
                                expect_string=vendor_expects['any_view'],
                                read_timeout=read_timeout
                            )
                        )
                else:
                    # 普通查询命令，使用默认方式
                    print(f"[INFO] Sending command without expect_string (query command)")
                    output = await loop.run_in_executor(
                        None,
                        lambda: connection.send_command(command, read_timeout=read_timeout)
                    )

                if output:
                    print(f"[SUCCESS] Command '{command}' executed successfully on device {device.hostname}")
                    print(f"[INFO] Output length: {len(output)} characters")
                else:
                    print(f"[WARNING] Command '{command}' returned empty output on device {device.hostname}")

                return output

            except NetmikoTimeoutException as e:
                print(f"[ERROR] Timeout executing command '{command}' on device {device.hostname} ({device.ip_address})")
                print(f"[ERROR] Timeout value: {read_timeout}s")
                print(f"[ERROR] Possible causes:")
                print(f"[ERROR]   1. Command execution takes too long")
                print(f"[ERROR]   2. Device is busy")
                print(f"[ERROR]   3. Network latency")
                print(f"[ERROR]   4. Prompt pattern not detected (try using expect_string)")
                return None

            except Exception as e:
                print(f"[ERROR] Error sending command '{command}' to device {device.hostname}: {e}")
                print(f"[ERROR] Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                return None

        except NetmikoTimeoutException as e:
            print(f"[ERROR] Connection timeout for device {device.hostname} ({device.ip_address})")
            print(f"[ERROR] Connection timeout: {self.conn_timeout}s")
            print(f"[ERROR] Possible causes:")
            print(f"[ERROR]   1. Network unreachable")
            print(f"[ERROR]   2. Firewall blocking connection")
            print(f"[ERROR]   3. Wrong IP address or port")
            print(f"[ERROR]   4. Device SSH service not running")
            return None

        except NetmikoAuthenticationException as e:
            print(f"[ERROR] Authentication failed for device {device.hostname} ({device.ip_address})")
            print(f"[ERROR] Possible causes:")
            print(f"[ERROR]   1. Invalid username: {device.username}")
            print(f"[ERROR]   2. Invalid password")
            print(f"[ERROR]   3. Account locked or disabled")
            print(f"[ERROR]   4. Device requires special authentication method")
            return None

        except Exception as e:
            print(f"[ERROR] Unexpected error executing command '{command}' on device {device.hostname} ({device.ip_address}): {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            print(f"[ERROR] Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            if ssh_connection:
                # 如果是从连接池获取的连接，只需释放回连接池
                await ssh_conn_pool.release_connection(ssh_connection)
                print(f"[INFO] Released connection back to pool for device {device.hostname}")
            elif connection:
                # 如果是直接创建的连接，需要关闭
                try:
                    connection.disconnect()
                    print(f"[INFO] Disconnected from device {device.hostname} after command execution")
                except Exception as e:
                    print(f"[WARNING] Error disconnecting from device {device.hostname}: {e}")

    def parse_version_info(self, output: str, vendor: str) -> Dict[str, Any]:
        """
        解析设备版本信息

        Args:
            output: 命令输出
            vendor: 设备厂商

        Returns:
            解析后的版本信息字典
        """
        if not output:
            return {}

        version_info = {
            "device_id": None,
            "software_version": None,
            "hardware_version": None,
            "boot_version": None,
            "system_image": None,
            "uptime": None,
            "collected_at": datetime.now(),
        }

        vendor_lower = vendor.lower().strip()

        try:
            if vendor_lower.startswith("cisco"):
                version_info.update(self._parse_cisco_version(output))
            elif vendor_lower in ["huawei", "h3c"]:
                version_info.update(self._parse_huawei_version(output))
            elif vendor_lower == "ruijie":
                version_info.update(self._parse_ruijie_version(output))
        except Exception as e:
            print(f"Error parsing version info: {e}")

        return version_info

    def _parse_cisco_version(self, output: str) -> Dict[str, Any]:
        """解析Cisco版本信息"""
        result = {}

        # 潯件版本 - 支持多种格式
        # Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11
        # Cisco IOS XE Software, Version 17.3.5
        # 先尝试匹配完整的版本行
        version_match = re.search(r'Cisco IOS Software[,\s]+Version\s+([^\n\(]+)\s*\)?[^\n]*', output, re.IGNORECASE)
        if version_match:
            result["software_version"] = "Cisco IOS Software, Version " + version_match.group(1).strip()
        else:
            # 备用：只匹配版本号
            ios_match = re.search(r'Version\s+([^\s,\n]+)', output, re.IGNORECASE)
            if ios_match:
                result["software_version"] = "Cisco IOS Software, Version " + ios_match.group(1)

        # 系统镜像
        image_match = re.search(r'System image file is\s+"?([^"\n]+)"?', output)
        if image_match:
            result["system_image"] = image_match.group(1)

        # 硬件版本
        hw_match = re.search(r'Hardware is\s+([^\n]+)', output)
        if hw_match:
            result["hardware_version"] = hw_match.group(1)

        # 运行时间
        uptime_match = re.search(r'uptime is\s+([^\n]+)', output)
        if uptime_match:
            result["uptime"] = uptime_match.group(1)

        return result

    def _parse_huawei_version(self, output: str) -> Dict[str, Any]:
        """解析华为/H3C版本信息"""
        result = {}

        # 软件版本
        version_match = re.search(r'Version\s+([^\s\n]+)', output)
        if not version_match:
            version_match = re.search(r'VRP.*Version\s+([^\s\n]+)', output)
        if version_match:
            result["software_version"] = version_match.group(1)

        # 硬件版本
        hw_match = re.search(r'Hardware Version\s+([^\s\n]+)', output)
        if hw_match:
            result["hardware_version"] = hw_match.group(1)

        # 启动版本
        boot_match = re.search(r'Bootrom Version\s+([^\s\n]+)', output)
        if boot_match:
            result["boot_version"] = boot_match.group(1)

        # 系统镜像
        image_match = re.search(r'Software Name\s+([^\s\n]+)', output)
        if image_match:
            result["system_image"] = image_match.group(1)

        # 运行时间
        uptime_match = re.search(r'Uptime is\s+([^\n]+)', output)
        if uptime_match:
            result["uptime"] = uptime_match.group(1)

        return result

    def _parse_ruijie_version(self, output: str) -> Dict[str, Any]:
        """解析锐捷版本信息"""
        result = {}

        # 软件版本
        version_match = re.search(r'Software Version\s+([^\s\n]+)', output)
        if version_match:
            result["software_version"] = version_match.group(1)

        # 系统镜像
        image_match = re.search(r'Boot image\s+([^\s\n]+)', output)
        if image_match:
            result["system_image"] = image_match.group(1)

        # 运行时间
        uptime_match = re.search(r'System uptime\s+([^\n]+)', output)
        if uptime_match:
            result["uptime"] = uptime_match.group(1)

        return result

    def parse_serial_from_version(self, output: str, vendor: str) -> Optional[str]:
        """
        从版本命令输出中解析序列号

        Args:
            output: 版本命令输出
            vendor: 设备厂商

        Returns:
            序列号字符串，未找到返回None
        """
        if not output:
            return None

        vendor_lower = vendor.lower().strip()

        # Cisco
        if vendor_lower.startswith("cisco"):
            # 查找 "Processor board ID" 或 "System Serial Number"
            match = re.search(r'(?:Processor board ID|System Serial Number)\s+([A-Z0-9]+)', output)
            if match:
                return match.group(1)

        # 华为/H3C
        elif vendor_lower in ["huawei", "h3c"]:
            # 查找 "ESN" 或 "MAC" 地址（部分设备用MAC代替SN）
            match = re.search(r'ESN\s+([A-Z0-9]+)', output)
            if match:
                return match.group(1)

        return None

    def parse_serial_from_inventory(self, output: str, vendor: str) -> Optional[str]:
        """
        从inventory命令输出中解析序列号

        Args:
            output: inventory命令输出
            vendor: 设备厂商

        Returns:
            序列号字符串，未找到返回None
        """
        if not output:
            return None

        vendor_lower = vendor.lower().strip()

        # Cisco
        if vendor_lower.startswith("cisco"):
            # 查找 "SN:" 或 "Serial Number:"
            match = re.search(r'SN:\s+([A-Z0-9]+)', output)
            if not match:
                match = re.search(r'Serial Number:\s+([A-Z0-9]+)', output)
            if match:
                return match.group(1)

        return None

    def parse_mac_table(self, output: str, vendor: str) -> List[Dict[str, Any]]:
        """
        解析MAC地址表

        Args:
            output: MAC地址表命令输出
            vendor: 设备厂商

        Returns:
            MAC地址条目列表
        """
        if not output:
            return []

        mac_entries = []
        vendor_lower = vendor.lower().strip()

        try:
            if vendor_lower.startswith("cisco"):
                mac_entries = self._parse_cisco_mac_table(output)
            elif vendor_lower in ["huawei", "h3c"]:
                mac_entries = self._parse_huawei_mac_table(output)
            elif vendor_lower == "ruijie":
                mac_entries = self._parse_ruijie_mac_table(output)
        except Exception as e:
            print(f"Error parsing MAC table: {e}")

        return mac_entries

    def _parse_cisco_mac_table(self, output: str) -> List[Dict[str, Any]]:
        """解析Cisco MAC地址表"""
        mac_entries = []

        # Cisco MAC地址表格式：
        # Vlan    Mac Address       Type        Ports
        # ----    -----------       --------    -----
        #   1    0011.2233.4455    DYNAMIC     Gi1/0/1

        lines = output.strip().split('\n')
        for line in lines:
            # 跳过标题行
            if not line.strip() or re.match(r'Vlan\s+Mac\s+Address', line, re.IGNORECASE):
                continue

            # 匹配MAC地址行 - 使用更精确的正则
            # 匹配格式: VLAN号 + 空格 + MAC地址(12位十六进制) + 空格 + 类型 + 空格 + 接口名
            match = re.search(r'(\d+)\s+([0-9A-Fa-f.:\-]+)\s+(\w+)\s+(.+)', line)
            if match:
                mac_raw = match.group(2)
                mac_entries.append({
                    "mac_address": mac_raw.upper(),
                    "vlan_id": int(match.group(1)),
                    "interface": match.group(3),
                    "address_type": match.group(4).lower()
                })

        return mac_entries

    def _parse_huawei_mac_table(self, output: str) -> List[Dict[str, Any]]:
        """解析华为/H3C MAC地址表"""
        mac_entries = []

        # 华为/H3C MAC地址表格式：
        # MAC Address    VLAN/VSI    Learned-From        Type
        # 0011-2233-4455 1/-         GE1/0/1             dynamic

        lines = output.strip().split('\n')
        for line in lines:
            # 跳过标题行和空行
            if not line.strip() or re.match(r'MAC\s+Address', line, re.IGNORECASE):
                continue

            # 匹配MAC地址行 - 使用更灵活的正则（支持GE1/0/1格式）
            # 华为格式：MAC地址 VLAN/VSI 接口 类型
            match = re.search(r'([0-9A-Fa-f-]+)\s*(?:[/-]\s*(\d+)/\S*\s*(\S+))', line)
            if match:
                mac_raw = match.group(1)
                mac_entries.append({
                    "mac_address": mac_raw.upper(),
                    "vlan_id": int(match.group(2)),
                    "interface": match.group(3).strip(),
                    "address_type": match.group(4).lower()
                })

        return mac_entries

    def _parse_ruijie_mac_table(self, output: str) -> List[Dict[str, Any]]:
        """解析锐捷MAC地址表（使用类似Cisco格式）"""
        return self._parse_cisco_mac_table(output)

    def _normalize_mac_address(self, mac: str) -> str:
        """
        标准化MAC地址格式为 xx:xx:xx:xx:xx:xx
        保留原始格式（Cisco用点分隔，华为用横线分隔）

        Args:
            mac: 原始MAC地址字符串

        Returns:
            标准化后的MAC地址
        """
        # 移除所有分隔符并转为大写
        mac_clean = re.sub(r'[^0-9A-Fa-f]', '', mac.upper())

        # 如果已经是12位十六进制，保持原始格式（添加原始分隔符）
        if len(mac_clean) == 12:
            return mac

        # 如果格式不正确，尝试添加冒号分隔符
        return mac

    def parse_interfaces_info(self, interfaces_output: str, status_output: Optional[str], vendor: str) -> List[Dict[str, Any]]:
        """
        解析接口信息

        Args:
            interfaces_output: 接口详细命令输出
            status_output: 接口状态命令输出（可选）
            vendor: 设备厂商

        Returns:
            接口信息列表
        """
        if not interfaces_output:
            return []

        interfaces = []
        vendor_lower = vendor.lower().strip()

        try:
            if vendor_lower.startswith("cisco"):
                interfaces = self._parse_cisco_interfaces(interfaces_output, status_output)
            elif vendor_lower in ["huawei", "h3c"]:
                interfaces = self._parse_huawei_interfaces(interfaces_output, status_output)
            elif vendor_lower == "ruijie":
                interfaces = self._parse_ruijie_interfaces(interfaces_output, status_output)
        except Exception as e:
            print(f"Error parsing interfaces info: {e}")

        return interfaces

    def _parse_cisco_interfaces(self, interfaces_output: str, status_output: Optional[str]) -> List[Dict[str, Any]]:
        """解析Cisco接口信息"""
        interfaces = []

        # 解析详细接口信息
        # GigabitEthernet1/0/1 is up, line protocol is up
        #   Description: Uplink to Core
        #   MTU 1500 bytes, BW 1000000 Kbit

        interface_blocks = re.split(r'\n(?=[A-Za-z]+\d+/\d+)', interfaces_output)

        for block in interface_blocks:
            block = block.strip()
            if not block or re.match(r'^(Line|Cabling|Dampening|Last)', block):
                continue

            interface_match = re.match(r'([A-Za-z]+\d+(?:/\d+)*)\s+is\s+(\w+)', block)
            if not interface_match:
                continue

            interface_name = interface_match.group(1)
            status = interface_match.group(2)

            # 解析描述
            desc_match = re.search(r'Description:\s+([^\n]+)', block)
            description = desc_match.group(1).strip() if desc_match else ""

            # 解析速率
            speed_match = re.search(r'BW\s+(\d+)\s*Kbit', block)
            speed = f"{speed_match.group(1)} Kbit" if speed_match else ""

            interfaces.append({
                "port_name": interface_name,
                "status": status,
                "description": description,
                "speed": speed
            })

        # 如果有状态输出，合并状态信息
        if status_output:
            self._merge_cisco_interface_status(interfaces, status_output)

        return interfaces

    def _merge_cisco_interface_status(self, interfaces: List[Dict[str, Any]], status_output: str):
        """合并Cisco接口状态信息"""
        # Port      Name               Status       Vlan
        # Gi1/0/1   Uplink             connected    1
        lines = status_output.split('\n')

        for line in lines:
            # 跳过标题行
            if re.match(r'Port\s+Name', line):
                continue

            # 匹配状态行
            match = re.match(r'(\S+)\s+(.*?)\s+(\w+)', line)
            if match:
                port_short = match.group(1)
                status = match.group(2)

                # 查找对应的接口
                for interface in interfaces:
                    if port_short in interface["port_name"]:
                        interface["status"] = status
                        break

    def _parse_huawei_interfaces(self, interfaces_output: str, status_output: Optional[str]) -> List[Dict[str, Any]]:
        """解析华为/H3C接口信息"""
        interfaces = []

        # Huawei接口格式：
        # GigabitEthernet1/0/1
        #   Description: Uplink
        #   Line protocol state: up
        #   Line protocol state (physical): up

        interface_blocks = re.split(r'\n(?=[A-Za-z]+\d+/\d+)', interfaces_output)

        for block in interface_blocks:
            block = block.strip()
            if not block:
                continue

            interface_match = re.match(r'([A-Za-z]+\d+(?:/\d+)*)', block)
            if not interface_match:
                continue

            interface_name = interface_match.group(1)

            # 解析状态
            state_match = re.search(r'(?:Line protocol state|Physical state):\s+(\w+)', block)
            status = state_match.group(1).lower() if state_match else "unknown"

            # 解析描述
            desc_match = re.search(r'Description:\s+([^\n]+)', block)
            description = desc_match.group(1).strip() if desc_match else ""

            interfaces.append({
                "port_name": interface_name,
                "status": status,
                "description": description,
                "speed": ""
            })

        return interfaces

    def _parse_ruijie_interfaces(self, interfaces_output: str, status_output: Optional[str]) -> List[Dict[str, Any]]:
        """解析锐捷接口信息（使用类似Cisco格式）"""
        return self._parse_cisco_interfaces(interfaces_output, status_output)

    async def collect_device_version(self, device: Device) -> Optional[Dict[str, Any]]:
        """
        采集设备版本信息

        Args:
            device: 设备对象

        Returns:
            版本信息字典，失败返回None
        """
        if not device.username or not device.password:
            print(f"Device {device.hostname} missing credentials")
            return None

        command = self.get_commands(device.vendor, "version")
        if not command:
            return None

        output = await self.execute_command(device, command)
        if not output:
            return None

        version_info = self.parse_version_info(output, device.vendor)
        version_info["device_id"] = device.id
        return version_info

    async def collect_device_serial(self, device: Device) -> Optional[str]:
        """
        采集设备序列号

        Args:
            device: 设备对象

        Returns:
            序列号字符串，失败返回None
        """
        print(f"[INFO] Starting serial collection for device {device.hostname} ({device.ip_address})")
        
        if not device.username or not device.password:
            print(f"[ERROR] Device {device.hostname} ({device.ip_address}) missing credentials")
            return None

        connection = None
        try:
            # 建立一次连接，执行多个命令
            connection = await self.connect_to_device(device)
            if not connection:
                print(f"[ERROR] Failed to connect to device {device.hostname} ({device.ip_address}) for serial collection")
                return None

            loop = asyncio.get_event_loop()
            
            # 先从版本命令中尝试获取
            version_command = self.get_commands(device.vendor, "version")
            if version_command:
                print(f"[INFO] Executing version command on {device.hostname}: {version_command}")
                try:
                    output = await loop.run_in_executor(
                        None,
                        lambda: connection.send_command(version_command, read_timeout=20)
                    )
                    if output:
                        print(f"[INFO] Version command output received from {device.hostname}")
                        serial = self.parse_serial_from_version(output, device.vendor)
                        if serial:
                            print(f"[SUCCESS] Found serial from version output: {serial} for {device.hostname}")
                            return serial
                        else:
                            print(f"[INFO] Serial not found in version output for {device.hostname}")
                    else:
                        print(f"[WARNING] Version command returned empty output for {device.hostname}")
                except Exception as e:
                    print(f"[ERROR] Error executing version command on {device.hostname}: {e}")

            # 如果版本命令中没有，尝试inventory命令
            inventory_command = self.get_commands(device.vendor, "inventory")
            if inventory_command:
                print(f"[INFO] Executing inventory command on {device.hostname}: {inventory_command}")
                try:
                    output = await loop.run_in_executor(
                        None,
                        lambda: connection.send_command(inventory_command, read_timeout=20)
                    )
                    if output:
                        print(f"[INFO] Inventory command output received from {device.hostname}")
                        serial = self.parse_serial_from_inventory(output, device.vendor)
                        if serial:
                            print(f"[SUCCESS] Found serial from inventory output: {serial} for {device.hostname}")
                            return serial
                        else:
                            print(f"[INFO] Serial not found in inventory output for {device.hostname}")
                    else:
                        print(f"[WARNING] Inventory command returned empty output for {device.hostname}")
                except Exception as e:
                    print(f"[ERROR] Error executing inventory command on {device.hostname}: {e}")

            print(f"[ERROR] No serial found for device {device.hostname} ({device.ip_address})")
            return None
            
        except Exception as e:
            print(f"[ERROR] Unexpected error collecting serial for device {device.hostname} ({device.ip_address}): {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if connection:
                try:
                    connection.disconnect()
                    print(f"[INFO] Disconnected from device {device.hostname}")
                except Exception as e:
                    print(f"[WARNING] Error disconnecting from device {device.hostname}: {e}")

    async def collect_interfaces_info(self, device: Device) -> Optional[List[Dict[str, Any]]]:
        """
        采集设备接口信息

        Args:
            device: 设备对象

        Returns:
            接口信息列表，失败返回None
        """
        if not device.username or not device.password:
            print(f"Device {device.hostname} missing credentials")
            return None

        interfaces_command = self.get_commands(device.vendor, "interfaces")
        if not interfaces_command:
            return None

        connection = None
        try:
            # 建立一次连接，执行多个命令
            connection = await self.connect_to_device(device)
            if not connection:
                print(f"Failed to connect to device {device.hostname} for interface collection")
                return None

            loop = asyncio.get_event_loop()
            
            # 获取接口详细信息
            print(f"Executing interfaces command on {device.hostname}: {interfaces_command}")
            interfaces_output = await loop.run_in_executor(
                None,
                lambda: connection.send_command(interfaces_command, read_timeout=30)
            )
            
            if not interfaces_output:
                print(f"No interfaces output received from {device.hostname}")
                return None

            # 如果有状态命令，也获取状态信息
            status_output = None
            status_command = self.get_commands(device.vendor, "interfaces_status")
            if status_command and status_command != interfaces_command:
                print(f"Executing interfaces status command on {device.hostname}: {status_command}")
                status_output = await loop.run_in_executor(
                    None,
                    lambda: connection.send_command(status_command, read_timeout=30)
                )

            interfaces_info = self.parse_interfaces_info(interfaces_output, status_output, device.vendor)

            # 添加device_id到每个接口
            for interface in interfaces_info:
                interface["device_id"] = device.id

            print(f"Collected {len(interfaces_info)} interfaces from {device.hostname}")
            return interfaces_info if interfaces_info else None
            
        except Exception as e:
            print(f"Error collecting interfaces for device {device.hostname}: {e}")
            return None
        finally:
            if connection:
                try:
                    connection.disconnect()
                    print(f"Disconnected from device {device.hostname}")
                except:
                    pass

    async def collect_mac_table(self, device: Device) -> Optional[List[Dict[str, Any]]]:
        """
        采集设备MAC地址表

        Args:
            device: 设备对象

        Returns:
            MAC地址条目列表，失败返回None
        """
        if not device.username or not device.password:
            print(f"Device {device.hostname} missing credentials")
            return None

        mac_command = self.get_commands(device.vendor, "mac_table")
        if not mac_command:
            return None

        output = await self.execute_command(device, mac_command)
        if not output:
            return None

        mac_table = self.parse_mac_table(output, device.vendor)

        # 添加device_id到每个MAC条目
        for mac_entry in mac_table:
            mac_entry["device_id"] = device.id

        return mac_table if mac_table else None

    async def collect_running_config(self, device: Device) -> Optional[str]:
        """
        采集设备运行配置

        Args:
            device: 设备对象

        Returns:
            运行配置字符串，失败返回None
        """
        if not device.username or not device.password:
            print(f"Device {device.hostname} missing credentials")
            return None

        command = self.get_commands(device.vendor, "running_config")
        if not command:
            return None

        output = await self.execute_command(device, command)
        return output if output else None

    async def batch_collect_device_info(
        self,
        devices: List[Device],
        collect_types: List[str]
    ) -> Dict[str, Any]:
        """
        批量采集设备信息

        Args:
            devices: 设备对象列表
            collect_types: 采集类型列表，如 ["version", "serial", "interfaces", "mac_table", "running_config"]

        Returns:
            批量采集结果字典
        """
        results = {
            "total": len(devices),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for device in devices:
            detail = {
                "device_id": device.id,
                "hostname": device.hostname,
                "success": False,
                "data": {},
                "error": None
            }

            try:
                # 采集版本信息
                if "version" in collect_types:
                    version_info = await self.collect_device_version(device)
                    if version_info:
                        detail["data"]["version"] = version_info

                # 采集序列号
                if "serial" in collect_types:
                    serial = await self.collect_device_serial(device)
                    if serial:
                        detail["data"]["serial"] = serial

                # 采集接口信息
                if "interfaces" in collect_types:
                    interfaces = await self.collect_interfaces_info(device)
                    if interfaces:
                        detail["data"]["interfaces"] = interfaces

                # 采集MAC地址表
                if "mac_table" in collect_types:
                    mac_table = await self.collect_mac_table(device)
                    if mac_table:
                        detail["data"]["mac_table"] = mac_table
                        
                # 采集运行配置
                if "running_config" in collect_types:
                    running_config = await self.collect_running_config(device)
                    if running_config:
                        detail["data"]["running_config"] = running_config

                # 判断是否至少有一种数据采集成功
                if detail["data"]:
                    detail["success"] = True
                    results["success"] += 1
                else:
                    detail["error"] = "未采集到任何有效数据"
                    results["failed"] += 1

            except Exception as e:
                detail["error"] = str(e)
                results["failed"] += 1

            results["details"].append(detail)

        return results


# 创建全局NetmikoService实例
netmiko_service = NetmikoService()


def get_netmiko_service() -> NetmikoService:
    """
    获取Netmiko服务实例

    Returns:
        Netmiko服务实例
    """
    return netmiko_service
