# -*- coding: utf-8 -*-
"""
IP 定位验证服务

提供快照批次的验证和激活功能，支持基于差异比例的验证决策和回滚操作。

功能：
- 批次验证：根据采样总数和差异数量计算差异比例，与阈值比较决定是否激活
- 批次激活：验证通过后激活候选批次
- 回滚操作：回滚到指定的历史批次

使用示例：
    >>> from app.services.ip_location_validation_service import IPLocationValidationService
    >>> validator = IPLocationValidationService(db)
    >>> result = validator.validate_and_activate_batch(
    ...     candidate_batch_id="batch_001",
    ...     sample_total=1000,
    ...     diff_total=50,
    ...     threshold=0.1
    ... )
    >>> if result["passed"]:
    ...     print(f"验证通过，已激活批次：{result['active_batch_id']}")
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.ip_location_snapshot_service import IPLocationSnapshotService


class IPLocationValidationService:
    """
    IP 定位验证服务

    基于差异比例的批次验证和激活功能。
    """

    def __init__(self, db: Session):
        """
        初始化验证服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.snapshot_service = IPLocationSnapshotService(db)

    def validate_and_activate_batch(
        self,
        candidate_batch_id: str,
        sample_total: int,
        diff_total: int,
        threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        验证并激活候选批次

        根据采样总数和差异数量计算差异比例，如果差异比例低于阈值则激活候选批次。

        Args:
            candidate_batch_id: 候选批次 ID
            sample_total: 采样总数（用于计算差异比例的分母）
            diff_total: 差异数量（与旧批次比较发现的不同记录数）
            threshold: 差异比例阈值，默认 0.1（10%）

        Returns:
            验证结果字典，包含：
            - passed (bool): 是否通过验证
            - difference_ratio (float): 差异比例（0.0-1.0）
            - message (str): 结果描述信息
            - active_batch_id (Optional[str]): 当前激活的批次 ID

        Examples:
            >>> result = validator.validate_and_activate_batch(
            ...     candidate_batch_id="batch_001",
            ...     sample_total=1000,
            ...     diff_total=50,
            ...     threshold=0.1
            ... )
            >>> result["passed"]
            True
            >>> result["difference_ratio"]
            0.05
        """
        # 验证输入参数
        if sample_total <= 0:
            return {
                "passed": False,
                "difference_ratio": 1.0,
                "message": "sample_total must be positive",
                "active_batch_id": self.snapshot_service.get_active_batch_id()
            }

        # 计算差异比例
        ratio = diff_total / sample_total

        # 检查是否超过阈值
        if ratio > threshold:
            return {
                "passed": False,
                "difference_ratio": ratio,
                "message": f"difference ratio {ratio:.2%} exceeds threshold {threshold:.2%}",
                "active_batch_id": self.snapshot_service.get_active_batch_id()
            }

        # 验证通过，激活候选批次
        self.snapshot_service.activate_batch(candidate_batch_id)
        return {
            "passed": True,
            "difference_ratio": ratio,
            "message": f"batch activated (difference ratio: {ratio:.2%})",
            "active_batch_id": candidate_batch_id
        }

    def rollback(self, target_batch_id: str) -> Dict[str, Any]:
        """
        回滚到指定的历史批次

        Args:
            target_batch_id: 目标批次 ID（必须是已存在的历史批次）

        Returns:
            回滚结果字典，包含：
            - success (bool): 是否成功回滚
            - active_batch_id (Optional[str]): 回滚后激活的批次 ID
            - message (Optional[str]): 结果描述信息（如果失败）

        Examples:
            >>> result = validator.rollback(target_batch_id="batch_000")
            >>> if result["success"]:
            ...     print(f"已回滚到批次：{result['active_batch_id']}")
        """
        success = self.snapshot_service.rollback_to_batch(target_batch_id)
        result: Dict[str, Any] = {
            "success": success,
            "active_batch_id": self.snapshot_service.get_active_batch_id()
        }
        if not success:
            result["message"] = f"failed to rollback to batch {target_batch_id}"
        return result
