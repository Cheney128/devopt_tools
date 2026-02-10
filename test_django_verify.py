import sqlite3
import hashlib
import base64
import secrets

# 获取数据库中的哈希
conn = sqlite3.connect('switch_manage.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users WHERE username = ?', ('admin',))
row = cursor.fetchone()
conn.close()

if row:
    db_hash = row[1]
    print(f"数据库哈希: {db_hash}")

    # Django 格式验证
    def verify_django_pbkdf2(plain_password, hashed_password):
        try:
            parts = hashed_password.split('$')
            if len(parts) != 5:
                return False
            iterations = int(parts[2])
            salt = parts[3]
            expected_hash = parts[4]

            dk = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations,
                dklen=32
            )
            computed_hash = base64.b64encode(dk).decode('ascii')
            return secrets.compare_digest(computed_hash, expected_hash)
        except Exception:
            return False

    # 测试验证
    result = verify_django_pbkdf2("admin123", db_hash)
    print(f"\n验证 'admin123': {result}")

    if result:
        print("\n✅ 密码验证成功！")
    else:
        print("\n❌ 密码验证失败")
