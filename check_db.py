import sqlite3

conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()

# 检查用户表结构
cursor.execute('PRAGMA table_info(users)')
columns = cursor.fetchall()
print('Users table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 查询用户
cursor.execute('SELECT * FROM users LIMIT 1')
row = cursor.fetchone()
print('\nUser data:')
if row:
    print(f'  ID: {row[0]}')
    print(f'  Username: {row[1]}')
    print(f'  Password hash column index: 2, value: {row[2][:80] if row[2] else None}...')
    print(f'  Hash starts with: {row[2][:10] if row[2] else None}')

conn.close()
