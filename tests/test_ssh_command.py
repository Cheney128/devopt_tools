#!/usr/bin/env python3
"""
SSH命令执行测试脚本
用于测试SSH登录设备并执行命令
"""

import getpass
import logging
logging.basicConfig(level=logging.DEBUG)
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

# 设备信息
device_info = {
    'device_type': 'huawei',  # 华为设备
    'host': '10.23.2.95',      # 设备IP地址
    'username': 'njadmin',       # 用户名
    'port': 22,               # SSH端口
    'conn_timeout': 30,       # 连接超时时间（秒）
}

# 获取用户输入的密码
device_info['password'] = getpass.getpass(prompt='请输入设备密码: ')

print(f"\n正在连接设备 {device_info['host']}...")

try:
    # 建立SSH连接
    with ConnectHandler(**device_info) as conn:
        print(f"成功登录设备 {device_info['host']}")
        
        # 执行命令
        command = 'system-view'
        print(f"\n执行命令: {command}")
        
        # 发送命令
        output = conn.send_command(command)
        
        # 打印输出结果
        print("\n命令执行结果:")
        print(output)
        
        print(f"\n成功在设备 {device_info['host']} 上执行命令")
        
except NetmikoTimeoutException:
    print(f"连接超时: 无法连接到设备 {device_info['host']}")
except NetmikoAuthenticationException:
    print(f"认证失败: 用户名或密码错误")
except Exception as e:
    print(f"连接失败: {str(e)}")
