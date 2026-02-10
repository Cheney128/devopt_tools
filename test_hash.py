import sqlite3
from passlib.context import CryptContext

# 数据库中的哈希
hash_from_db = "$pbkdf2-sha256$29000$FQLAGKN0LoVQKsWYk7L2Pg$KO0eMccQENQ/nzpnTIQmdsKCSBCvdlLuodpW..."

# 测试不同的配置
print("=== 测试 passlib 配置 ===\n")

# 配置1: pbkdf2_sha256
ctx1 = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
print("配置1: schemes=['pbkdf2_sha256']")
try:
    result = ctx1.identify(hash_from_db)
    print(f"  identify() 结果: {result}")
except Exception as e:
    print(f"  identify() 错误: {type(e).__name__}: {e}")

try:
    result = ctx1.verify("admin123", hash_from_db)
    print(f"  verify('admin123', hash) 结果: {result}")
except Exception as e:
    print(f"  verify() 错误: {type(e).__name__}: {e}")

print()

# 配置2: 带 deprecated 和 default
ctx2 = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    default="pbkdf2_sha256"
)
print("配置2: schemes=['pbkdf2_sha256'], deprecated='auto', default='pbkdf2_sha256'")
try:
    result = ctx2.identify(hash_from_db)
    print(f"  identify() 结果: {result}")
except Exception as e:
    print(f"  identify() 错误: {type(e).__name__}: {e}")

try:
    result = ctx2.verify("admin123", hash_from_db)
    print(f"  verify('admin123', hash) 结果: {result}")
except Exception as e:
    print(f"  verify() 错误: {type(e).__name__}: {e}")

print()

# 检查哈希字符串的格式
print("=== 哈希格式分析 ===")
print(f"原始哈希: {hash_from_db}")
print(f"长度: {len(hash_from_db)}")
print(f"前20字符: {hash_from_db[:20]}")
