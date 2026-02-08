#!/usr/bin/env python3
"""
华为交换机连接测试 - 简单版本
用于测试与华为交换机的SSH连接
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException


async def test_connection():
    """
    测试华为交换机连接
    """
    print("=" * 70)
    print("华为交换机连接测试")
    print("=" * 70)
    
    # 用户提供的测试环境信息
    device_info = {
        'device_type': 'huawei',
        'host': '192.168.80.21',
        'username': 'njadmin',  # 用户提供的用户名
        'password': 'Huawei@1234',
        'port': 22,
        'timeout': 60,
        'conn_timeout': 30,
    }
    
    print(f"\n📋 设备信息:")
    print(f"   IP地址: {device_info['host']}")
    print(f"   端口: {device_info['port']}")
    print(f"   用户名: {device_info['username']}")
    print(f"   设备类型: {device_info['device_type']}")
    
    print("\n" + "=" * 70)
    print("步骤1: 测试SSH连接")
    print("=" * 70)
    
    try:
        print(f"📤 正在连接设备 {device_info['host']}...")
        
        loop = asyncio.get_event_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: ConnectHandler(**device_info)
        )
        
        print("✅ SSH连接成功!")
        
    except NetmikoAuthenticationException as e:
        print(f"❌ 认证失败: {e}")
        print("\n🔍 可能的原因:")
        print("   1. 用户名错误（当前使用: njadmin）")
        print("   2. 密码错误")
        print("   3. 设备需要特殊的认证方式")
        return False
    except NetmikoTimeoutException as e:
        print(f"❌ 连接超时: {e}")
        print("\n🔍 可能的原因:")
        print("   1. 设备IP地址错误")
        print("   2. 网络不可达")
        print("   3. SSH端口错误")
        return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("步骤2: 测试执行简单命令")
    print("=" * 70)
    
    try:
        print(f"📤 执行命令: display version")
        
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display version", read_timeout=30)
        )
        
        if output:
            print("✅ 命令执行成功!")
            print(f"\n📤 命令输出 (前10行):")
            lines = output.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
        else:
            print("❌ 命令执行失败!")
            connection.disconnect()
            return False
            
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        connection.disconnect()
        return False
    
    print("\n" + "=" * 70)
    print("步骤3: 查看当前设备名称")
    print("=" * 70)
    
    try:
        print(f"📤 执行命令: display current-configuration | include sysname")
        
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname", read_timeout=30)
        )
        
        if output:
            print("✅ 命令执行成功!")
            print(f"\n📤 当前设备名称配置:")
            print(output)
        else:
            print("⚠️  无法获取当前设备名称")
            
    except Exception as e:
        print(f"❌ 获取设备名称失败: {e}")
    
    print("\n" + "=" * 70)
    print("步骤4: 修改设备名称为 'huawei-test-01'")
    print("=" * 70)
    
    new_hostname = "huawei-test-01"
    
    try:
        print(f"📤 执行命令序列:")
        commands = [
            "system-view",
            f"sysname {new_hostname}",
            "return"
        ]
        
        for cmd in commands:
            print(f"   {cmd}")
            output = await loop.run_in_executor(
                None,
                lambda c=cmd: connection.send_command(c, read_timeout=30)
            )
            if output:
                print(f"✅ 命令 '{cmd}' 执行成功")
            else:
                print(f"❌ 命令 '{cmd}' 执行失败")
                connection.disconnect()
                return False
        
        print(f"\n✅ 设备名称修改为 '{new_hostname}' 成功!")
        
    except Exception as e:
        print(f"❌ 修改设备名称失败: {e}")
        import traceback
        traceback.print_exc()
        connection.disconnect()
        return False
    
    print("\n" + "=" * 70)
    print("步骤5: 验证设备名称修改结果")
    print("=" * 70)
    
    try:
        print(f"📤 执行命令: display current-configuration | include sysname")
        
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname", read_timeout=30)
        )
        
        if output:
            print("✅ 命令执行成功!")
            print(f"\n📤 验证结果:")
            print(output)
            
            if new_hostname in output:
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
    
    try:
        connection.disconnect()
        print("\n✅ 已断开设备连接")
    except:
        pass
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    return success


async def main():
    """
    主函数
    """
    print("\n🔍 开始测试华为交换机连接和命令执行功能\n")
    
    result = await test_connection()
    
    if result:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print("\n❌ 测试失败!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
