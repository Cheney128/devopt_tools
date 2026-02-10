import sqlite3
from passlib.context import CryptContext
import hashlib
import base64
import secrets

# 数据库中的哈希
hash_from_db = "$pbkdf2-sha256$29000$FQLAGKN0LoVQKsWYk7L2Pg$KO0eMccQENQ/nzpnTIQmdsKCSBCvdlLuodpW..."

# Django pbkdf2_sha256 格式兼容验证
def _verify_django_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split('$')
        if len(parts) != 5:
            return False

        algorithm = parts[1]  # pbkdf2-sha256
        iterations = int(parts[2])
        salt = parts[3]
        checksum = parts[4]

        dk = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations,
            dklen=32
        )
        computed_hash = base64.b64encode(dk).decode('ascii')
        return secrets.compare_digest(computed_hash, checksum)
    except Exception:
        return False

print("=== 测试 Django 格式兼容验证 ===")
print(f"密码: 'admin123'")
print(f"哈希: {hash_from_db[:50]}...")
print()

result = _verify_django_pbkdf2("admin123", hash_from_db)
print(f"验证结果: {result}")

if result:
    print("\n✅ 密码验证成功！登录问题已修复。")
else:
    print("\n❌ 密码验证失败")
