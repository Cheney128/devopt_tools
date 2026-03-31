"""
主应用文件
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import api_router
from app.services.backup_scheduler import backup_scheduler
from app.services.ip_location_scheduler import ip_location_scheduler
from app.services.arp_mac_scheduler import arp_mac_scheduler
from app.models import get_db

# 配置日志
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理

    启动顺序：backup → ip_location → arp_mac
    关闭顺序：arp_mac → ip_location → backup（反向）

    包含完整的错误处理和回滚机制
    """
    # ========== Startup ==========
    db = next(get_db())
    startup_success = False

    try:
        # 打印数据库连接信息（隐藏密码）
        db_url = os.getenv('DATABASE_URL', '未设置')
        if db_url and '@' in db_url:
            parts = db_url.split('@')
            credentials = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
            masked_url = db_url.replace(credentials, '***:***')
        else:
            masked_url = db_url

        logger.info(f"[Startup] DATABASE_URL: {masked_url}")
        logger.info(f"[Startup] DEPLOY_MODE: {os.getenv('DEPLOY_MODE', '未设置')}")

        # 1. 加载并启动 backup_scheduler
        try:
            backup_scheduler.load_schedules(db)
            backup_scheduler.start()
            logger.info("[Startup] Backup scheduler started")
        except Exception as e:
            logger.warning(f"Could not start backup scheduler: {e}")

        # 2. 启动 ip_location_scheduler
        try:
            ip_location_scheduler.start()
            logger.info("[Startup] IP Location scheduler started (interval: 10 minutes)")
        except Exception as e:
            logger.warning(f"Could not start IP location scheduler: {e}")

        # 3. 启动 arp_mac_scheduler
        try:
            arp_mac_scheduler.start(db)
            logger.info("[Startup] ARP/MAC scheduler started (interval: 30 minutes)")
        except Exception as e:
            logger.warning(f"Could not start ARP/MAC scheduler: {e}")

        startup_success = True
        logger.info("[Startup] All schedulers started successfully")

        yield

    except Exception as e:
        # 错误处理：回滚已启动的调度器
        logger.error(f"Scheduler startup failed: {e}")

        # 反向关闭已启动的调度器
        try:
            arp_mac_scheduler.shutdown()
            logger.info("[Startup Rollback] ARP/MAC scheduler shutdown")
        except Exception as e2:
            logger.error(f"[Startup Rollback] ARP/MAC scheduler shutdown failed: {e2}")

        try:
            ip_location_scheduler.shutdown()
            logger.info("[Startup Rollback] IP Location scheduler shutdown")
        except Exception as e2:
            logger.error(f"[Startup Rollback] IP Location scheduler shutdown failed: {e2}")

        try:
            backup_scheduler.shutdown()
            logger.info("[Startup Rollback] Backup scheduler shutdown")
        except Exception as e2:
            logger.error(f"[Startup Rollback] Backup scheduler shutdown failed: {e2}")

        raise

    finally:
        # ========== Shutdown ==========
        logger.info("[Shutdown] Shutting down all schedulers...")

        # 反向关闭调度器（arp_mac → ip_location → backup）
        try:
            arp_mac_scheduler.shutdown()
            logger.info("[Shutdown] ARP/MAC scheduler shutdown complete")
        except Exception as e:
            logger.error(f"[Shutdown] ARP/MAC scheduler shutdown failed: {e}")

        try:
            ip_location_scheduler.shutdown()
            logger.info("[Shutdown] IP Location scheduler shutdown complete")
        except Exception as e:
            logger.error(f"[Shutdown] IP Location scheduler shutdown failed: {e}")

        try:
            backup_scheduler.shutdown()
            logger.info("[Shutdown] Backup scheduler shutdown complete")
        except Exception as e:
            logger.error(f"[Shutdown] Backup scheduler shutdown failed: {e}")

        # 关闭数据库 Session
        db.close()
        logger.info("[Shutdown] All schedulers shutdown complete, database session closed")


# 创建FastAPI应用实例（使用 lifespan 管理生命周期）
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
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
