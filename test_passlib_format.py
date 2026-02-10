from passlib.context import CryptContext
import hashlib
import base64

ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 生成新哈希
password = "admin123"
new_hash = ctx.hash(password)

print(f"密码: {password}")
print(f"passlib 生成的哈希: {new_hash}")
print()

# 解析 passlib 格式
parts = new_hash.split('$')
print("passlib 哈希结构:")
for i, part in enumerate(parts):
    print(f"  Part {i}: {part}")

print()

# 验证
result = ctx.verify(password, new_hash)
print(f"passlib 验证结果: {result}")

# 手动验证
print()
print("手动验证:")
iterations = int(parts[2])
salt = parts[3]
expected = parts[4]

dk = hashlib.pbkdf2_hmac(
    'sha256',
    password.encode('utf-8'),
    salt.encode('utf-8'),
    iterations,
    dklen=32
)
computed = base64.b64encode(dk).decode('ascii')

print(f"  迭代次数: {iterations}")
print(f"  Salt: {salt}")
print(f"  预期: {expected}")
print(f"  计算: {computed}")
print(f"  匹配: {computed == expected}")
