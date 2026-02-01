"""
验证修复后的Netmiko服务
测试目标：192.168.80.21
测试命令：修改主机名
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.netmiko_service import NetmikoService

class MockDevice:
    def __init__(self):
        self.id = 1
        self.hostname = "huawei"
        self.ip_address = "192.168.80.21"
        self.vendor = "huawei"
        self.username = "njadmin"
        self.password = "Huawei@1234"
        self.login_port = 22
        self.login_method = "ssh"

async def test_fix():
    """测试修复后的命令执行"""
    print("=" * 60)
    print("验证修复: Netmiko服务配置命令执行")
    print("=" * 60)

    device = MockDevice()
    netmiko_service = NetmikoService()

    try:
        # 测试1: 查看当前主机名
        print("\n[测试1] 查看当前主机名...")
        output = await netmiko_service.execute_command(
            device,
            "display current-configuration | include sysname"
        )
        print(f"输出: {output.strip() if output else '无'}")

        # 测试2: 进入system-view
        print("\n[测试2] 进入system-view...")
        output = await netmiko_service.execute_command(
            device,
            "system-view"
        )
        print(f"输出: {output.strip()[-100:] if output else '无'}")

        # 测试3: 修改主机名
        print("\n[测试3] 修改主机名为 test-fix...")
        output = await netmiko_service.execute_command(
            device,
            "sysname test-fix"
        )
        print(f"输出: {output.strip()[-100:] if output else '无'}")

        # 测试4: 提交配置
        print("\n[测试4] 提交配置...")
        output = await netmiko_service.execute_command(
            device,
            "commit"
        )
        print(f"输出: {output.strip()[-200:] if output else '无'}")

        # 测试5: 退出system-view
        print("\n[测试5] 退出system-view...")
        output = await netmiko_service.execute_command(
            device,
            "return"
        )
        print(f"输出: {output.strip()[-100:] if output else '无'}")

        # 测试6: 验证修改
        print("\n[测试6] 验证主机名修改...")
        output = await netmiko_service.execute_command(
            device,
            "display current-configuration | include sysname"
        )
        print(f"输出: {output.strip() if output else '无'}")

        if output and "test-fix" in output:
            print("\n" + "=" * 60)
            print("OK 修复验证成功! 主机名已修改为 test-fix")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("FAIL 修复验证失败! 主机名未修改")
            print("=" * 60)
            return False

    except Exception as e:
        print("\nFAIL 测试失败: " + str(e))
        import traceback
        traceback.print_exc()
        return False