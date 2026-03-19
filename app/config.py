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

        # JWT 密钥配置 - 使用固定密钥，避免后端重启后 token 失效
        # 生产环境应该通过环境变量设置，开发环境使用默认密钥
        self.SECRET_KEY = (os.getenv('SECRET_KEY') or '').strip() or 'switch-manage-dev-secret-key-2024-very-long-and-secure'

        # CORS配置
        self.BACKEND_CORS_ORIGINS = [
            "http://localhost:5173",  # Vite开发服务器
            "http://localhost:5174",  # Vite开发服务器（备用端口）
            "http://localhost:3000",  # 备用开发端口
        ]
        
        # 延迟检测配置
        self.LATENCY_CHECK_ENABLED = os.getenv('LATENCY_CHECK_ENABLED', 'True').lower() == 'true'
        self.LATENCY_CHECK_INTERVAL = int(os.getenv('LATENCY_CHECK_INTERVAL', '5'))
        self.LATENCY_CHECK_TIMEOUT = int(os.getenv('LATENCY_CHECK_TIMEOUT', '5'))
        self.LATENCY_CHECK_RETRY_COUNT = int(os.getenv('LATENCY_CHECK_RETRY_COUNT', '2'))

        # IP 定位配置
        self.IP_LOCATION_COLLECTION_ENABLED = os.getenv("IP_LOCATION_COLLECTION_ENABLED", "True").lower() == "true"
        self.IP_LOCATION_COLLECTION_INTERVAL_HOURS = int(os.getenv("IP_LOCATION_COLLECTION_INTERVAL_HOURS", "3"))
        self.IP_LOCATION_BATCH_SIZE = int(os.getenv("IP_LOCATION_BATCH_SIZE", "20"))
        self.IP_LOCATION_BATCH_INTERVAL_SECONDS = int(os.getenv("IP_LOCATION_BATCH_INTERVAL_SECONDS", "120"))
        self.IP_LOCATION_MAX_CONCURRENT = int(os.getenv("IP_LOCATION_MAX_CONCURRENT", "10"))
        self.IP_LOCATION_DATA_RETENTION_DAYS = int(os.getenv("IP_LOCATION_DATA_RETENTION_DAYS", "7"))
        self.IP_LOCATION_SILENT_HOURS = [int(h) for h in os.getenv("IP_LOCATION_SILENT_HOURS", "").split(",") if h.strip()]


# 创建全局配置实例
settings = Settings()
