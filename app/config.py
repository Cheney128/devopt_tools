"""
应用配置模块
"""
from dotenv import load_dotenv
import os
from typing import Optional

# 配置优先级修复：
# 1. 合一部署模式：完全依赖环境变量，不加载.env
# 2. 非合一部署模式：加载.env，但使用override=False避免覆盖已有环境变量
if os.getenv('DEPLOY_MODE') != 'unified':
    load_dotenv(override=False)  # 不覆盖已存在的环境变量

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

        # API配置
        self.API_V1_STR = os.getenv('API_V1_STR', '/api/v1')
        self.PROJECT_NAME = os.getenv('PROJECT_NAME', 'Switch Manage System')

        # CORS配置
        self.BACKEND_CORS_ORIGINS = [
            "http://localhost:5173",  # Vite开发服务器
            "http://localhost:3000",  # 备用开发端口
        ]


# 创建全局配置实例
settings = Settings()
