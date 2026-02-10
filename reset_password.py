import sqlite3
from passlib.context import CryptContext

# 创建新的密码哈希
ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 密码
password = "admin123"
new_hash = ctx.hash(password)

print(f"密码: {password}")
print(f"新哈希: {new_hash}")
print(f"新哈希长度: {len(new_hash)}")

# 更新数据库
conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()

# 更新 admin 用户的密码
cursor.execute(
    'UPDATE users SET password_hash = ? WHERE username = ?',
    (new_hash, 'admin')
)

# 验证更新
cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
row = cursor.fetchone()
print(f"\n数据库更新后的用户:")
print(f"  用户名: {row[0]}")
print(f"  新哈希: {row[1][:60]}...")
print(f"  哈希长度: {len(row[1])}")

conn.commit()
conn.close()

print("\n✅ 数据库已更新，请使用新密码登录")
