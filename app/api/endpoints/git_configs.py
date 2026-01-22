"""
Git配置管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.models import get_db
from app.models.models import GitConfig
from app.schemas.schemas import GitConfig as GitConfigSchema, GitConfigCreate, GitConfigUpdate
from app.services.git_service import get_git_service, GitService

# 创建路由器
router = APIRouter()


@router.get("/", response_model=List[GitConfigSchema])
def get_git_configs(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取Git配置列表
    """
    query = db.query(GitConfig)
    
    if is_active is not None:
        query = query.filter(GitConfig.is_active == is_active)
    
    git_configs = query.order_by(GitConfig.created_at.desc()).offset(skip).limit(limit).all()
    return git_configs


@router.get("/{config_id}", response_model=GitConfigSchema)
def get_git_config(config_id: int, db: Session = Depends(get_db)):
    """
    获取Git配置详情
    """
    git_config = db.query(GitConfig).filter(GitConfig.id == config_id).first()
    if not git_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitConfig with id {config_id} not found"
        )
    return git_config


@router.post("/", response_model=GitConfigSchema, status_code=status.HTTP_201_CREATED)
def create_git_config(
    git_config: GitConfigCreate,
    db: Session = Depends(get_db)
):
    """
    创建Git配置
    """
    # 检查是否已存在相同的仓库URL
    existing_config = db.query(GitConfig).filter(GitConfig.repo_url == git_config.repo_url).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitConfig with repo_url {git_config.repo_url} already exists"
        )
    
    # 如果是新的活跃配置，将其他配置设置为非活跃
    if git_config.is_active:
        db.query(GitConfig).filter(GitConfig.is_active == True).update({"is_active": False})
    
    # 创建Git配置记录
    db_git_config = GitConfig(**git_config.model_dump())
    db.add(db_git_config)
    db.commit()
    db.refresh(db_git_config)
    return db_git_config


@router.put("/{config_id}", response_model=GitConfigSchema)
def update_git_config(
    config_id: int,
    git_config: GitConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    更新Git配置
    """
    # 检查Git配置是否存在
    db_git_config = db.query(GitConfig).filter(GitConfig.id == config_id).first()
    if not db_git_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitConfig with id {config_id} not found"
        )
    
    # 检查仓库URL是否已被其他配置使用
    if git_config.repo_url and git_config.repo_url != db_git_config.repo_url:
        existing_config = db.query(GitConfig).filter(GitConfig.repo_url == git_config.repo_url).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitConfig with repo_url {git_config.repo_url} already exists"
            )
    
    # 如果设置为活跃，将其他配置设置为非活跃
    if git_config.is_active == True:
        db.query(GitConfig).filter(GitConfig.is_active == True).update({"is_active": False})
    
    # 更新Git配置
    update_data = git_config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_git_config, field, value)
    
    db.commit()
    db.refresh(db_git_config)
    return db_git_config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_git_config(config_id: int, db: Session = Depends(get_db)):
    """
    删除Git配置
    """
    git_config = db.query(GitConfig).filter(GitConfig.id == config_id).first()
    if not git_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitConfig with id {config_id} not found"
        )
    
    db.delete(git_config)
    db.commit()
    return None


@router.post("/{config_id}/test", response_model=Dict[str, Any])
def test_git_connection(
    config_id: int,
    db: Session = Depends(get_db),
    git_service: GitService = Depends(get_git_service)
):
    """
    测试Git连接
    """
    git_config = db.query(GitConfig).filter(GitConfig.id == config_id).first()
    if not git_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitConfig with id {config_id} not found"
        )
    
    result = git_service.test_connection(git_config)
    return result


@router.post("/active/{config_id}", response_model=GitConfigSchema)
def set_active_git_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """
    设置活跃的Git配置
    """
    # 检查Git配置是否存在
    git_config = db.query(GitConfig).filter(GitConfig.id == config_id).first()
    if not git_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GitConfig with id {config_id} not found"
        )
    
    # 将所有配置设置为非活跃
    db.query(GitConfig).update({"is_active": False})
    
    # 将当前配置设置为活跃
    git_config.is_active = True
    db.commit()
    db.refresh(git_config)
    
    return git_config