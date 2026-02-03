"""
直接SSH连接交换机测试
测试目标：192.168.80.21
"""
import paramiko
import time
import sys

def test_ssh_direct():
    """使用Paramiko直接连接交换机并执行命令"""
    print("=" * 60)
    print("测试1: 直接SSH连接交换机")
    print("=" * 60)
    print("目标设备: 192.168.80.21")
    print("用户名: njadmin")
    print("端口: 22")
    print("-" * 60)

    ssh = None
    try:
        # 创建SSH客户端
        print("[1/5] 创建SSH客户端...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 连接设备
        print("[2/5] 连接设备 (超时: 30秒)...")
        ssh.connect(
            hostname='192.168.80.21',
            port=22,
            username='njadmin',
            password='Huawei@1234',
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        print("OK SSH连接成功!")

        # 创建交互式shell
        print("[3/5] 创建交互式shell...")
        shell = ssh.invoke_shell()
        time.sleep(2)

        # 读取初始输出
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print("初始提示符获取完成")

        # 执行查看当前主机名命令
        print("[4/5] 查看当前主机名...")
        shell.send("display current-configuration | include sysname\n")
        time.sleep(2)

        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print("当前主机名配置:")
        print(output)

        # 进入系统视图修改主机名
        print("[5/5] 修改主机名为 test1234...")
        shell.send("system-view\n")
        time.sleep(1)

        # 读取system-view输出
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')

        # 修改主机名
        shell.send("sysname test1234\n")
        time.sleep(1)

        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')

        # 提交配置
        shell.send("commit\n")
        time.sleep(2)

        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print("提交配置输出:")
        print(output[-200:] if len(output) > 200 else output)

        # 退出到用户视图
        shell.send("return\n")
        time.sleep(1)

        # 验证新主机名
        shell.send("display current-configuration | include sysname\n")
        time.sleep(2)

        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print("验证新主机名:")
        print(output)

        if "test1234" in output:
            print("OK 主机名修改成功!")
            result = True
        else:
            print("FAIL 主机名修改失败!")
            result = False

        print("=" * 60)
        print("测试1结果: SSH直接连接 - " + ("成功" if result else "失败"))
        print("=" * 60)
        return result

    except Exception as e:
        print("FAIL SSH连接失败: " + str(e))
        import traceback
        traceback.print_exc()
        print("=" * 60)
        print("测试1结果: SSH直接连接 - 失败")
        print("=" * 60)
        return False

    finally:
        if ssh:
            ssh.close()
            print("[清理] SSH连接已关闭")

if __name__ == "__main__":
    success = test_ssh_direct()
    sys.exit(0 if success else 1)
