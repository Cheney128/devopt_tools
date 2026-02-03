"""
测试 MySQL 权限问题
"""
import pymysql
import socket

print(f"Current machine: {socket.gethostname()}")
print(f"VMware VMnet8 IP: 192.168.80.1")
print(f"Database server: 192.168.80.133:3307")
print(f"MySQL sees client as: 192.168.80.1")

# 测试不同的连接方式
tests = [
    # 测试 1: 直接连接 MySQL 服务器
    {
        "name": "Direct connection to MySQL",
        "host": "192.168.80.133",
        "port": 3307,
        "user": "root",
        "password": "1qaz@WSX",
        "database": "switch_manage"
    },
    # 测试 2: 尝试连接到 MySQL 服务器（不带数据库）
    {
        "name": "Connection to MySQL server (no database)",
        "host": "192.168.80.133",
        "port": 3307,
        "user": "root",
        "password": "1qaz@WSX",
        "database": None
    }
]

for test in tests:
    print(f"\n=== {test['name']} ===")
    print(f"Host: {test['host']}:{test['port']}")
    print(f"User: {test['user']}")
    print(f"Database: {test['database']}")
    
    try:
        conn_kwargs = {
            'host': test['host'],
            'port': test['port'],
            'user': test['user'],
            'password': test['password'],
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'connect_timeout': 5
        }
        
        if test['database']:
            conn_kwargs['database'] = test['database']
        
        conn = pymysql.connect(**conn_kwargs)
        print("✅ Connection successful!")
        
        if test['database']:
            # 测试查询
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()['VERSION()']
                print(f"MySQL Version: {version}")
        
        conn.close()
        print("✅ Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

print("\n=== 解决方案 ===")
print("问题原因：MySQL 服务器缺少 root@192.168.80.1 的访问权限")
print("\n在 MySQL 服务器上执行以下 SQL 命令：")
print("1. 授予 root 用户从 192.168.80