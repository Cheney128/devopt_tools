"""
IP 定位 API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.schemas.ip_location_schemas import (
    IPLocationQueryResponse,
    IPLocationResult,
    IPListResponse,
    IPListEntry,
    CollectionStatus,
    CollectionTriggerResponse
)
from app.services.ip_location_service import get_ip_location_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search/{ip_address}", response_model=IPLocationQueryResponse)
async def search_ip(
    ip_address: str,
    db: Session = Depends(get_db)
):
    """
    搜索 IP 地址定位

    - **ip_address**: 要搜索的 IP 地址
    """
    try:
        service = get_ip_location_service(db)
        locations = service.locate_ip(ip_address)

        # 转换为响应模型
        location_results = [
            IPLocationResult(**loc) for loc in locations
        ]

        return IPLocationQueryResponse(
            success=True,
            ip_address=ip_address,
            locations=location_results,
            message=f"找到 {len(locations)} 条记录" if locations else "未找到该 IP 的定位信息"
        )
    except Exception as e:
        logger.error(f"搜索 IP {ip_address} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/list", response_model=IPListResponse)
async def list_ips(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取 IP 列表
    """
    try:
        service = get_ip_location_service(db)
        total, items = service.get_ip_list(page=page, page_size=page_size, search=search)

        # 转换为响应模型
        ip_entries = [
            IPListEntry(**item) for item in items
        ]

        return IPListResponse(
            total=total,
            items=ip_entries,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"获取 IP 列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/collection/status", response_model=CollectionStatus)
async def get_collection_status(
    db: Session = Depends(get_db)
):
    """
    获取数据收集状态
    """
    try:
        service = get_ip_location_service(db)
        status = service.collection_status
        return CollectionStatus(**status)
    except Exception as e:
        logger.error(f"获取收集状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/collection/trigger", response_model=CollectionTriggerResponse)
async def trigger_collection(
    db: Session = Depends(get_db)
):
    """
    触发数据收集任务
    """
    try:
        service = get_ip_location_service(db)
        result = await service.collect_from_all_devices()

        return CollectionTriggerResponse(
            success=result["success"],
            message=result["message"],
            status=CollectionStatus(**service.collection_status)
        )
    except Exception as e:
        logger.error(f"触发收集任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")