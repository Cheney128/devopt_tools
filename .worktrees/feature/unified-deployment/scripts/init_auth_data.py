"""
初始化认证相关数据
创建初始角色和管理员账号
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models import get_db, User, Role, engine, SessionLocal
from app.models.user_models import Base as UserBase
from app.core.security import get_password_hash


def init_roles(db: Session):
    """
    初始化角色数据
    """
    roles = [
        {"name": "admin", "description": "系统管理员，拥有所有权限"},
        {"name": "user", "description": "普通用户，拥有基本操作权限"}
    ]
    
    created_roles = []
    for role_data in roles:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            created_roles.append(role_data["name"])
    
    db.commit()
    if created_roles:
        print(f"✓ 创建角色: {', '.join(created_roles)}")
    else:
        print("✓ 角色已存在，跳过创建")


def init_admin_user(db: Session):
    """
    初始化管理员账号
    """
    admin_username = "admin"
    admin_password = "admin123"
    
    # 检查是否已存在管理员
    existing_admin = db.query(User).filter(User.username == admin_username).first()
    if existing_admin:
        print(f"✓ 管理员账号 '{admin_username}' 已存在，跳过创建")
        return
    
    # 获取 admin 角色
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        print("✗ 错误: admin 角色不存在，请先运行 init_roles()")
        return
    
    # 创建管理员用户
    admin_user = User(
        username=admin_username,
        password_hash=get_password_hash(admin_password),
        nickname="系统管理员",
        email="admin@example.com",
        status="active",
        is_superuser=True
    )
    admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    
    print(f"✓ 创建管理员账号: {admin_username}")
    print(f"  默认密码: {admin_password}")
    print(f"  请登录后及时修改密码！")


def init_database_tables():
    """
    创建用户认证相关的数据库表
    """
    # 导入所有模型以确保表被创建
    from app.models.user_models import User, Role, Permission, CaptchaRecord, user_roles, role_permissions
    
    print("正在创建用户认证相关表...")
    UserBase.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")


def main():
    """
    主函数
    """
    print("=" * 50)
    print("初始化认证相关数据")
    print("=" * 50)
    
    # 创建数据库表
    init_database_tables()
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 初始化角色
        print("\n[1/2] 初始化角色...")
        init_roles(db)
        
        # 初始化管理员账号
        print("\n[2/2] 初始化管理员账号...")
        init_admin_user(db)
        
        print("\n" + "=" * 50)
        print("初始化完成！")
        print("=" * 50)
        print("\n默认登录信息:")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n请登录后及时修改默认密码！")
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
