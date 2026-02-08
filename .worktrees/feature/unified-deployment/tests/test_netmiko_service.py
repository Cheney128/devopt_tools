"""
Netmiko服务连接交换机测试
测试目标：192.168.80.21
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.netmiko_service import NetmikoService

# 创建设备对象模拟
class MockDevice:
    def __init__(self):
        self.id = 1
        self.hostname = "test1234"
        self.ip_address = "192.168.80.21"
        self.vendor = "huawei"
        self.username = "njadmin"
        self.password = "Huawei@1234"
        self.login_port = 22
        self.login_method = "ssh"

async def test_netmiko_service():
    """测试Netmiko服务连接交换机"""
    print("=" * 60)
    print("测试2: Netmiko服务连接交换机")
    print("=" * 60)
    print("目标设备: 192.168.80.21")
    print("用户名: njadmin")
    print("端口: 22")
    print("-" * 60)

    device = MockDevice()
    netmiko_service = NetmikoService()
    connection = None

    try:
        # 测试1: 连接设备
        print("[1/4] 测试Netmiko连接...")
        connection = await netmiko_service.connect_to_device(device)
        if connection:
            print("OK Netmiko连接成功!")
        else:
            print("FAIL Netmiko连接失败!")
            return False

        # 测试2: 执行查看主机名命令
        print("[2/4] 执行命令 'display current-configuration | include sysname'...")
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname")
        )
        if output:
            print("命令输出:")
            print(output)
            if "test1234" in output:
                print("OK 当前主机名是 test1234")
            else:
                print("WARN 无法识别主机名")
        else:
            print("FAIL 命令执行失败，无输出")
            return False

        # 测试3: 修改主机名为 huawei-test
        print("[3/4] 修改主机名为 huawei-test...")

        # 进入system-view (华为设备进入系统视图的命令)
        print("  进入system-view...")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("system-view", expect_string=r"\[.*\]")
        )
        print(f"  进入system-view输出: {output[:100] if output else '无'}")

        # 修改主机名
        print("  执行sysname huawei-test...")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("sysname huawei-test", expect_string=r"\[.*\]")
        )
        print(f"  修改主机名输出: {output[:100] if output else '无'}")

        # 提交配置
        print("  执行commit...")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("commit", expect_string=r"\[.*\]")
        )
        print(f"  提交配置输出: {output[:200] if output else '无'}")

        # 退出system-view
        print("  执行return...")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("return", expect_string=r"<.*>")
        )
        print(f"  退出system-view输出: {output[:100] if output else '无'}")

        # 测试4: 验证主机名修改
        print("[4/4] 验证主机名修改...")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname")
        )
        print("命令输出:")
        print(output)

        if output and "huawei-test" in output:
            print("OK 主机名已修改为 huawei-test")
            result = True
        else:
            print("FAIL 主机名修改验证失败")
            result = False

        print("=" * 60)
        print("测试2结果: Netmiko服务 - " + ("成功" if result else "失败"))
        print("=" * 60)
        return result

    except Exception as e:
        print("FAIL Netmiko服务测试失败: " + str(e))
        import traceback
        traceback.print_exc()
        print("=" * 60)
        print("测试2结果: Netmiko服务 - 失败")
        print("=" * 60)
        return False

    finally:
        if connection:
            connection.disconnect()
            print("[清理] 连接已断开")

if __name__ == "__main__":
    result = asyncio.run(test_netmiko_service())
    sys.exit(0 if result else 1)
