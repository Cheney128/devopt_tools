from passlib.context import CryptContext
import sqlite3

# 加载当前的 security.py
import sys
sys.path.insert(0, '.')

# 测试 passlib 验证
ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 获取数据库中的哈希
conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
row = cursor.fetchone()
conn.close()

if row:
    username, db_hash = row
    print(f"用户名: {username}")
    print(f"数据库哈希: {db_hash}")
    print()

    # 测试验证
    result = ctx.verify("admin123", db_hash)
    print(f"验证 'admin123': {result}")

    if result:
        print("\n✅ 密码验证成功！登录问题已修复。")
    else:
        print("\n❌ 密码验证失败")
