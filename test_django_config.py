import sys
sys.path.insert(0, '.')
from passlib.context import CryptContext
import sqlite3

ctx = CryptContext(
    schemes=['pbkdf2_sha256', 'django_pbkdf2_sha256'],
    deprecated='auto',
    default='pbkdf2_sha256'
)

conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
row = cursor.fetchone()
conn.close()

if row:
    username, db_hash = row
    print(f'用户名: {username}')
    print(f'数据库哈希: {db_hash}')
    print()
    
    try:
        identified = ctx.identify(db_hash)
        print(f'识别结果: {identified}')
        
        result = ctx.verify('admin123', db_hash)
        print(f'验证 admin123: {result}')
        
        if result:
            print('\n✅ 密码验证成功！')
        else:
            print('\n❌ 密码验证失败')
    except Exception as e:
        print(f'错误: {e}')
