"""
测试 SQLAlchemy 连接
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

print(f"Testing SQLAlchemy connection with: {settings.DATABASE_URL}")

try:
    # 创建引擎
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    print("✅ Engine created successfully")
    
    # 测试连接
    print("Testing connection...")
    with engine.connect() as conn:
        print("✅ Connection successful!")
        
        # 测试查询
        result = conn.execute("SELECT VERSION()")
        version = result.scalar()
        print(f"MySQL Version: {version}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
