"""
主应用文件
"""
import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import api_router
from app.services.backup_scheduler import backup_scheduler
from app.services.latency_scheduler import init_latency_scheduler
from app.models import get_db

logger = logging.getLogger(__name__)

# 全局主事件循环引用
_main_event_loop = None


def get_main_event_loop() -> asyncio.AbstractEventLoop:
    """
    获取主事件循环引用
    
    Returns:
        asyncio.AbstractEventLoop: 主事件循环对象
        
    Raises:
        RuntimeError: 如果主事件循环未初始化
    """
    if _main_event_loop is None:
        raise RuntimeError("Main event loop not initialized. Call init_main_event_loop() first.")
    return _main_event_loop


def init_main_event_loop() -> None:
    """
    初始化主事件循环引用
    应该在 FastAPI startup 事件中调用
    """
    global _main_event_loop
    _main_event_loop = asyncio.get_running_loop()
    logger.info(f"[MainLoop] Main event loop initialized: {_main_event_loop}")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS中间件
# 合一部署：CORS可以放宽，因为前端和后端同源
if os.getenv('DEPLOY_MODE') == 'unified':
    # 合一部署：同源访问，CORS限制可放宽
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:80"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 分离部署：需要允许前端域名
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    # 初始化主事件循环引用
    init_main_event_loop()
    
    # 打印数据库连接信息（隐藏密码）
    db_url = os.getenv('DATABASE_URL', '未设置')
    # 隐藏密码部分
    if db_url and '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
        masked_url = db_url.replace(credentials, '***:***')
    else:
        masked_url = db_url

    logger.info(f"[Startup] DATABASE_URL: {masked_url}")
    logger.info(f"[Startup] DEPLOY_MODE: {os.getenv('DEPLOY_MODE', '未设置')}")

    # 加载备份任务
    try:
        logger.info("[Startup] Loading backup schedules...")
        db = next(get_db())
        backup_scheduler.load_schedules(db)
        logger.info("[Startup] Backup schedules loaded successfully")
    except Exception as e:
        logger.error(f"[Startup] Could not load backup schedules from database: {e}")
        logger.error("[Startup] Application will continue without backup scheduler functionality.")
    
    # 启动延迟检测调度器
    try:
        logger.info("[Startup] Starting latency scheduler...")
        latency_scheduler = init_latency_scheduler(
            enabled=settings.LATENCY_CHECK_ENABLED,
            interval_minutes=settings.LATENCY_CHECK_INTERVAL
        )
        latency_scheduler.start()
        logger.info(f"[Startup] Latency scheduler started (enabled={settings.LATENCY_CHECK_ENABLED}, interval={settings.LATENCY_CHECK_INTERVAL}min)")
    except Exception as e:
        logger.error(f"[Startup] Could not start latency scheduler: {e}")
        logger.error("[Startup] Application will continue without latency scheduler functionality.")


@app.get("/")
async def root():
    """
    根路径
    """
    return {
        "message": "Welcome to Switch Manage System",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "healthy"}
