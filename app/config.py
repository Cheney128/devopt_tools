"""
应用配置模块
"""
from dotenv import load_dotenv
import os
from typing import Optional

# 配置优先级修复：
# 1. 合一部署模式：完全依赖环境变量，不加载.env
# 2. 非合一部署模式：加载.env，但使用 override=False 避免覆盖已有环境变量
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

        # API 配置
        self.API_V1_STR = os.getenv('API_V1_STR', '/api/v1')
        self.PROJECT_NAME = os.getenv('PROJECT_NAME', 'Switch Manage System')

        # JWT 密钥配置 - 使用固定密钥，避免后端重启后 token 失效
        # 生产环境应该通过环境变量设置，开发环境使用默认密钥
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'switch-manage-dev-secret-key-2024-very-long-and-secure')

        # CORS 配置
        self.BACKEND_CORS_ORIGINS = [
            "http://localhost:5173",  # Vite 开发服务器
            "http://localhost:3000",  # 备用开发端口
        ]

        # ARP/MAC 采集配置
        self.ARP_MAC_COLLECTION_ENABLED = os.getenv('ARP_MAC_COLLECTION_ENABLED', 'True').lower() == 'true'
        self.ARP_MAC_COLLECTION_ON_STARTUP = os.getenv('ARP_MAC_COLLECTION_ON_STARTUP', 'True').lower() == 'true'
        self.ARP_MAC_COLLECTION_INTERVAL = int(
            os.getenv('ARP_MAC_COLLECTION_INTERVAL', '30')
        )

        # Netmiko 超时配置（最终方案）
        self.NETMIKO_DEFAULT_TIMEOUT = int(os.getenv('NETMIKO_DEFAULT_TIMEOUT', '20'))
        self.NETMIKO_ARP_TABLE_TIMEOUT = int(os.getenv('NETMIKO_ARP_TABLE_TIMEOUT', '65'))
        self.NETMIKO_MAC_TABLE_TIMEOUT = int(os.getenv('NETMIKO_MAC_TABLE_TIMEOUT', '95'))
        self.NETMIKO_MAX_TIMEOUT = int(os.getenv('NETMIKO_MAX_TIMEOUT', '240'))
        self.NETMIKO_NETWORK_DELAY_COMPENSATION = int(os.getenv('NETMIKO_NETWORK_DELAY_COMPENSATION', '5'))
        self.NETMIKO_DYNAMIC_TIMEOUT_ENABLED = os.getenv('NETMIKO_DYNAMIC_TIMEOUT_ENABLED', 'True').lower() == 'true'
        self.NETMIKO_USE_OPTIMIZED_METHOD = os.getenv('NETMIKO_USE_OPTIMIZED_METHOD', 'True').lower() == 'true'


# 创建全局配置实例
settings = Settings()
