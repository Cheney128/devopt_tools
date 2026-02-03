"""
最终测试 MySQL 连接
"""
import pymysql
import socket
import subprocess

print("=== 网络配置信息 ===")
print(f"主机名: {socket.gethostname()}")

# 获取网络接口信息
print("\n网络接口:")
for interface, ip in [
    ("VMware VMnet8", "192.168.80.1"),
    ("本地网络", "192.168.124.123")
]:
    print(f"{interface}: {ip}")

print("\n=== 连接测试 ===")
print(f"数据库服务器: 192.168.80.133:3307")
print(f"客户端 IP (MySQL 看到的): 192.168.80.1")

# 测试连接
try:
    conn = pymysql.connect(
        host='192.168.80.133',
        port=3307,
        user='root',
        password='1qaz@WSX',
        database='switch_manage',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )
    print("✅ 连接成功！")
    print(f"连接 ID: {conn.thread_id()}")
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()['VERSION()']
        print(f"MySQL 版本: {version}")
    
    conn.close()
    print("✅ 连接关闭成功")
    
except Exception as e:
    print(f"❌ 连接失败: {e}")

print("\n=== 问题