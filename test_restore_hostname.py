"""
恢复交换机名称为 huawei
"""
import paramiko
import time
import sys

def restore_hostname():
    """恢复交换机名称为 huawei"""
    print("=" * 60)
    print("恢复交换机名称为 huawei")
    print("=" * 60)

    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname='192.168.80.21',
            port=22,
            username='njadmin',
            password='Huawei@1234',
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        print("SSH连接成功")

        shell = ssh.invoke_shell()
        time.sleep(2)

        # 清空初始输出
        while shell.recv_ready():
            shell.recv(65535)

        # 查看当前主机名
        shell.send("display current-configuration | include sysname\n")
        time.sleep(2)
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print(f"当前主机名配置: {output.strip()}")

        # 恢复主机名
        shell.send("system-view\n")
        time.sleep(1)
        while shell.recv_ready():
            shell.recv(65535)

        shell.send("sysname huawei\n")
        time.sleep(1)
        while shell.recv_ready():
            shell.recv(65535)

        shell.send("commit\n")
        time.sleep(2)
        while shell.recv_ready():
            shell.recv(65535)

        shell.send("return\n")
        time.sleep(1)
        while shell.recv_ready():
            shell.recv(65535)

        # 验证
        shell.send("display current-configuration | include sysname\n")
        time.sleep(2)
        output = ""
        while shell.recv_ready():
            output += shell.recv(65535).decode('utf-8', errors='ignore')
        print(f"恢复后主机名配置: {output.strip()}")

        if "sysname huawei" in output:
            print("OK 主机名已恢复为 huawei")
            return True
        else:
            print("FAIL 主机名恢复失败")
            return False

    except Exception as e:
        print(f"FAIL 恢复失败: {e}")
        return False
    finally:
        if ssh:
            ssh.close()
            print("SSH连接已关闭")

if __name__ == "__main__":
    success = restore_hostname()
    sys.exit(0 if success else 1)
