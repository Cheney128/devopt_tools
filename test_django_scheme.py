import sqlite3
from passlib.context import CryptContext

# 测试 Django pbkdf2_sha256 格式
ctx = CryptContext(schemes=["django_pbkdf2_sha256"], deprecated="auto")

# 获取数据库中的哈希
conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
row = cursor.fetchone()
conn.close()

if row:
    db_hash = row[1]
    print(f"数据库哈希: {db_hash}")
    print(f"哈希格式: {ctx.identify(db_hash)}")
    print()

    # 测试验证
    result = ctx.verify("admin123", db_hash)
    print(f"验证 'admin123': {result}")
