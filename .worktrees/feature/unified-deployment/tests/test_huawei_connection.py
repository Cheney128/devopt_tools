#!/usr/bin/env python3
"""
华为交换机Netmiko连接测试脚本
用于测试与华为交换机的SSH连接，排查连接问题
"""

import sys
import getpass
from typing import Optional
from app.models.models import Device
from app.services.netmiko_service import NetmikoService


def create_test_device() -> Device:
    """
    创建测试设备对象，模拟数据库中的设备
    """
    # 使用用户提供的设备信息
    device = Device()
    device.id = 1
    device.hostname = "模块33-R01-24口业务接入"
    device.ip_address = "10.23.2.54"
    device.vendor = "华为"
    device.model = "S5735S-L24T4S-QA2"
    device.login_method = "ssh"
    device.login_port = 22
    device.username = "njadmin"
    device.password = None  # 后续由用户输入
    device.status = "offline"
    
    return device


async def test_device_connection(device: Device) -> None:
    """
    测试设备连接
    """
    print("=" * 60)
    print(f"测试设备连接: {device.hostname} ({device.ip_address})")
    print("=" * 60)
    
    # 创建Netmiko服务实例
    netmiko_service = NetmikoService()
    
    # 获取设备类型
    device_type = netmiko_service.get_device_type(device.vendor)
    print(f"设备厂商: {device.vendor}")
    print(f"Netmiko设备类型: {device_type}")
    print(f"登录方式: {device.login_method}")
    print(f"端口: {device.login_port}")
    print(f"用户名: {device.username}")
    print(f"密码长度: {len(device.password) if device.password else 0} 个字符")
    print()
    
    # 直接测试Netmiko连接，不通过封装方法
    print("📋 直接测试Netmiko连接...")
    from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
    
    device_params = {
        "device_type": device_type,
        "host": device.ip_address,
        "username": device.username,
        "password": device.password,
        "port": device.login_port,
        "timeout": 60,
        "conn_timeout": 30,
    }
    
    try:
        connection = ConnectHandler(**device_params)
        print("✅ 直接连接成功!")
        
        # 测试执行命令
        print("\n📋 测试执行命令...")
        version_command = netmiko_service.get_commands(device.vendor, "version")
        print(f"执行命令: {version_command}")
        
        output = connection.send_command(version_command, read_timeout=30)
        print("\n📤 命令输出 (前5行):")
        lines = output.split('\n')[:5]
        for line in lines:
            print(f"   {line}")
        print("\n✅ 命令执行成功!")
        
        connection.disconnect()
    except NetmikoAuthenticationException as e:
        print(f"❌ 认证失败: {e}")
        print("\n🔍 认证失败可能原因:")
        print("   1. 密码错误")
        print("   2. 用户名错误")
        print("   3. 设备不允许该用户通过SSH登录")
        print("   4. 设备需要特殊的认证方式")
    except NetmikoTimeoutException as e:
        print(f"❌ 连接超时: {e}")
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 然后测试封装的方法
    print("\n" + "-" * 60)
    print("📋 测试封装的连接方法...")
    print("-" * 60)
    
    try:
        # 测试连接
        connection = await netmiko_service.connect_to_device(device)
        
        if connection:
            print("✅ 封装方法连接成功!")
            connection.disconnect()
        else:
            print("❌ 封装方法连接失败!")
    except Exception as conn_error:
        print(f"❌ 封装方法连接异常: {conn_error}")
    finally:
        print("=" * 60)
        print("测试完成")
        print("=" * 60)


async def main() -> None:
    """
    主函数
    """
    # 创建测试设备
    device = create_test_device()
    
    # 获取用户输入的密码
    password = getpass.getpass(f"请输入设备 {device.hostname} 的密码: ")
    device.password = password
    
    # 测试连接
    await test_device_connection(device)


if __name__ == "__main__":
    # 运行主函数
    import asyncio
    asyncio.run(main())
