"""
测试数据库连接脚本
"""
import pymysql
from app.config import settings

print(f"Testing database connection with: {settings.DATABASE_URL}")

# 解析数据库连接字符串
import re

url = settings.DATABASE_URL
match = re.match(r'mysql://(.*?):(.*?)@(.*?):(.*?)/(.*?)', url)
if match:
    user = match.group(1)
    password = match.group(2).replace('%40', '@')
    host = match.group(3)
    port = int(match.group(4))
    database = match.group(5)
    
    print(f"User: {user}")
    print(f"Password: {password}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    
    try:
        # 尝试连接数据库
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("\n✅ Database connection successful!")
        print(f"Connection ID: {conn.thread_id()}")
        
        # 测试查询
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
            print(f"MySQL Version: {result['VERSION()']}")
        
        conn.close()
        print("✅ Connection closed successfully!")
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
else:
    print("❌ Failed to parse database URL")
