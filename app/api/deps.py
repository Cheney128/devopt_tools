"""
API 依赖项
包含认证依赖、权限检查等
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models import get_db, User, Role
from app.core.security import decode_access_token


# 使用 HTTPBearer 获取 token
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    """
    return current_user


def check_admin_permission(current_user: User = Depends(get_current_user)) -> User:
    """
    检查管理员权限
    """
    # 检查是否为超级管理员
    if current_user.is_superuser:
        return current_user
    
    # 检查是否有 admin 角色
    role_names = [role.name for role in current_user.roles]
    if "admin" in role_names:
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足，需要管理员权限"
    )


def require_roles(required_roles: list):
    """
    角色权限检查装饰器工厂
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_names = [role.name for role in current_user.roles]
        
        # 超级管理员拥有所有权限
        if current_user.is_superuser:
            return current_user
        
        # 检查是否有所需角色
        if not any(role in role_names for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker
