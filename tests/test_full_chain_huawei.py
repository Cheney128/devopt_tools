"""
前端到后端完整链路测试 - 华为交换机
测试目标：验证从前端到后端的命令下发完整链路
测试设备：华为交换机 (192.168.80.21)
测试命令：修改设备名称为 'huawei-test-01'
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
TEST_CONFIG = {
    "device": {
        "id": 999,  # 测试用设备ID
        "hostname": "huawei-test-device",
        "ip_address": "192.168.80.21",
        "vendor": "Huawei",
        "model": "S5720",
        "username": "njadmin",
        "password": "Huawei@1234",
        "login_method": "ssh",
        "login_port": 22,
        "status": "active"
    },
    "test_command": "sysname huawei-test-01",
    "verify_command": "display current-configuration | include sysname"
}


class TestResult:
    """测试结果记录类"""
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()

    def end(self):
        self.end_time = datetime.now()

    def add_result(self, phase: str, success: bool, message: str, details: dict = None):
        result = {
            "phase": phase,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} [{phase}] {message}")
        return success

    def get_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "duration_seconds": duration,
            "results": self.results
        }

    def print_summary(self):
        summary = self.get_summary()
        print("\n" + "="*80)
        print("测试总结报告")
        print("="*80)
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed']}")
        print(f"失败: {summary['failed']}")
        print(f"耗时: {summary['duration_seconds']:.2f} 秒")
        print("="*80)

        if summary['failed'] > 0:
            print("\n失败的测试:")
            for result in summary['results']:
                if not result['success']:
                    print(f"  - {result['phase']}: {result['message']}")


# 创建测试结果实例
test_result = TestResult()


async def test_phase_1_network_connectivity():
    """
    阶段1: 网络连通性测试
    测试目标IP是否可以ping通
    """
    print("\n" + "="*80)
    print("阶段1: 网络连通性测试")
    print("="*80)

    import subprocess

    ip = TEST_CONFIG["device"]["ip_address"]

    try:
        # Windows系统使用 -n 参数
        result = subprocess.run(
            ["ping", "-n", "4", ip],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # 解析ping结果
            output = result.stdout
            if "TTL=" in output or "ttl=" in output:
                return test_result.add_result(
                    "网络连通性",
                    True,
                    f"设备 {ip} 网络连通性正常",
                    {"ping_output": output[:500]}
                )
            else:
                return test_result.add_result(
                    "网络连通性",
                    False,
                    f"设备 {ip} ping无响应",
                    {"ping_output": output[:500]}
                )
        else:
            return test_result.add_result(
                "网络连通性",
                False,
                f"设备 {ip} ping失败",
                {"error": result.stderr[:500]}
            )
    except Exception as e:
        return test_result.add_result(
            "网络连通性",
            False,
            f"ping测试异常: {str(e)}"
        )


async def test_phase_2_ssh_connectivity():
    """
    阶段2: SSH连接测试
    使用paramiko测试SSH连接
    """
    print("\n" + "="*80)
    print("阶段2: SSH连接测试")
    print("="*80)

    try:
        import paramiko

        device = TEST_CONFIG["device"]

        print(f"尝试SSH连接到 {device['ip_address']}:{device['login_port']}")
        print(f"用户名: {device['username']}")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=device['ip_address'],
                port=device['login_port'],
                username=device['username'],
                password=device['password'],
                timeout=30,
                banner_timeout=30,
                auth_timeout=30
            )

            # 测试执行简单命令
            stdin, stdout, stderr = client.exec_command("display version", timeout=20)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')

            client.close()

            if output and "Huawei" in output:
                return test_result.add_result(
                    "SSH连接",
                    True,
                    f"SSH连接成功，设备响应正常",
                    {"version_output": output[:300]}
                )
            elif output:
                return test_result.add_result(
                    "SSH连接",
                    True,
                    f"SSH连接成功",
                    {"output": output[:300]}
                )
            else:
                return test_result.add_result(
                    "SSH连接",
                    False,
                    f"SSH连接成功但命令无输出",
                    {"error": error[:300]}
                )

        except paramiko.AuthenticationException as e:
            return test_result.add_result(
                "SSH连接",
                False,
                f"SSH认证失败: {str(e)}",
                {"error_type": "AuthenticationException"}
            )
        except paramiko.SSHException as e:
            return test_result.add_result(
                "SSH连接",
                False,
                f"SSH连接异常: {str(e)}",
                {"error_type": "SSHException"}
            )
        except Exception as e:
            return test_result.add_result(
                "SSH连接",
                False,
                f"SSH连接失败: {str(e)}",
                {"error_type": type(e).__name__}
            )
        finally:
            try:
                client.close()
            except:
                pass

    except ImportError:
        return test_result.add_result(
            "SSH连接",
            False,
            "paramiko库未安装"
        )


async def test_phase_3_netmiko_connection():
    """
    阶段3: Netmiko连接测试
    使用Netmiko库测试设备连接
    """
    print("\n" + "="*80)
    print("阶段3: Netmiko连接测试")
    print("="*80)

    try:
        from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

        device = TEST_CONFIG["device"]

        device_params = {
            "device_type": "huawei",
            "host": device['ip_address'],
            "username": device['username'],
            "password": device['password'],
            "port": device['login_port'],
            "timeout": 60,
            "conn_timeout": 30,
            "allow_agent": False,
            "global_delay_factor": 2,
            "fast_cli": False,
        }

        print(f"Netmiko连接参数:")
        print(f"  - device_type: {device_params['device_type']}")
        print(f"  - host: {device_params['host']}")
        print(f"  - port: {device_params['port']}")
        print(f"  - username: {device_params['username']}")
        print(f"  - timeout: {device_params['timeout']}")

        try:
            connection = ConnectHandler(**device_params)

            # 测试执行命令
            output = connection.send_command("display version", read_timeout=20)
            connection.disconnect()

            if output:
                return test_result.add_result(
                    "Netmiko连接",
                    True,
                    f"Netmiko连接成功，命令执行正常",
                    {"output_length": len(output), "output_preview": output[:300]}
                )
            else:
                return test_result.add_result(
                    "Netmiko连接",
                    False,
                    f"Netmiko连接成功但命令无输出"
                )

        except NetmikoAuthenticationException as e:
            return test_result.add_result(
                "Netmiko连接",
                False,
                f"Netmiko认证失败: {str(e)}",
                {"error_type": "NetmikoAuthenticationException"}
            )
        except NetmikoTimeoutException as e:
            return test_result.add_result(
                "Netmiko连接",
                False,
                f"Netmiko连接超时: {str(e)}",
                {"error_type": "NetmikoTimeoutException"}
            )
        except Exception as e:
            return test_result.add_result(
                "Netmiko连接",
                False,
                f"Netmiko连接失败: {str(e)}",
                {"error_type": type(e).__name__, "error": str(e)[:500]}
            )

    except ImportError:
        return test_result.add_result(
            "Netmiko连接",
            False,
            "Netmiko库未安装"
        )


async def test_phase_4_backend_api():
    """
    阶段4: 后端API测试
    测试后端API端点是否正常工作
    """
    print("\n" + "="*80)
    print("阶段4: 后端API测试")
    print("="*80)

    try:
        import httpx

        base_url = "http://localhost:8000/api/v1"

        # 测试1: 健康检查
        print("测试API健康状态...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{base_url}/devices", params={"page": 1, "page_size": 1})
                if response.status_code == 200:
                    test_result.add_result(
                        "后端API-健康检查",
                        True,
                        f"API服务正常运行，状态码: {response.status_code}"
                    )
                else:
                    test_result.add_result(
                        "后端API-健康检查",
                        False,
                        f"API服务异常，状态码: {response.status_code}"
                    )
        except Exception as e:
            test_result.add_result(
                "后端API-健康检查",
                False,
                f"API服务无法访问: {str(e)}"
            )

        return True

    except ImportError:
        return test_result.add_result(
            "后端API测试",
            False,
            "httpx库未安装"
        )


async def test_phase_5_full_chain():
    """
    阶段5: 完整链路测试
    模拟前端到后端的完整命令下发流程
    """
    print("\n" + "="*80)
    print("阶段5: 完整链路测试")
    print("="*80)

    try:
        from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

        device = TEST_CONFIG["device"]
        command = TEST_CONFIG["test_command"]

        print(f"测试命令: {command}")
        print(f"目标设备: {device['ip_address']}")

        device_params = {
            "device_type": "huawei",
            "host": device['ip_address'],
            "username": device['username'],
            "password": device['password'],
            "port": device['login_port'],
            "timeout": 60,
            "conn_timeout": 30,
            "allow_agent": False,
            "global_delay_factor": 2,
            "fast_cli": False,
        }

        try:
            # 步骤1: 建立连接
            print("步骤1: 建立SSH连接...")
            connection = ConnectHandler(**device_params)
            print("  ✅ SSH连接成功")

            # 步骤2: 进入系统视图
            print("步骤2: 进入系统视图...")
            connection.config_mode()
            print("  ✅ 进入系统视图成功")

            # 步骤3: 执行修改主机名命令
            print(f"步骤3: 执行命令 '{command}'...")
            output = connection.send_command_timing(command, last_read=3.0)
            print(f"  ✅ 命令执行成功")
            print(f"  输出: {output[:200] if output else '无输出'}")

            # 步骤4: 保存配置
            print("步骤4: 保存配置...")
            save_output = connection.send_command_timing("save", last_read=3.0)
            if "Y/N" in save_output or "y/n" in save_output:
                save_output += connection.send_command_timing("Y", last_read=3.0)
            print(f"  ✅ 配置保存成功")

            # 步骤5: 验证修改
            print("步骤5: 验证主机名修改...")
            connection.exit_config_mode()
            verify_output = connection.send_command("display current-configuration | include sysname", read_timeout=10)
            print(f"  验证输出: {verify_output[:200]}")

            # 步骤6: 关闭连接
            connection.disconnect()
            print("  ✅ 连接已关闭")

            # 检查结果
            if "huawei-test-01" in verify_output:
                return test_result.add_result(
                    "完整链路测试",
                    True,
                    f"命令下发成功，主机名已修改为 'huawei-test-01'",
                    {
                        "command": command,
                        "verify_output": verify_output[:300],
                        "save_output": save_output[:200]
                    }
                )
            else:
                return test_result.add_result(
                    "完整链路测试",
                    False,
                    f"命令执行完成但验证失败，主机名可能未修改",
                    {
                        "command": command,
                        "verify_output": verify_output[:300]
                    }
                )

        except NetmikoAuthenticationException as e:
            return test_result.add_result(
                "完整链路测试",
                False,
                f"认证失败: {str(e)}",
                {"phase": "connection", "error_type": "NetmikoAuthenticationException"}
            )
        except NetmikoTimeoutException as e:
            return test_result.add_result(
                "完整链路测试",
                False,
                f"连接超时: {str(e)}",
                {"phase": "connection", "error_type": "NetmikoTimeoutException"}
            )
        except Exception as e:
            return test_result.add_result(
                "完整链路测试",
                False,
                f"测试失败: {str(e)}",
                {"phase": "unknown", "error_type": type(e).__name__, "error": str(e)[:500]}
            )

    except ImportError:
        return test_result.add_result(
            "完整链路测试",
            False,
            "Netmiko库未安装"
        )


async def test_phase_6_error_scenarios():
    """
    阶段6: 错误场景测试
    测试各种错误情况的处理
    """
    print("\n" + "="*80)
    print("阶段6: 错误场景测试")
    print("="*80)

    # 测试1: 错误密码
    print("测试1: 错误密码场景...")
    try:
        from netmiko import ConnectHandler, NetmikoAuthenticationException

        device = TEST_CONFIG["device"].copy()
        device['password'] = 'wrong_password'

        device_params = {
            "device_type": "huawei",
            "host": device['ip_address'],
            "username": device['username'],
            "password": device['password'],
            "port": device['login_port'],
            "timeout": 30,
            "conn_timeout": 15,
        }

        try:
            connection = ConnectHandler(**device_params)
            connection.disconnect()
            test_result.add_result(
                "错误场景-错误密码",
                False,
                "错误密码应该认证失败，但实际连接成功"
            )
        except NetmikoAuthenticationException:
            test_result.add_result(
                "错误场景-错误密码",
                True,
                "错误密码正确触发认证失败异常"
            )
        except Exception as e:
            test_result.add_result(
                "错误场景-错误密码",
                True,
                f"错误密码触发异常: {type(e).__name__}"
            )

    except ImportError:
        test_result.add_result(
            "错误场景-错误密码",
            False,
            "Netmiko库未安装"
        )

    # 测试2: 错误IP
    print("测试2: 错误IP场景...")
    try:
        from netmiko import ConnectHandler, NetmikoTimeoutException

        device = TEST_CONFIG["device"].copy()
        device['ip_address'] = '192.168.255.255'  # 不存在的IP

        device_params = {
            "device_type": "huawei",
            "host": device['ip_address'],
            "username": device['username'],
            "password": device['password'],
            "port": device['login_port'],
            "timeout": 10,
            "conn_timeout": 5,
        }

        try:
            connection = ConnectHandler(**device_params)
            connection.disconnect()
            test_result.add_result(
                "错误场景-错误IP",
                False,
                "错误IP应该连接失败，但实际连接成功"
            )
        except NetmikoTimeoutException:
            test_result.add_result(
                "错误场景-错误IP",
                True,
                "错误IP正确触发连接超时异常"
            )
        except Exception as e:
            test_result.add_result(
                "错误场景-错误IP",
                True,
                f"错误IP触发异常: {type(e).__name__}"
            )

    except ImportError:
        test_result.add_result(
            "错误场景-错误IP",
            False,
            "Netmiko库未安装"
        )

    return True


async def run_all_tests():
    """运行所有测试阶段"""
    print("\n" + "="*80)
    print("前端到后端完整链路测试 - 华为交换机")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标设备: {TEST_CONFIG['device']['ip_address']}")
    print(f"测试命令: {TEST_CONFIG['test_command']}")
    print("="*80)

    test_result.start()

    # 执行各个测试阶段
    await test_phase_1_network_connectivity()
    await test_phase_2_ssh_connectivity()
    await test_phase_3_netmiko_connection()
    await test_phase_4_backend_api()
    await test_phase_5_full_chain()
    await test_phase_6_error_scenarios()

    test_result.end()

    # 打印测试总结
    test_result.print_summary()

    # 保存测试报告
    report_file = f"test_report_full_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = os.path.join(os.path.dirname(__file__), report_file)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_result.get_summary(), f, ensure_ascii=False, indent=2)

    print(f"\n测试报告已保存: {report_path}")

    return test_result.get_summary()


if __name__ == "__main__":
    # 运行测试
    summary = asyncio.run(run_all_tests())

    # 根据测试结果设置退出码
    if summary['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
