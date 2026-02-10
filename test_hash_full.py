import hashlib
import base64
import secrets

# 完整的 Django 格式哈希
full_hash = "$pbkdf2-sha256$29000$FQLAGKN0LoVQKsWYk7L2Pg$KO0eMccQENQ/nzpnTIQmdsKCSBCvdlLuodpWBBy/ukA"

def verify_django_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    """
    验证 Django 格式的 pbkdf2_sha256 哈希
    Django 格式: $pbkdf2-sha256$iterations$salt$hash
    """
    try:
        parts = hashed_password.split('$')
        if len(parts) != 5:
            print(f"  错误: 哈希部分数量不正确 (期望5个部分，得到{len(parts)}个)")
            return False

        algorithm = parts[1]
        iterations = int(parts[2])
        salt = parts[3]
        expected_hash = parts[4]

        print(f"  算法: {algorithm}")
        print(f"  迭代次数: {iterations}")
        print(f"  Salt: {salt}")
        print(f"  预期哈希: {expected_hash}")
        print()

        # 计算哈希
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations,
            dklen=32
        )
        computed_hash = base64.b64encode(dk).decode('ascii')

        print(f"  计算哈希: {computed_hash}")
        print()

        # 使用 constant-time 比较
        result = secrets.compare_digest(computed_hash, expected_hash)
        return result
    except Exception as e:
        print(f"  错误: {e}")
        return False

# 测试
print("=== 验证 Django pbkdf2-sha256 哈希 ===")
print()
print(f"测试密码: 'admin123'")
print(f"哈希: {full_hash}")
print()

result = verify_django_pbkdf2("admin123", full_hash)
print(f"验证结果: {result}")

if result:
    print("\n✅ 密码验证成功！")
else:
    print("\n❌ 密码验证失败")
    print()
    print("尝试其他密码...")

# 尝试其他常见密码
test_passwords = ["admin", "password", "123456", "admin12345"]
for pwd in test_passwords:
    print(f"\n尝试密码: '{pwd}'")
    result = verify_django_pbkdf2(pwd, full_hash)
    if result:
        print(f"✅ 匹配! 密码是: {pwd}")
        break
else:
    print("\n未找到匹配的密码")
