"""
命令模板管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import get_db
from app.models.models import CommandTemplate as CommandTemplateModel
from app.schemas.schemas import (
    CommandTemplate,
    CommandTemplateCreate,
    CommandTemplateUpdate,
    BaseResponse
)

# 创建路由器
router = APIRouter()


@router.get("/", response_model=BaseResponse)
def get_command_templates(
    page: int = 1,
    page_size: int = 10,
    vendor: Optional[str] = None,
    device_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    tags: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取命令模板列表
    """
    # 转换page和page_size为skip和limit
    skip = (page - 1) * page_size
    limit = page_size
    
    query = db.query(CommandTemplateModel)
    
    if vendor:
        query = query.filter(CommandTemplateModel.vendor == vendor)
    
    if device_type:
        query = query.filter(CommandTemplateModel.device_type == device_type)
    
    if is_public is not None:
        query = query.filter(CommandTemplateModel.is_public == is_public)
    
    if tags:
        # 标签过滤（简单实现，仅匹配完全一致的标签）
        query = query.filter(CommandTemplateModel.tags.contains([tags]))
    
    # 获取总记录数
    total = query.count()
    # 获取分页数据
    templates = query.offset(skip).limit(limit).all()
    
    # 将数据库模型转换为Pydantic模型
    template_responses = [CommandTemplate.model_validate(template) for template in templates]
    
    # 计算总页数
    pages = (total + page_size - 1) // page_size
    
    return {
        "success": True,
        "message": "获取命令模板列表成功",
        "data": {
            "total": total,
            "items": template_responses,
            "page": page,
            "size": page_size,
            "pages": pages
        }
    }


@router.get("/{template_id}")
def get_command_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个命令模板详情
    """
    template = db.query(CommandTemplateModel).filter(CommandTemplateModel.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command template with id {template_id} not found"
        )
    
    # 将数据库模型转换为Pydantic模型
    template_response = CommandTemplate.model_validate(template)
    
    return {
        "success": True,
        "message": "获取命令模板详情成功",
        "data": template_response
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_command_template(
    template: CommandTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    创建命令模板
    """
    # 检查模板名称是否已存在
    existing_template = db.query(CommandTemplateModel).filter(CommandTemplateModel.name == template.name).first()
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Command template with name {template.name} already exists"
        )
    
    # 创建模板
    db_template = CommandTemplateModel(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # 将数据库模型转换为Pydantic模型
    template_response = CommandTemplate.model_validate(db_template)
    
    return {
        "success": True,
        "message": "创建命令模板成功",
        "data": template_response
    }


@router.put("/{template_id}")
def update_command_template(
    template_id: int,
    template_update: CommandTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    更新命令模板
    """
    db_template = db.query(CommandTemplateModel).filter(CommandTemplateModel.id == template_id).first()
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command template with id {template_id} not found"
        )
    
    # 检查模板名称是否已被其他模板使用
    if template_update.name and template_update.name != db_template.name:
        existing_template = db.query(CommandTemplateModel).filter(CommandTemplateModel.name == template_update.name).first()
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Command template with name {template_update.name} already exists"
            )
    
    # 更新模板信息
    update_data = template_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)
    
    db.commit()
    db.refresh(db_template)
    
    # 将数据库模型转换为Pydantic模型
    template_response = CommandTemplate.model_validate(db_template)
    
    return {
        "success": True,
        "message": "更新命令模板成功",
        "data": template_response
    }


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_command_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    删除命令模板
    """
    db_template = db.query(CommandTemplateModel).filter(CommandTemplateModel.id == template_id).first()
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Command template with id {template_id} not found"
        )
    
    db.delete(db_template)
    db.commit()
    return None


@router.get("/vendor/{vendor}")
def get_templates_by_vendor(
    vendor: str,
    db: Session = Depends(get_db)
):
    """
    根据厂商获取命令模板
    """
    templates = db.query(CommandTemplateModel).filter(CommandTemplateModel.vendor == vendor, CommandTemplateModel.is_public == True).all()
    
    # 将数据库模型转换为Pydantic模型
    template_responses = [CommandTemplate.model_validate(template) for template in templates]
    
    return {
        "success": True,
        "message": f"获取{vendor}厂商的命令模板成功",
        "data": template_responses
    }


@router.get("/device-type/{device_type}")
def get_templates_by_device_type(
    device_type: str,
    db: Session = Depends(get_db)
):
    """
    根据设备类型获取命令模板
    """
    templates = db.query(CommandTemplateModel).filter(CommandTemplateModel.device_type == device_type, CommandTemplateModel.is_public == True).all()
    
    # 将数据库模型转换为Pydantic模型
    template_responses = [CommandTemplate.model_validate(template) for template in templates]
    
    return {
        "success": True,
        "message": f"获取{device_type}设备类型的命令模板成功",
        "data": template_responses
    }
