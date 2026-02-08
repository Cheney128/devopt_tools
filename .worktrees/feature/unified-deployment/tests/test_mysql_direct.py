"""
直接测试 MySQL 连接
"""
import pymysql
import socket

print(f"Current machine: {socket.gethostname()} ({socket.gethostbyname(socket.gethostname())})")

# 直接硬编码连接参数
host = '192.168.80.133'
port = 3307
user = 'root'
password = '1qaz@WSX'
database = 'switch_manage'

print(f"\nAttempting to connect to MySQL at {host}:{port}...")

try:
    # 尝试连接
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )
    
    print("✅ Connection successful!")
    print(f"Connection ID: {conn.thread_id()}")
    
    # 测试查询
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()['VERSION()']
        print(f"MySQL Version: {version}")
        
        cursor.execute("SHOW DATABASES LIKE 'switch_manage'")
        if cursor.fetchone():
            print("✅ Database 'switch_manage' exists")
        else:
            print("❌ Database 'switch_manage' does not exist")
    
    conn.close()
    print("\n✅ Connection closed successfully")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
