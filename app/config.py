from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    """
    # 应用基本配置
    APP_NAME: str = "Switch Manage System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str
    
    # Oxidized配置
    OXIDIZED_URL: Optional[str] = "http://localhost:8888"
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Switch Manage System"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()