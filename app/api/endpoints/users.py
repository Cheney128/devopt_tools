"""
用户管理相关 API 端点
包含用户列表、创建、更新、删除、重置密码等功能
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models import get_db, User, Role
from app.schemas.user_schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    PasswordResetRequest, ProfileUpdateRequest, PasswordChangeRequest
)
from app.core.security import get_password_hash, verify_password
from app.api.deps import get_current_user, check_admin_permission

router = APIRouter()


@router.get("", response_model=UserListResponse)
def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词（用户名/昵称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    role: Optional[str] = Query(None, description="角色筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    获取用户列表（管理员权限）
    """
    query = db.query(User)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.nickname.ilike(f"%{keyword}%")
            )
        )
    
    # 状态筛选
    if status:
        query = query.filter(User.status == status)
    
    # 角色筛选
    if role:
        query = query.join(User.roles).filter(Role.name == role)
    
    # 计算总数
    total = query.count()
    
    # 分页
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(user) for user in users],
        page=page,
        page_size=page_size
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    创建用户（管理员权限）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在"
        )
    
    # 创建用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        nickname=user_data.nickname,
        email=user_data.email,
        phone=user_data.phone,
        status=user_data.status
    )
    
    # 分配角色
    role = db.query(Role).filter(Role.name == user_data.role).first()
    if role:
        new_user.roles.append(role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    获取当前用户个人信息
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    profile_data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新当前用户个人信息
    """
    # 更新字段
    if profile_data.nickname is not None:
        current_user.nickname = profile_data.nickname
    if profile_data.email is not None:
        current_user.email = profile_data.email
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.avatar is not None:
        current_user.avatar = profile_data.avatar
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.put("/me/password")
def change_my_password(
    password_data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改当前用户密码
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"ok": True}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    获取指定用户信息（管理员权限）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    更新用户信息（管理员权限）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能修改自己的角色（避免管理员把自己降级）
    if user.id == current_user.id and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    # 更新字段
    if user_data.nickname is not None:
        user.nickname = user_data.nickname
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.status is not None:
        user.status = user_data.status
    
    # 更新角色
    if user_data.role is not None:
        # 清除现有角色
        user.roles = []
        role = db.query(Role).filter(Role.name == user_data.role).first()
        if role:
            user.roles.append(role)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    重置用户密码（管理员权限）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 重置密码
    user.password_hash = get_password_hash(password_data.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"ok": True}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin_permission)
):
    """
    删除用户（管理员权限）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录用户"
        )
    
    db.delete(user)
    db.commit()
    
    return None
