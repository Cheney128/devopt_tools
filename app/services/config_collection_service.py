# -*- coding: utf-8 -*-
"""
配置采集服务

功能：
从设备采集配置的核心业务逻辑，不依赖 FastAPI Depends 注入。
供 API 端点和 backup_scheduler 调用。
"""

import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session
from app.models.models import Configuration, Device, GitConfig
from app.services.netmiko_service import NetmikoService
from app.services.git_service import GitService

logger = logging.getLogger(__name__)


async def collect_device_config(
    device_id: int,
    db: Session,
    netmiko_service: NetmikoService,
    git_service: GitService
) -> Dict[str, Any]:
    """
    从设备采集配置的核心服务函数

    Args:
        device_id: 设备 ID
        db: 数据库 Session（由调用方管理生命周期）
        netmiko_service: Netmiko 服务实例
        git_service: Git 服务实例

    Returns:
        Dict[str, Any]: 采集结果，包含：
            - success: bool - 是否成功
            - message: str - 结果消息
            - config_id: int - 配置记录 ID（可选）
            - version: str - 配置版本（可选）
            - config_changed: bool - 配置是否有变化（可选）
            - config_size: int - 配置大小（可选）
            - git_commit_id: str - Git 提交 ID（可选）
    """
    try:
        # 检查设备是否存在
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return {"success": False, "message": "Device not found"}

        # 从设备获取配置
        config_content = await netmiko_service.collect_running_config(device)
        if not config_content:
            return {"success": False, "message": "Failed to get config from device"}

        # 获取设备最新配置
        latest_config = db.query(Configuration).filter(
            Configuration.device_id == device_id
        ).order_by(Configuration.config_time.desc()).first()

        # 检查配置是否有变化
        if latest_config and latest_config.config_content == config_content:
            return {
                "success": True,
                "message": "配置无变化，已成功登录并验证",
                "config_id": latest_config.id,
                "config_changed": False,
                "config_size": len(config_content) if config_content else 0
            }

        # 生成版本号
        new_version = "1.0"
        if latest_config:
            current_version = latest_config.version
            try:
                major, minor = map(int, current_version.split("."))
                new_version = f"{major}.{minor + 1}"
            except:
                new_version = "1.0"

        # 创建新的配置记录
        new_config = Configuration(
            device_id=device_id,
            config_content=config_content,
            version=new_version,
            change_description="Auto-collected from device"
        )

        # 检查是否有 Git 配置，如果有则提交到 Git
        git_commit_id = None
        try:
            git_config = db.query(GitConfig).filter(GitConfig.is_active == True).first()
            if git_config:
                # 为每个设备创建新的 GitService 实例，避免单例模式下的资源冲突
                device_git_service = GitService()
                if device_git_service.init_repo(git_config):
                    commit_id = device_git_service.commit_config(
                        device.hostname,
                        config_content,
                        f"Auto-update config for {device.hostname} at {datetime.now()}"
                    )
                    if commit_id:
                        device_git_service.push_to_remote()
                        git_commit_id = commit_id
                    device_git_service.close()
        except Exception as git_error:
            logger.warning(f"Git operation error: {str(git_error)}")
            # Git 操作失败不影响配置获取，继续执行

        # 保存 Git 提交 ID
        if git_commit_id:
            new_config.git_commit_id = git_commit_id

        # 保存到数据库
        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        return {
            "success": True,
            "message": "Config collected from device and saved",
            "config_id": new_config.id,
            "version": new_config.version,
            "config_changed": True,
            "config_size": len(config_content) if config_content else 0,
            "git_commit_id": git_commit_id
        }

    except Exception as e:
        logger.error(f"Error in collect_device_config: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to collect config: {str(e)}"
        }