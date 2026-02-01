"""
应用配置模块
"""
from dotenv import load_dotenv
import os
from typing import Optional

# 手动加载 .env 文件
load_dotenv()

class Settings:
    """
    应用配置类
    """
    def __init__(self):
        # 应用基本配置
        self.APP_NAME = os.getenv('APP_NAME', 'Switch Manage System')
        self.APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
        self.DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

        # 数据库配置
        self.DATABASE_URL = os.getenv('DATABASE_URL')

        # Oxidized配置
        self.OXIDIZED_URL = os.getenv('OXIDIZED_URL', 'http://localhost:8888')

        # API配置
        self.API_V1_STR = os.getenv('API_V1_STR', '/api/v1')
        self.PROJECT_NAME = os.getenv('PROJECT_NAME', 'Switch Manage System')

        # CORS配置
        self.BACKEND_CORS_ORIGINS = ["*"]


# 创建全局配置实例
settings = Settings()

