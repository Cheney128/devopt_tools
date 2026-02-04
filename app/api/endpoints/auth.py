"""
认证相关 API 端点
包含登录、登出、验证码等功能
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import get_db, User, Role, CaptchaRecord
from app.schemas.user_schemas import (
    LoginRequest, LoginResponse, CaptchaResponse,
    UserResponse
)
from app.core.security import (
    verify_password, create_access_token, get_password_hash,
    generate_captcha_code, generate_captcha_id, create_captcha_image
)
from app.api.deps import get_current_user

router = APIRouter()


# 登录失败锁定配置
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha(db: Session = Depends(get_db)):
    """
    获取验证码
    """
    # 生成验证码
    captcha_code = generate_captcha_code()
    captcha_id = generate_captcha_id()
    
    # 创建验证码图片
    captcha_image = create_captcha_image(captcha_code)
    
    # 保存到数据库
    expired_at = datetime.utcnow() + timedelta(minutes=5)
    captcha_record = CaptchaRecord(
        captcha_id=captcha_id,
        captcha_code=captcha_code.upper(),
        expired_at=expired_at
    )
    db.add(captcha_record)
    db.commit()
    
    return CaptchaResponse(
        captcha_id=captcha_id,
        captcha_image=captcha_image,
        expires_in=300
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    """
    # 1. 验证验证码
    captcha_record = db.query(CaptchaRecord).filter(
        CaptchaRecord.captcha_id == login_data.captcha_id
    ).first()
    
    if not captcha_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码不存在或已过期"
        )
    
    if captcha_record.used:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码已使用，请重新获取"
        )
    
    if captcha_record.expired_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码已过期"
        )
    
    if captcha_record.captcha_code != login_data.captcha_code.upper():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码错误"
        )
    
    # 标记验证码已使用
    captcha_record.used = True
    db.commit()
    
    # 2. 查找用户
    user = db.query(User).filter(
        User.username == login_data.username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 3. 检查账号是否被锁定
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"账号已锁定，请 {remaining_minutes} 分钟后重试"
        )
    
    # 4. 检查账号状态
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )
    
    # 5. 验证密码
    if not verify_password(login_data.password, user.password_hash):
        # 增加失败次数
        user.failed_login_attempts += 1
        
        # 如果达到最大失败次数，锁定账号
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"密码错误次数过多，账号已锁定 {LOCK_DURATION_MINUTES} 分钟"
            )
        
        db.commit()
        remaining_attempts = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，还剩 {remaining_attempts} 次机会"
        )
    
    # 6. 登录成功，重置失败次数并更新登录信息
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.client.host if request.client else None
    db.commit()
    
    # 7. 创建访问令牌
    # 如果选择了"记住我"，延长令牌有效期
    if login_data.remember:
        expires_delta = timedelta(days=7)  # 7天
        expires_in = 7 * 24 * 60 * 60
    else:
        expires_delta = timedelta(minutes=30)  # 30分钟
        expires_in = 30 * 60
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=expires_delta
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出
    
    第一阶段仅做前端清理，后端记录登出事件（可选）
    """
    # 这里可以添加登出日志记录
    # 后续可以在这里实现 token 黑名单
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    """
    return UserResponse.model_validate(current_user)
