#!/usr/bin/env python3
"""
华为交换机命令执行测试 - 修改设备名称
测试通过前端到后端的完整命令下发流程
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.models import Device
from app.services.netmiko_service import NetmikoService


def create_test_device() -> Device:
    """
    创建测试设备对象
    """
    device = Device()
    device.id = 999
    device.hostname = "test-device"
    device.ip_address = "192.168.80.21"
    device.vendor = "华为"
    device.model = "S5735"
    device.login_method = "ssh"
    device.login_port = 22
    device.username = "njadmin"
    device.password = "Huawei@1234"
    device.status = "offline"
    
    return device


async def test_change_hostname():
    """
    测试修改华为交换机设备名称
    """
    print("=" * 70)
    print("华为交换机命令执行测试 - 修改设备名称")
    print("=" * 70)
    
    device = create_test_device()
    netmiko_service = NetmikoService()
    
    print(f"\n📋 设备信息:")
    print(f"   主机名: {device.hostname}")
    print(f"   IP地址: {device.ip_address}")
    print(f"   厂商: {device.vendor}")
    print(f"   型号: {device.model}")
    print(f"   登录方式: {device.login_method}")
    print(f"   端口: {device.login_port}")
    print(f"   用户名: {device.username}")
    
    device_type = netmiko_service.get_device_type(device.vendor)
    print(f"   Netmiko设备类型: {device_type}")
    
    print("\n" + "=" * 70)
    print("步骤1: 测试设备连接")
    print("=" * 70)
    
    try:
        connection = await netmiko_service.connect_to_device(device)
        if connection:
            print("✅ 设备连接成功!")
        else:
            print("❌ 设备连接失败!")
            return False
    except Exception as e:
        print(f"❌ 设备连接异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("步骤2: 查看当前设备名称")
    print("=" * 70)
    
    try:
        current_hostname_output = await netmiko_service.execute_command(device, "display current-configuration | include sysname")
        if current_hostname_output:
            print(f"📤 当前设备名称配置:")
            print(current_hostname_output)
        else:
            print("⚠️  无法获取当前设备名称")
    except Exception as e:
        print(f"❌ 获取当前设备名称失败: {e}")
    
    print("\n" + "=" * 70)
    print("步骤3: 修改设备名称为 'huawei-test-01'")
    print("=" * 70)
    
    new_hostname = "huawei-test-01"
    
    try:
        # 华为交换机修改主机名的命令序列
        commands = [
            "system-view",
            f"sysname {new_hostname}",
            "return"
        ]
        
        print(f"📤 执行命令序列:")
        for cmd in commands:
            print(f"   {cmd}")
        
        # 逐条执行命令
        for cmd in commands:
            output = await netmiko_service.execute_command(device, cmd)
            if output:
                print(f"✅ 命令 '{cmd}' 执行成功")
            else:
                print(f"❌ 命令 '{cmd}' 执行失败")
                return False
        
        print(f"\n✅ 设备名称修改为 '{new_hostname}' 成功!")
        
    except Exception as e:
        print(f"❌ 修改设备名称失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("步骤4: 验证设备名称修改结果")
    print("=" * 70)
    
    try:
        verify_output = await netmiko_service.execute_command(device, "display current-configuration | include sysname")
        if verify_output:
            print(f"📤 验证结果:")
            print(verify_output)
            
            if new_hostname in verify_output:
                print(f"✅ 设备名称已成功修改为 '{new_hostname}'")
                success = True
            else:
                print(f"❌ 设备名称修改失败，未找到 '{new_hostname}'")
                success = False
        else:
            print("❌ 无法验证设备名称修改结果")
            success = False
    except Exception as e:
        print(f"❌ 验证设备名称失败: {e}")
        success = False
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    return success


async def test_simple_command():
    """
    测试简单命令执行（不修改配置）
    """
    print("\n" + "=" * 70)
    print("简单命令执行测试 - 查看设备版本")
    print("=" * 70)
    
    device = create_test_device()
    netmiko_service = NetmikoService()
    
    try:
        version_command = netmiko_service.get_commands(device.vendor, "version")
        print(f"📤 执行命令: {version_command}")
        
        output = await netmiko_service.execute_command(device, version_command)
        if output:
            print(f"✅ 命令执行成功!")
            print(f"\n📤 命令输出 (前10行):")
            lines = output.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print("❌ 命令执行失败!")
            return False
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """
    主函数
    """
    print("\n🔍 开始测试华为交换机命令执行功能\n")
    
    # 先测试简单命令
    simple_result = await test_simple_command()
    
    # 如果简单命令成功，再测试修改主机名
    if simple_result:
        print("\n" + "=" * 70)
        print("简单命令测试通过，继续测试修改主机名功能")
        print("=" * 70)
        hostname_result = await test_change_hostname()
        
        if hostname_result:
            print("\n✅ 所有测试通过!")
            return 0
        else:
            print("\n❌ 修改主机名测试失败!")
            return 1
    else:
        print("\n❌ 简单命令测试失败，跳过修改主机名测试!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
