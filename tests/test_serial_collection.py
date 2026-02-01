#!/usr/bin/env python3
"""
测试设备序列号采集功能
"""
import sys
import os
import asyncio
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.netmiko_service import NetmikoService
from app.models.models import Device


def test_serial_collection_logic():
    """
    测试序列号采集逻辑
    """
    # 创建模拟设备
    device = Mock(spec=Device)
    device.id = 1
    device.hostname = "test-switch"
    device.ip_address = "10.23.2.20"
    device.vendor = "cisco"
    device.model = "Catalyst WS-C3850-48T"
    device.username = "admin"
    device.password = "toW3cBee"
    device.login_port = 22
    device.login_method = "ssh"
    
    # 创建Netmiko服务实例
    netmiko_service = NetmikoService()
    
    # 模拟连接和命令执行
    with patch.object(netmiko_service, 'connect_to_device') as mock_connect, \
         patch('asyncio.get_event_loop') as mock_loop:
        
        # 模拟连接对象
        mock_connection = Mock()
        mock_connect.return_value = mock_connection
        
        # 模拟版本命令输出
        version_output = """
Cisco IOS Software, C3750 Software (C3750-IPSERVICESK9-M), Version 15.0(2)SE11, RELEASE SOFTWARE (fc3)
System image file is "flash:c3750-ipservicesk9-mz.150-2.SE11.bin"
cisco WS-C3750-24TS (PowerPC405) processor (revision H0) with 131072K bytes of memory.
Processor board ID FOC12345678
        """
        
        # 模拟inventory命令输出
        inventory_output = """
NAME: "1", DESCR: "WS-C3750-24TS"
PID: WS-C3750-24TS-S  , VID: V05  , SN: FOC12345678
        """
        
        # 模拟命令执行返回值
        mock_connection.send_command.side_effect = [version_output, inventory_output]
        
        # 模拟事件循环
        mock_executor = Mock()
        mock_executor.run_in_executor = Mock()
        mock_executor.run_in_executor.side_effect = lambda _, func: func()
        mock_loop.return_value = mock_executor
        
        # 运行序列号采集
        async def run_test():
            serial = await netmiko_service.collect_device_serial(device)
            print(f"Collected serial: {serial}")
            assert serial == "FOC12345678", f"Expected serial 'FOC12345678', got '{serial}'"
            
            # 验证连接只建立了一次
            mock_connect.assert_called_once()
            # 验证命令执行了两次
            assert mock_connection.send_command.call_count == 2
            print("✅ Test passed: Serial collection works correctly with single connection")
        
        # 运行测试
        asyncio.run(run_test())


if __name__ == "__main__":
    print("Testing device serial collection...")
    try:
        test_serial_collection_logic()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)