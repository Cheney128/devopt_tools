#!/usr/bin/env python3
"""
SSH连接对比测试
对比Shell SSH、Paramiko、Netmiko的连接行为
分析为什么Shell可以连接但Netmiko失败
"""

import asyncio
import sys
import os
import socket
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('paramiko')
logger.setLevel(logging.DEBUG)

# 测试配置
DEVICE_IP = "192.168.80.21"
DEVICE_PORT = 22
USERNAME = "njadmin"
PASSWORD = "Huawei@1234"


async def test_socket_connection():
    """
    测试1: 基础Socket连接
    验证TCP层连接是否正常
    """
    print("=" * 70)
    print("测试1: 基础Socket连接")
    print("=" * 70)
    
    try:
        print(f"📤 尝试连接到 {DEVICE_IP}:{DEVICE_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((DEVICE_IP, DEVICE_PORT))
        
        # 尝试读取SSH banner
        print("📤 等待SSH banner...")
        sock.settimeout(5)
        banner = sock.recv(1024)
        
        if banner:
            print(f"✅ 收到SSH banner: {banner.decode('utf-8', errors='ignore').strip()}")
        else:
            print("❌ 未收到SSH banner")
        
        sock.close()
        print("✅ Socket连接测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Socket连接失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_paramiko_direct():
    """
    测试2: 直接使用Paramiko连接
    不通过Netmiko，直接使用Paramiko的Transport
    """
    print("\n" + "=" * 70)
    print("测试2: 直接使用Paramiko连接")
    print("=" * 70)
    
    try:
        import paramiko
        
        print(f"📤 创建Paramiko Transport...")
        transport = paramiko.Transport((DEVICE_IP, DEVICE_PORT))
        
        print(f"📤 设置连接参数...")
        transport.set_keepalive(30)
        
        print(f"📤 开始连接...")
        transport.start_client()
        
        print(f"📤 获取服务器密钥...")
        server_key = transport.get_remote_server_key()
        print(f"✅ 服务器密钥: {server_key.get_name()} {server_key.get_base64()[:50]}...")
        
        print(f"📤 尝试认证...")
        transport.auth_password(username=USERNAME, password=PASSWORD)
        
        if transport.is_authenticated():
            print("✅ 认证成功!")
            
            # 打开会话
            print("📤 打开会话...")
            channel = transport.open_session()
            channel.get_pty()
            channel.invoke_shell()
            
            # 读取初始输出
            print("📤 读取初始输出...")
            await asyncio.sleep(1)
            if channel.recv_ready():
                output = channel.recv(1024).decode('utf-8', errors='ignore')
                print(f"✅ 初始输出:\n{output}")
            
            # 发送命令
            print("📤 发送命令: display version")
            channel.send("display version\n")
            await asyncio.sleep(2)
            
            if channel.recv_ready():
                output = channel.recv(4096).decode('utf-8', errors='ignore')
                print(f"✅ 命令输出 (前500字符):\n{output[:500]}")
            
            channel.close()
        else:
            print("❌ 认证失败")
        
        transport.close()
        print("✅ Paramiko直接连接测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Paramiko连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_paramiko_sshclient():
    """
    测试3: 使用Paramiko的SSHClient连接
    更接近Netmiko的实现方式
    """
    print("\n" + "=" * 70)
    print("测试3: 使用Paramiko的SSHClient连接")
    print("=" * 70)
    
    try:
        import paramiko
        
        print(f"📤 创建SSHClient...")
        client = paramiko.SSHClient()
        
        print(f"📤 设置缺失主机密钥策略...")
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"📤 尝试连接...")
        client.connect(
            hostname=DEVICE_IP,
            port=DEVICE_PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=30,
            auth_timeout=30
        )
        
        print("✅ SSHClient连接成功!")
        
        # 执行命令
        print("📤 执行命令: display version")
        stdin, stdout, stderr = client.exec_command("display version", timeout=30)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(f"✅ 命令输出 (前500字符):\n{output[:500]}")
        if error:
            print(f"⚠️  错误输出: {error}")
        
        client.close()
        print("✅ Paramiko SSHClient测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Paramiko SSHClient连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_netmiko_basic():
    """
    测试4: 使用Netmiko基础连接
    """
    print("\n" + "=" * 70)
    print("测试4: 使用Netmiko基础连接")
    print("=" * 70)
    
    try:
        from netmiko import ConnectHandler
        
        device_params = {
            'device_type': 'huawei',
            'host': DEVICE_IP,
            'username': USERNAME,
            'password': PASSWORD,
            'port': DEVICE_PORT,
            'timeout': 60,
            'conn_timeout': 30,
        }
        
        print(f"📤 使用参数连接: {device_params}")
        
        loop = asyncio.get_event_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: ConnectHandler(**device_params)
        )
        
        print("✅ Netmiko连接成功!")
        
        # 执行命令
        print("📤 执行命令: display version")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display version", read_timeout=30)
        )
        
        if output:
            print(f"✅ 命令输出 (前500字符):\n{output[:500]}")
        
        await loop.run_in_executor(None, connection.disconnect)
        print("✅ Netmiko基础连接测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Netmiko连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


async def test_netmiko_with_session_log():
    """
    测试5: 使用Netmiko并启用会话日志
    捕获详细的会话信息
    """
    print("\n" + "=" * 70)
    print("测试5: 使用Netmiko并启用会话日志")
    print("=" * 70)
    
    session_log_file = "netmiko_session.log"
    
    try:
        from netmiko import ConnectHandler
        
        device_params = {
            'device_type': 'huawei',
            'host': DEVICE_IP,
            'username': USERNAME,
            'password': PASSWORD,
            'port': DEVICE_PORT,
            'timeout': 60,
            'conn_timeout': 30,
            'session_log': session_log_file,
            'session_log_file_mode': 'write',
        }
        
        print(f"📤 使用参数连接（启用会话日志）...")
        print(f"📤 会话日志文件: {session_log_file}")
        
        loop = asyncio.get_event_loop()
        connection = await loop.run_in_executor(
            None,
            lambda: ConnectHandler(**device_params)
        )
        
        print("✅ Netmiko连接成功!")
        
        # 执行命令
        print("📤 执行命令: display version")
        output = await loop.run_in_executor(
            None,
            lambda: connection.send_command("display version", read_timeout=30)
        )
        
        if output:
            print(f"✅ 命令输出 (前500字符):\n{output[:500]}")
        
        await loop.run_in_executor(None, connection.disconnect)
        
        # 读取会话日志
        if os.path.exists(session_log_file):
            print(f"\n📤 会话日志内容:")
            with open(session_log_file, 'r') as f:
                log_content = f.read()
                print(log_content[:2000])  # 只显示前2000字符
        
        print("✅ Netmiko会话日志测试通过")
        return True
        
    except Exception as e:
        print(f"❌ Netmiko连接失败: {e}")
        print(f"❌ 错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # 即使失败也尝试读取会话日志
        if os.path.exists(session_log_file):
            print(f"\n📤 会话日志内容（失败时）:")
            with open(session_log_file, 'r') as f:
                log_content = f.read()
                print(log_content[:2000])
        
        return False


async def test_netmiko_alternative_device_types():
    """
    测试6: 尝试不同的设备类型
    华为设备可能有多种device_type映射
    """
    print("\n" + "=" * 70)
    print("测试6: 尝试不同的设备类型")
    print("=" * 70)
    
    from netmiko import ConnectHandler
    from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE
    
    # 可能的华为设备类型
    possible_types = [
        'huawei',
        'huawei_ssh',
        'huawei_telnet',
        'huawei_vrp',
        'hp_comware',  # H3C/华三使用这个
    ]
    
    # 显示所有可用的设备类型
    print("📤 所有可用的设备类型（包含huawei）:")
    available_types = [k for k in CLASS_MAPPER_BASE.keys() if 'huawei' in k.lower() or 'hp' in k.lower()]
    for t in available_types:
        print(f"   - {t}")
    
    for device_type in possible_types:
        if device_type not in CLASS_MAPPER_BASE:
            print(f"\n⚠️  设备类型 '{device_type}' 不可用，跳过")
            continue
            
        print(f"\n📤 尝试设备类型: {device_type}")
        
        try:
            device_params = {
                'device_type': device_type,
                'host': DEVICE_IP,
                'username': USERNAME,
                'password': PASSWORD,
                'port': DEVICE_PORT,
                'timeout': 30,
                'conn_timeout': 15,
            }
            
            loop = asyncio.get_event_loop()
            connection = await loop.run_in_executor(
                None,
                lambda: ConnectHandler(**device_params)
            )
            
            print(f"✅ 设备类型 '{device_type}' 连接成功!")
            
            # 执行简单命令
            output = await loop.run_in_executor(
                None,
                lambda: connection.send_command("display version", read_timeout=20)
            )
            
            if output:
                print(f"✅ 命令执行成功，输出长度: {len(output)}")
            
            await loop.run_in_executor(None, connection.disconnect)
            return True, device_type
            
        except Exception as e:
            print(f"❌ 设备类型 '{device_type}' 连接失败: {e}")
    
    return False, None


async def analyze_ssh_banner():
    """
    测试7: 分析SSH Banner
    对比Shell SSH和Python获取的Banner
    """
    print("\n" + "=" * 70)
    print("测试7: 分析SSH Banner")
    print("=" * 70)
    
    try:
        print("📤 使用Socket获取SSH Banner...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((DEVICE_IP, DEVICE_PORT))
        
        # 等待并读取banner
        sock.settimeout(5)
        banner = sock.recv(1024)
        
        if banner:
            banner_str = banner.decode('utf-8', errors='ignore').strip()
            print(f"✅ 收到的Banner: {banner_str}")
            
            # 分析banner
            if 'SSH' in banner_str:
                print("✅ 这是有效的SSH Banner")
                
                # 提取SSH版本
                if 'SSH-2.0' in banner_str:
                    print("✅ 设备支持SSH 2.0")
                elif 'SSH-1.99' in banner_str:
                    print("✅ 设备支持SSH 1.99（兼容1.5和2.0）")
                elif 'SSH-1.5' in banner_str:
                    print("⚠️  设备只支持SSH 1.5")
            else:
                print("⚠️  这不是标准的SSH Banner")
        else:
            print("❌ 未收到Banner")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ 获取Banner失败: {e}")
        return False


async def main():
    """
    主函数
    """
    print("\n🔍 SSH连接对比测试")
    print("=" * 70)
    print(f"设备: {DEVICE_IP}:{DEVICE_PORT}")
    print(f"用户名: {USERNAME}")
    print("=" * 70)
    
    results = {}
    
    # 执行所有测试
    results['socket'] = await test_socket_connection()
    results['paramiko_direct'] = await test_paramiko_direct()
    results['paramiko_sshclient'] = await test_paramiko_sshclient()
    results['netmiko_basic'] = await test_netmiko_basic()
    results['netmiko_session_log'] = await test_netmiko_with_session_log()
    results['netmiko_alt_types'] = await test_netmiko_alternative_device_types()
    results['banner_analysis'] = await analyze_ssh_banner()
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:25s}: {status}")
    
    # 分析结论
    print("\n" + "=" * 70)
    print("分析结论")
    print("=" * 70)
    
    if results.get('socket') and results.get('paramiko_direct'):
        print("✅ Socket和Paramiko直接连接都成功")
        print("✅ 问题可能出在Netmiko的封装层")
    
    if not results.get('netmiko_basic') and results.get('paramiko_sshclient'):
        print("⚠️  Paramiko SSHClient成功但Netmiko失败")
        print("⚠️  可能是Netmiko的设备类型配置问题")
    
    print("\n" + "=" * 70)
    print("建议的解决方案")
    print("=" * 70)
    print("1. 尝试使用不同的device_type（如huawei_ssh）")
    print("2. 检查Netmiko的版本兼容性")
    print("3. 使用Paramiko直接连接替代Netmiko")
    print("4. 调整SSH连接参数（banner_timeout等）")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
