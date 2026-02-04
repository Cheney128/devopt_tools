"""
主应用文件
"""
import os
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
    # 打印数据库连接信息（隐藏密码）
    db_url = os.getenv('DATABASE_URL', '未设置')
    # 隐藏密码部分
    if db_url and '@' in db_url:
        parts = db_url.split('@')
        credentials = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
        masked_url = db_url.replace(credentials, '***:***')
    else:
        masked_url = db_url

    print(f"[Startup] DATABASE_URL: {masked_url}")
    print(f"[Startup] DEPLOY_MODE: {os.getenv('DEPLOY_MODE', '未设置')}")

    # 加载备份任务
    try:
        db = next(get_db())
        backup_scheduler.load_schedules(db)
    except Exception as e:
        print(f"Warning: Could not load backup schedules from database: {e}")
        print("Application will continue without backup scheduler functionality.")


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
