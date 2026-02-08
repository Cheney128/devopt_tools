"""
测试数据库连接脚本（详细版）
"""
import pymysql
import socket
from app.config import settings
from sqlalchemy.engine import make_url

print(f"Testing database connection with: {settings.DATABASE_URL}")
print(f"Current machine hostname: {socket.gethostname()}")
print(f"Current machine IP: {socket.gethostbyname(socket.gethostname())}")

# 解析数据库连接字符串
url = make_url(settings.DATABASE_URL)
if url:
    user = url.username
    password = url.password
    host = url.host
    port = url.port
    database = url.database
    
    print(f"\nParsed connection details:")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    
    try:
        # 尝试连接数据库（不带数据库名）
        print("\nTesting connection to MySQL server...")
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Successfully connected to MySQL server!")
        print(f"Connection ID: {conn.thread_id()}")
        
        # 测试查询
        with conn.cursor() as cursor:
            # 查看当前连接的用户和主机
            cursor.execute("SELECT USER(), CURRENT_USER()")
            result = cursor.fetchone()
            print(f"\nCurrent connection:")
            print(f"USER(): {result['USER()']}")
            print(f"CURRENT_USER(): {result['CURRENT_USER()']}")
            
            # 查看用户权限
            cursor.execute("SELECT user, host FROM mysql.user WHERE user = 'root'")
            users = cursor.fetchall()
            print("\nRoot user permissions:")
            for u in users:
                print(f"User: {u.get('user', u.get('USER'))}, Host: {u.get('host', u.get('HOST'))}")
        
        conn.close()
        print("\n✅ Connection closed successfully!")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Failed to parse database URL")
