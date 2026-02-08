"""
测试数据库连接脚本（调试正则表达式）
"""
import pymysql
import socket
import re
from app.config import settings

print(f"Testing database connection with: {settings.DATABASE_URL}")
print(f"Current machine hostname: {socket.gethostname()}")
print(f"Current machine IP: {socket.gethostbyname(socket.gethostname())}")

# 解析数据库连接字符串
url = settings.DATABASE_URL
print(f"\nOriginal URL: {url}")

# 测试不同的正则表达式
patterns = [
    r'mysql://(.*?):(.*?)@(.*?):(.*?)/(.*?)',
    r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)',
]

for i, pattern in enumerate(patterns):
    match = re.match(pattern, url)
    print(f"\nPattern {i+1}: {pattern}")
    if match:
        print(f"Groups: {match.groups()}")
        if len(match.groups()) >= 5:
            user = match.group(1)
            password = match.group(2).replace('%40', '@')
            host = match.group(3)
            port = int(match.group(4))
            database = match.group(5)
            
            print(f"Parsed:")
            print(f"User: {user}")
            print(f"Password: {'*' * len(password)}")
            print(f"Host: {host}")
            print(f"Port: {port}")
            print(f"Database: {database}")
    else:
        print("No match")

# 手动解析
print(f"\nManual parsing:")
parts = url.split('@')
if len(parts) == 2:
    auth_part = parts[0].replace('mysql://', '')
    host_part = parts[1]
    
    user_pass = auth_part.split(':')
    if len(user_pass) == 2:
        user = user_pass[0]
        password = user_pass[1].replace('%40', '@')
        print(f"User: {user}")
        print(f"Password: {'*' * len(password)}")
    
    host_db = host_part.split('/')
    if len(host_db) == 2:
        host_port = host_db[0]
        database = host_db[1]
        print(f"Database: {database}")
        
        hp_parts = host_port.split(':')
        if len(hp_parts) == 2:
            host = hp_parts[0]
            port = int(hp_parts[1])
            print(f"Host: {host}")
            print(f"Port: {port}")
