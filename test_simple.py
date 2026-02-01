"""简单测试修复"""
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

async def test():
    print("=" * 60)
    print("测试修复后的Netmiko服务")
    print("=" * 60)

    device = MockDevice()
    service = NetmikoService()

    # 测试配置命令检测
    print("\n[测试] 配置命令检测:")
    test_cmds = ["system-view", "sysname test", "display version", "commit"]
    for cmd in test_cmds:
        is_config = service._is_config_command(cmd, "huawei")
        print(f"  {cmd}: {'配置命令' if is_config else '查询命令'}")

    # 测试expect字符串获取
    print("\n[测试] Expect字符串:")
    expects = service._get_vendor_expect_strings("huawei")
    for k, v in expects.items():
        print(f"  {k}: {v}")

    # 测试实际连接和命令执行
    print("\n[测试] 实际命令执行:")
    print("  连接设备...")

    try:
        # 执行查询命令
        output = await service.execute_command(device, "display current-configuration | include sysname")
        print(f"  当前主机名: {output.strip() if output else '无'}")

        # 执行配置命令
        print("  进入system-view...")
        output = await service.execute_command(device, "system-view")
        print(f"  结果: {'成功' if output is not None else '失败'}")

        print("  修改主机名...")
        output = await service.execute_command(device, "sysname test123")
        print(f"  结果: {'成功' if output is not None else '失败'}")

        print("  提交配置...")
        output = await service.execute_command(device, "commit")
        print(f"  结果: {'成功' if output is not None else '失败'}")

        print("  退出system-view...")
        output = await service.execute_command(device, "return")
        print(f"  结果: {'成功' if output is not None else '失败'}")

        # 验证
        output = await service.execute_command(device, "display current-configuration | include sysname")
        print(f"\n  验证主机名: {output.strip() if output else '无'}")

        if output and "test123" in output:
            print("\n" + "=" * 60)
            print("OK 修复成功! 主机名已修改为 test123")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("FAIL 修复失败")
            print("=" * 60)
            return False

    except Exception as e:
        print("FAIL 错误: " + str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
