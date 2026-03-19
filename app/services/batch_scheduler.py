"""
分批调度器
用于避免同时访问大量网络设备造成压力
"""
import asyncio
import random
from typing import List, Any, Callable, Awaitable, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BatchScheduler:
    """通用分批调度器"""

    def __init__(
        self,
        batch_size: int = 20,
        batch_interval: float = 120.0,
        max_concurrent: int = 10
    ):
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._is_running = False
        self._cancel_requested = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def cancel(self):
        """请求取消当前任务"""
        self._cancel_requested = True

    async def run_tasks(
        self,
        items: List[Any],
        task_func: Callable[[Any], Awaitable[Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[List[Any], List[Exception]]:
        """
        分批执行任务

        Args:
            items: 待处理的项目列表
            task_func: 对每个 item 执行的异步函数
            progress_callback: 进度回调 (completed, total)

        Returns:
            (成功结果列表, 失败异常列表)
        """
        if not items:
            return [], []

        self._is_running = True
        self._cancel_requested = False

        total = len(items)
        completed = 0
        results = []
        errors = []

        # 分批
        batches = [items[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        logger.info(f"分批执行: {total} 个项目分为 {len(batches)} 批，每批 {self.batch_size} 个")

        try:
            for batch_idx, batch in enumerate(batches):
                if self._cancel_requested:
                    logger.info("任务被取消")
                    break

                logger.info(f"执行第 {batch_idx + 1}/{len(batches)} 批")

                # 并发执行当前批次
                batch_tasks = []
                for item in batch:
                    task = self._wrap_task(item, task_func)
                    batch_tasks.append(task)

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # 处理结果
                for result in batch_results:
                    if isinstance(result, Exception):
                        errors.append(result)
                    else:
                        results.append(result)
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, total)

                # 不是最后一批的话，等待一段时间
                if batch_idx < len(batches) - 1 and not self._cancel_requested:
                    logger.info(f"等待 {self.batch_interval} 秒后执行下一批")
                    await asyncio.sleep(self.batch_interval)

        finally:
            self._is_running = False

        logger.info(f"分批执行完成: {len(results)} 成功, {len(errors)} 失败")
        return results, errors

    async def _wrap_task(self, item: Any, task_func: Callable[[Any], Awaitable[Any]]) -> Any:
        """包装单个任务，加入信号量控制"""
        async with self.semaphore:
            return await task_func(item)


def randomize_order(items: List[Any]) -> List[Any]:
    """随机打乱顺序，避免每次按相同顺序执行"""
    shuffled = items.copy()
    random.shuffle(shuffled)
    return shuffled


def is_silent_hour(current_hour: int, silent_hours: List[int]) -> bool:
    """检查是否是静默时段"""
    return current_hour in silent_hours
