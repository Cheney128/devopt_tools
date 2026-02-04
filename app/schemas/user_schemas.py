"""
用户相关的 Pydantic Schema 定义
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator


# ==================== 基础 Schema ====================

class RoleBase(BaseModel):
    """角色基础 Schema"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class RoleCreate(RoleBase):
    """创建角色 Schema"""
    pass


class RoleResponse(RoleBase):
    """角色响应 Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 用户 Schema ====================

class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=100)
    nickname: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class UserCreate(UserBase):
    """创建用户 Schema"""
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="user", pattern="^(admin|user)$")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v


class UserUpdate(BaseModel):
    """更新用户 Schema"""
    nickname: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")


class UserResponse(UserBase):
    """用户响应 Schema"""
    id: int
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    roles: List[RoleResponse] = []
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应 Schema"""
    total: int
    items: List[UserResponse]
    page: int
    page_size: int


# ==================== 认证相关 Schema ====================

class CaptchaResponse(BaseModel):
    """验证码响应 Schema"""
    captcha_id: str
    captcha_image: str
    expires_in: int = 300  # 5分钟


class LoginRequest(BaseModel):
    """登录请求 Schema"""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    captcha_id: str = Field(..., min_length=1)
    captcha_code: str = Field(..., min_length=1, max_length=10)
    remember: Optional[bool] = False


class LoginResponse(BaseModel):
    """登录响应 Schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class PasswordResetRequest(BaseModel):
    """重置密码请求 Schema（管理员使用）"""
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordChangeRequest(BaseModel):
    """修改密码请求 Schema（用户自己使用）"""
    old_password: str = Field(..., min_length=1, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)


class ProfileUpdateRequest(BaseModel):
    """更新个人信息请求 Schema"""
    nickname: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = Field(None, max_length=255)


# ==================== Token Schema ====================

class TokenPayload(BaseModel):
    """Token Payload Schema"""
    sub: Optional[int] = None  # 用户ID
    exp: Optional[datetime] = None


class TokenData(BaseModel):
    """Token 数据 Schema"""
    user_id: Optional[int] = None
