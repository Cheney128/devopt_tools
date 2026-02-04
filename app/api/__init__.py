"""
API路由主文件
"""
from fastapi import APIRouter

from app.api.endpoints import devices, ports, vlans, inspections, configurations, device_collection, git_configs, command_templates, command_history, auth, users

# 创建API路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(ports.router, prefix="/ports", tags=["ports"])
api_router.include_router(vlans.router, prefix="/vlans", tags=["vlans"])
api_router.include_router(inspections.router, prefix="/inspections", tags=["inspections"])
api_router.include_router(configurations.router, prefix="/configurations", tags=["configurations"])
api_router.include_router(device_collection.router, prefix="/device-collection", tags=["device-collection"])
api_router.include_router(git_configs.router, prefix="/git-configs", tags=["git-configs"])
api_router.include_router(command_templates.router, prefix="/command-templates", tags=["command-templates"])
api_router.include_router(command_history.router, prefix="/command-history", tags=["command-history"])
