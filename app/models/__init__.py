"""
数据库模块
提供数据库引擎、会话管理和模型基类
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.models import Base
from app.models.user_models import User, Role, Permission, CaptchaRecord, user_roles, role_permissions

# 配置 pymysql 作为 MySQL 驱动
import pymysql
pymysql.install_as_MySQLdb()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依赖项：获取数据库会话
def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = [
    'Base', 'get_db', 'engine', 'SessionLocal',
    'User', 'Role', 'Permission', 'CaptchaRecord',
    'user_roles', 'role_permissions'
]