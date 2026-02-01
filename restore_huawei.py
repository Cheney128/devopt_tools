"""恢复交换机名称为huawei"""
import paramiko
import time

def restore():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.80.21', port=22, username='njadmin', password='Huawei@1234', timeout=30)

    shell = ssh.invoke_shell()
    time.sleep(2)

    # 清空缓冲区
    while shell.recv_ready():
        shell.recv(65535)

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

    ssh.close()
    print(output)

    if "sysname huawei" in output:
        print("OK 主机名已恢复为 huawei")
        return True
