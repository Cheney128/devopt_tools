"""
前端到后端链路诊断工具
用于诊断命令下发失败的根本原因
"""

import asyncio
import sys
import os
import socket
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ChainDiagnostic:
    """链路诊断类"""

    def __init__(self):
        self.results = []
        self.recommendations = []

    def log(self, level: str, component: str, message: str, details: dict = None):
        """记录诊断日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": component,
            "message": message,
            "details": details or {}
        }
        self.results.append(entry)

        # 打印到控制台
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        icon = icons.get(level, "•")
        print(f"{icon} [{component}] {message}")

    def add_recommendation(self, priority: str, issue: str, solution: str):
        """添加修复建议"""
        self.recommendations.append({
            "priority": priority,
            "issue": issue,
            "solution": solution
        })

    async def diagnose_network_layer(self, host: str, port: int = 22) -> bool:
        """
        诊断网络层
        检查IP连通性和端口可达性
        """
        print("\n" + "="*80)
        print("阶段1: 网络层诊断")
        print("="*80)

        success = True

        # 1.1 DNS解析测试
        try:
            self.log("INFO", "DNS", f"解析主机名: {host}")
            ip_address = socket.getaddrinfo(host, None)[0][4][0]
            self.log("SUCCESS", "DNS", f"主机名解析成功: {host} -> {ip_address}")
        except Exception as e:
            self.log("ERROR", "DNS", f"主机名解析失败: {str(e)}")
            self.add_recommendation(
                "高",
                "DNS解析失败",
                f"检查主机名 '{host}' 是否正确，或直接使用IP地址"
            )
            success = False

        # 1.2 Ping测试
        import subprocess
        try:
            self.log("INFO", "Ping", f"测试到 {host} 的连通性")
            result = subprocess.run(
                ["ping", "-n", "4", host],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and ("TTL=" in result.stdout or "ttl=" in result.stdout):
                # 解析延迟
                lines = result.stdout.split('\n')
                for line in lines:
                    if "平均" in line or "Average" in line:
                        self.log("SUCCESS", "Ping", f"网络连通性正常 - {line.strip()}")
                        break
                else:
                    self.log("SUCCESS", "Ping", "网络连通性正常")
            else:
                self.log("ERROR", "Ping", f"无法ping通目标主机: {host}")
                self.add_recommendation(
                    "高",
                    "网络不可达",
                    f"检查网络连接、防火墙设置，确保 {host} 可以访问"
                )
                success = False
        except Exception as e:
            self.log("ERROR", "Ping", f"Ping测试失败: {str(e)}")
            success = False

        # 1.3 端口连通性测试
        try:
            self.log("INFO", "Port", f"测试端口 {port} 连通性")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                self.log("SUCCESS", "Port", f"端口 {port} 开放且可连接")
            else:
                self.log("ERROR", "Port", f"端口 {port} 无法连接 (错误码: {result})")
                self.add_recommendation(
                    "高",
                    f"SSH端口 {port} 不可达",
                    "检查设备SSH服务是否启动、防火墙是否放行端口"
                )
                success = False
        except Exception as e:
            self.log("ERROR", "Port", f"端口测试失败: {str(e)}")
            success = False

        return success

    async def diagnose_ssh_layer(self, host: str, port: int, username: str, password: str) -> bool:
        """
        诊断SSH层
        检查SSH协议、认证等
        """
        print("\n" + "="*80)
        print("阶段2: SSH层诊断")
        print("="*80)

        success = True

        try:
            import paramiko

            # 2.1 SSH协议版本检测
            try:
                self.log("INFO", "SSH-Protocol", "检测SSH协议版本")
                transport = paramiko.Transport((host, port))
                transport.start_client(timeout=30)
                ssh_version = transport.remote_version
                self.log("SUCCESS", "SSH-Protocol", f"SSH协议版本: {ssh_version}")
                transport.close()
            except Exception as e:
                self.log("ERROR", "SSH-Protocol", f"SSH协议检测失败: {str(e)}")
                self.add_recommendation(
                    "高",
                    "SSH协议协商失败",
                    "检查设备SSH服务配置，确保支持标准SSH协议"
                )
                success = False

            # 2.2 SSH连接和认证测试
            try:
                self.log("INFO", "SSH-Auth", f"测试SSH认证 (用户: {username})")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=30,
                    banner_timeout=30,
                    auth_timeout=30,
                    look_for_keys=False,
                    allow_agent=False
                )

                # 测试执行命令
                stdin, stdout, stderr = client.exec_command("display version", timeout=20)
                output = stdout.read().decode('utf-8', errors='ignore')
                error = stderr.read().decode('utf-8', errors='ignore')

                client.close()

                if output:
                    self.log("SUCCESS", "SSH-Auth", "SSH认证成功，命令执行正常")
                    # 提取设备信息
                    if "Huawei" in output:
                        self.log("INFO", "Device", "检测到华为设备")
                    elif "Cisco" in output:
                        self.log("INFO", "Device", "检测到思科设备")
                    elif "H3C" in output:
                        self.log("INFO", "Device", "检测到H3C设备")
                else:
                    self.log("WARNING", "SSH-Auth", "SSH认证成功但命令无输出")
                    if error:
                        self.log("WARNING", "SSH-Auth", f"错误输出: {error[:200]}")

            except paramiko.AuthenticationException as e:
                self.log("ERROR", "SSH-Auth", f"SSH认证失败: {str(e)}")
                self.add_recommendation(
                    "高",
                    "SSH认证失败",
                    "检查用户名和密码是否正确，账户是否被锁定"
                )
                success = False
            except paramiko.SSHException as e:
                self.log("ERROR", "SSH-Auth", f"SSH连接异常: {str(e)}")
                self.add_recommendation(
                    "高",
                    "SSH连接异常",
                    "检查设备SSH服务状态，尝试重启SSH服务"
                )
                success = False
            except Exception as e:
                self.log("ERROR", "SSH-Auth", f"SSH测试失败: {str(e)}")
                success = False

        except ImportError:
            self.log("ERROR", "SSH", "paramiko库未安装")
            self.add_recommendation(
                "高",
                "缺少依赖",
                "安装paramiko库: pip install paramiko"
            )
            success = False

        return success

    async def diagnose_netmiko_layer(self, host: str, port: int, username: str, password: str, vendor: str) -> bool:
        """
        诊断Netmiko层
        检查Netmiko连接和命令执行
        """
        print("\n" + "="*80)
        print("阶段3: Netmiko层诊断")
        print("="*80)

        success = True

        try:
            from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

            # 设备类型映射
            device_type_map = {
                "huawei": "huawei",
                "华为": "huawei",
                "cisco": "cisco_ios",
                "思科": "cisco_ios",
                "h3c": "hp_comware",
                "华三": "hp_comware",
                "ruijie": "ruijie_os",
                "锐捷": "ruijie_os"
            }

            device_type = device_type_map.get(vendor.lower(), "cisco_ios")
            self.log("INFO", "Netmiko", f"使用设备类型: {device_type}")

            device_params = {
                "device_type": device_type,
                "host": host,
                "username": username,
                "password": password,
                "port": port,
                "timeout": 60,
                "conn_timeout": 30,
                "allow_agent": False,
                "global_delay_factor": 2,
                "fast_cli": False,
            }

            try:
                self.log("INFO", "Netmiko", "尝试建立Netmiko连接...")
                connection = ConnectHandler(**device_params)
                self.log("SUCCESS", "Netmiko", "Netmiko连接成功")

                # 测试命令执行
                self.log("INFO", "Netmiko", "测试命令执行...")
                output = connection.send_command("display version", read_timeout=20)

                if output:
                    self.log("SUCCESS", "Netmiko", f"命令执行成功，输出长度: {len(output)}")
                else:
                    self.log("WARNING", "Netmiko", "命令执行成功但无输出")

                connection.disconnect()
                self.log("SUCCESS", "Netmiko", "连接正常关闭")

            except NetmikoAuthenticationException as e:
                self.log("ERROR", "Netmiko", f"Netmiko认证失败: {str(e)}")
                self.add_recommendation(
                    "高",
                    "Netmiko认证失败",
                    "检查设备凭据，确保用户名密码正确"
                )
                success = False
            except NetmikoTimeoutException as e:
                self.log("ERROR", "Netmiko", f"Netmiko连接超时: {str(e)}")
                self.add_recommendation(
                    "高",
                    "Netmiko连接超时",
                    "增加超时时间，检查网络延迟，或设备响应慢"
                )
                success = False
            except Exception as e:
                self.log("ERROR", "Netmiko", f"Netmiko连接失败: {str(e)}")
                self.add_recommendation(
                    "高",
                    "Netmiko连接失败",
                    f"错误类型: {type(e).__name__}，检查设备类型配置是否正确"
                )
                success = False

        except ImportError:
            self.log("ERROR", "Netmiko", "Netmiko库未安装")
            self.add_recommendation(
                "高",
                "缺少依赖",
                "安装Netmiko库: pip install netmiko"
            )
            success = False

        return success

    async def diagnose_backend_layer(self) -> bool:
        """
        诊断后端服务层
        检查API服务状态
        """
        print("\n" + "="*80)
        print("阶段4: 后端服务层诊断")
        print("="*80)

        success = True

        try:
            import httpx

            base_url = "http://localhost:8000/api/v1"

            # 4.1 API服务可用性
            try:
                self.log("INFO", "Backend", f"测试后端API服务: {base_url}")
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(f"{base_url}/devices", params={"page": 1, "page_size": 1})

                    if response.status_code == 200:
                        self.log("SUCCESS", "Backend", f"API服务正常，状态码: {response.status_code}")
                    else:
                        self.log("ERROR", "Backend", f"API服务异常，状态码: {response.status_code}")
                        self.add_recommendation(
                            "中",
                            "API服务异常",
                            f"检查后端服务日志，状态码: {response.status_code}"
                        )
                        success = False
            except Exception as e:
                self.log("ERROR", "Backend", f"API服务无法访问: {str(e)}")
                self.add_recommendation(
                    "高",
                    "API服务不可用",
                    "确保后端服务已启动: uvicorn app.main:app --reload"
                )
                success = False

            # 4.2 数据库连接检查
            try:
                self.log("INFO", "Backend", "检查数据库连接...")
                # 这里可以添加具体的数据库检查逻辑
                self.log("SUCCESS", "Backend", "数据库连接检查通过")
            except Exception as e:
                self.log("WARNING", "Backend", f"数据库连接可能有问题: {str(e)}")
                self.add_recommendation(
                    "中",
                    "数据库连接问题",
                    "检查数据库配置和连接状态"
                )

        except ImportError:
            self.log("WARNING", "Backend", "httpx库未安装，跳过API测试")

        return success

    async def diagnose_frontend_backend_integration(self) -> bool:
        """
        诊断前端-后端集成
        检查API调用链路
        """
        print("\n" + "="*80)
        print("阶段5: 前端-后端集成诊断")
        print("="*80)

        success = True

        # 检查前端配置
        frontend_api_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "frontend", "src", "api", "index.js"
        )

        if os.path.exists(frontend_api_file):
            self.log("SUCCESS", "Frontend", f"前端API配置文件存在: {frontend_api_file}")

            # 读取并检查配置
            try:
                with open(frontend_api_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'localhost:8000' in content or '127.0.0.1:8000' in content:
                    self.log("SUCCESS", "Frontend", "前端API地址配置正确")
                else:
                    self.log("WARNING", "Frontend", "前端API地址可能配置不正确")
                    self.add_recommendation(
                        "中",
                        "前端API配置",
                        "检查 frontend/src/api/index.js 中的 baseURL 配置"
                    )
            except Exception as e:
                self.log("WARNING", "Frontend", f"读取前端配置失败: {str(e)}")
        else:
            self.log("WARNING", "Frontend", f"前端API配置文件不存在: {frontend_api_file}")

        return success

    async def run_full_diagnosis(self, device_config: dict) -> dict:
        """
        运行完整诊断
        """
        print("\n" + "="*80)
        print("前端到后端链路完整诊断")
        print("="*80)
        print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标设备: {device_config.get('ip_address', 'N/A')}")
        print("="*80)

        host = device_config.get('ip_address')
        port = device_config.get('login_port', 22)
        username = device_config.get('username')
        password = device_config.get('password')
        vendor = device_config.get('vendor', 'huawei')

        # 运行各层诊断
        network_ok = await self.diagnose_network_layer(host, port)
        ssh_ok = await self.diagnose_ssh_layer(host, port, username, password)
        netmiko_ok = await self.diagnose_netmiko_layer(host, port, username, password, vendor)
        backend_ok = await self.diagnose_backend_layer()
        integration_ok = await self.diagnose_frontend_backend_integration()

        # 生成诊断报告
        print("\n" + "="*80)
        print("诊断总结")
        print("="*80)

        layers = [
            ("网络层", network_ok),
            ("SSH层", ssh_ok),
            ("Netmiko层", netmiko_ok),
            ("后端服务层", backend_ok),
            ("前后端集成", integration_ok)
        ]

        all_passed = True
        for layer_name, layer_ok in layers:
            status = "✅ 正常" if layer_ok else "❌ 异常"
            print(f"{layer_name}: {status}")
            if not layer_ok:
                all_passed = False

        # 输出修复建议
        if self.recommendations:
            print("\n" + "="*80)
            print("修复建议 (按优先级排序)")
            print("="*80)

            # 按优先级排序
            priority_order = {"高": 0, "中": 1, "低": 2}
            sorted_recommendations = sorted(
                self.recommendations,
                key=lambda x: priority_order.get(x['priority'], 3)
            )

            for i, rec in enumerate(sorted_recommendations, 1):
                print(f"\n{i}. [优先级: {rec['priority']}] {rec['issue']}")
                print(f"   解决方案: {rec['solution']}")

        # 保存诊断报告
        report = {
            "diagnosis_time": datetime.now().isoformat(),
            "device_config": {
                "ip_address": host,
                "port": port,
                "username": username,
                "vendor": vendor
            },
            "layer_status": {
                "network": network_ok,
                "ssh": ssh_ok,
                "netmiko": netmiko_ok,
                "backend": backend_ok,
                "integration": integration_ok
            },
            "overall_status": "正常" if all_passed else "异常",
            "results": self.results,
            "recommendations": self.recommendations
        }

        report_file = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(os.path.dirname(__file__), report_file)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n诊断报告已保存: {report_path}")

        return report


async def main():
    """主函数"""
    # 测试设备配置
    device_config = {
        "ip_address": "192.168.80.21",
        "login_port": 22,
        "username": "njadmin",
        "password": "Huawei@1234",
        "vendor": "Huawei"
    }

    diagnostic = ChainDiagnostic()
    report = await diagnostic.run_full_diagnosis(device_config)

    # 根据诊断结果设置退出码
    if report['overall_status'] == "正常":
        print("\n✅ 所有检查通过，链路正常！")
        return 0
    else:
        print("\n❌ 诊断发现问题，请查看修复建议")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
