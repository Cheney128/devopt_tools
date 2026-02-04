"""
安全相关工具模块
包含密码哈希、JWT Token、验证码生成等功能
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import string
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import random

from app.config import settings


# 密码哈希上下文
# 使用pbkdf2_sha256方案，避免bcrypt的72字节密码长度限制
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# JWT 配置
SECRET_KEY = getattr(settings, 'SECRET_KEY', None)
if not SECRET_KEY:
    # 如果没有配置，生成一个随机密钥（仅用于开发环境）
    SECRET_KEY = secrets.token_urlsafe(32)
    
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 默认30分钟


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    bcrypt 限制密码长度不能超过 72 字节
    """
    # bcrypt 限制密码长度不能超过 72 字节
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希
    bcrypt 限制密码长度不能超过 72 字节
    """
    # bcrypt 限制密码长度不能超过 72 字节
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT 令牌
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_captcha_code(length: int = 4) -> str:
    """
    生成随机验证码
    """
    # 使用数字和大写字母，排除容易混淆的字符
    chars = ''.join(set(string.ascii_uppercase + string.digits) - set('0O1I'))
    return ''.join(random.choices(chars, k=length))


def generate_captcha_id() -> str:
    """
    生成验证码唯一标识
    """
    return secrets.token_urlsafe(32)


def create_captcha_image(code: str, width: int = 120, height: int = 40) -> str:
    """
    创建验证码图片，返回 base64 编码的数据 URL
    """
    # 创建图片
    image = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体，如果失败则使用默认字体
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Debian/Ubuntu (安装fonts-dejavu-core)
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # CentOS/RHEL
        "arial.ttf",  # Windows
    ]
    
    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 24)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)
    
    # 添加干扰点
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
    
    # 绘制验证码字符
    char_width = width // len(code)
    for i, char in enumerate(code):
        x = i * char_width + random.randint(5, 15)
        y = random.randint(5, 10)
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        draw.text((x, y), char, font=font, fill=color)
    
    # 转换为 base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
