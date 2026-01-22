"""
主应用文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import api_router
from app.services.backup_scheduler import backup_scheduler
from app.models import get_db

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS中间件
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
    # 加载备份任务
    db = next(get_db())
    backup_scheduler.load_schedules(db)


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