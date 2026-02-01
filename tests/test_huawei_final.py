#!/usr/bin/env python3
"""
华为交换机最终测试
验证前端到后端的完整命令下发流程
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netmiko import ConnectHandler


# 测试配置
DEVICE_IP = "192.168.80.21"
DEVICE_PORT = 22
USERNAME = "njadmin"
PASSWORD = "Huawei@1234"


async def test_full_workflow():
    """
    测试完整的命令下发流程
    """
    print("=" * 70)
    print("华为交换机最终测试 - 完整命令下发流程")
    print("=" * 70)
    
    print(f"\n📋 设备信息:")
    print(f"   IP地址: {DEVICE_IP}")
    print(f"   端口: {DEVICE_PORT}")
    print(f"   用户名: {USERNAME}")
    print(f"   设备类型: huawei")
    
    print("\n" + "=" * 70)
    print("步骤1: 建立SSH连接")
    print("=" * 70)
    
    try:
        device_params = {
            'device_type': 'huawei',
            'host': DEVICE_IP,
            'username': USERNAME,
            'password': PASSWORD,
            'port': DEVICE_PORT,
            'timeout': 60,
            'conn_timeout': 30,
        }
        
        print(f"📤 正在连接设备...")
        loop = asyncio.get_event_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: ConnectHandler(**device_params)
        )
        print("✅ SSH连接成功!")
        
    except Exception as e:
        print(f"❌ SSH连接失败: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("步骤2: 查看当前设备名称")
    print("=" * 70)
    
    try:
        print(f"📤 执行命令: display current-configuration | include sysname")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname", read_timeout=30)
        )
        
        if output:
            print(f"✅ 命令执行成功!")
            print(f"📤 当前设备名称:\n{output}")
            current_hostname = output.strip().replace("sysname ", "")
        else:
            print("⚠️  未获取到设备名称")
            current_hostname = "HUAWEI"
            
    except Exception as e:
        print(f"❌ 获取设备名称失败: {e}")
        current_hostname = "HUAWEI"
    
    print("\n" + "=" * 70)
    print("步骤3: 修改设备名称")
    print("=" * 70)
    
    new_hostname = "huawei-test-01"
    
    try:
        print(f"📤 进入系统视图...")
        await loop.run_in_executor(
            None,
            lambda: connection.send_command("system-view", expect_string=r"\[.*\]", read_timeout=30)
        )
        print("✅ 已进入系统视图")
        
        print(f"📤 修改设备名称为: {new_hostname}")
        await loop.run_in_executor(
            None,
            lambda: connection.send_command(f"sysname {new_hostname}", expect_string=r"\[.*\]", read_timeout=30)
        )
        print(f"✅ 设备名称已修改")
        
        print(f"📤 返回用户视图...")
        await loop.run_in_executor(
            None,
            lambda: connection.send_command("return", expect_string=r"<.*>", read_timeout=30)
        )
        print("✅ 已返回用户视图")
        
    except Exception as e:
        print(f"❌ 修改设备名称失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("步骤4: 验证设备名称修改")
    print("=" * 70)
    
    try:
        print(f"📤 执行命令: display current-configuration | include sysname")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display current-configuration | include sysname", read_timeout=30)
        )
        
        if output:
            print(f"✅ 命令执行成功!")
            print(f"📤 验证结果:\n{output}")
            
            if new_hostname in output:
                print(f"✅ 设备名称已成功修改为 '{new_hostname}'")
                success = True
            else:
                print(f"❌ 设备名称修改失败")
                success = False
        else:
            print("❌ 无法验证设备名称")
            success = False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        success = False
    
    print("\n" + "=" * 70)
    print("步骤5: 恢复原始设备名称")
    print("=" * 70)
    
    try:
        print(f"📤 恢复设备名称为: {current_hostname}")
        
        await loop.run_in_executor(
            None,
            lambda: connection.send_command("system-view", expect_string=r"\[.*\]", read_timeout=30)
        )
        
        await loop.run_in_executor(
            None,
            lambda: connection.send_command(f"sysname {current_hostname}", expect_string=r"\[.*\]", read_timeout=30)
        )
        
        await loop.run_in_executor(
            None,
            lambda: connection.send_command("return", expect_string=r"<.*>", read_timeout=30)
        )
        
        print(f"✅ 设备名称已恢复")
        
    except Exception as e:
        print(f"⚠️  恢复设备名称失败: {e}")
    
    print("\n" + "=" * 70)
    print("步骤6: 断开连接")
    print("=" * 70)
    
    try:
        await loop.run_in_executor(None, connection.disconnect)
        print("✅ 已断开设备连接")
    except Exception as e:
        print(f"⚠️  断开连接时出错: {e}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
    
    return success


async def main():
    """
    主函数
    """
    print("\n🔍 开始华为交换机最终测试\n")
    
    result = await test_full_workflow()
    
    if result:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print("\n❌ 测试失败!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
