#!/usr/bin/env python3
"""
asyncio.create_task() 跨事件循环行为验证脚本

目的：验证 SSH 连接池中 asyncio.create_task() 在 __init__ 中的问题
"""

import asyncio
import sys

print("=" * 60)
print("asyncio.create_task() 跨事件循环行为验证")
print("=" * 60)

print(f"\nPython 版本: {sys.version}")

# ============================================
# 场景 1：在无事件循环时调用 create_task
# ============================================
print("\n" + "-" * 60)
print("场景 1：在无事件循环时调用 asyncio.create_task()")
print("-" * 60)

async def periodic_cleanup():
    """模拟清理任务"""
    print("  清理任务开始运行...")
    await asyncio.sleep(0.1)
    print("  清理任务完成")

try:
    # 在无事件循环时创建 task（这是 SSH 连接池的问题）
    task = asyncio.create_task(periodic_cleanup())
    print(f"创建成功: {task}")
except RuntimeError as e:
    print(f"❌ 失败: {e}")
    print("asyncio.create_task() 在无事件循环时会失败！")

# ============================================
# 场景 2：在有事件循环时创建 task
# ============================================
print("\n" + "-" * 60)
print("场景 2：在有事件循环时创建 asyncio.create_task()")
print("-" * 60)

async def main_with_task():
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")

    task = asyncio.create_task(periodic_cleanup())
    print(f"  创建成功: {task}")

    # 等待任务完成
    await task

try:
    asyncio.run(main_with_task())
    print("✅ 在有事件循环时创建 task 成功")
except Exception as e:
    print(f"❌ 失败: {e}")

# ============================================
# 场景 3：Task 在事件循环关闭后的状态
# ============================================
print("\n" + "-" * 60)
print("场景 3：Task 创建后事件循环关闭的情况")
print("-" * 60)

class PoolWithTask:
    """模拟 SSH 连接池，在 __init__ 中创建 task"""

    def __init__(self):
        print("  初始化连接池...")
        self._cleanup_task = None
        try:
            # 模拟 SSH 连接池第 72 行的行为
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            print(f"  创建 task 成功: {self._cleanup_task}")
        except RuntimeError as e:
            print(f"  创建 task 失败: {e}")
            self._cleanup_task = None

    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(60)
                print("  执行清理...")
            except asyncio.CancelledError:
                print("  清理任务被取消")
                break

print("创建连接池实例（无事件循环）:")
try:
    pool1 = PoolWithTask()
    print(f"pool1._cleanup_task: {pool1._cleanup_task}")
except Exception as e:
    print(f"创建失败: {e}")

# ============================================
# 场景 4：完整模拟 SSH 连接池问题
# ============================================
print("\n" + "-" * 60)
print("场景 4：完整模拟 SSH 连接池的使用场景")
print("-" * 60)

class SSHConnectionPoolSimulated:
    """完整模拟 SSH 连接池"""

    def __init__(self):
        # 模拟第 70 行：Lock 创建
        self._lock = None
        self._lock_initialized = False

        # 模拟第 72 行：create_task
        self._cleanup_task = None
        try:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # 无事件循环时失败
            pass

        print(f"  初始化完成:")
        print(f"    _lock: {self._lock}")
        print(f"    _cleanup_task: {self._cleanup_task}")

    def _get_lock(self):
        """懒初始化获取 Lock"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _periodic_cleanup(self):
        """定期清理"""
        while True:
            await asyncio.sleep(60)
            print("  清理...")

    async def _ensure_cleanup_task(self):
        """确保清理任务启动"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            print("  清理任务已创建")

    async def get_connection(self, device_id: int):
        """获取连接"""
        await self._ensure_cleanup_task()

        lock = self._get_lock()
        async with lock:
            print(f"  获取设备 {device_id} 的连接")
            await asyncio.sleep(0.1)
            return f"connection_{device_id}"

# 在模块导入阶段（无事件循环）创建连接池
print("模拟模块导入阶段创建全局连接池:")
global_pool = SSHConnectionPoolSimulated()

# 模拟 arp_mac_scheduler 的 _run_async 调用
async def collection_task_1():
    print("\n第一次采集任务开始:")
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")

    lock = global_pool._get_lock()
    print(f"  Lock: {lock}")

    try:
        # 使用 Lock
        async with lock:
            print("  ✅ 成功获取 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ Lock 失败: {e}")

    # 尝试获取连接
    try:
        conn = await global_pool.get_connection(1)
        print(f"  ✅ 获取连接成功: {conn}")
    except Exception as e:
        print(f"  ❌ 获取连接失败: {e}")

async def collection_task_2():
    print("\n第二次采集任务开始:")
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")

    lock = global_pool._get_lock()
    print(f"  Lock: {lock}")

    try:
        async with lock:
            print("  ✅ 成功获取 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ Lock 失败: {e}")

    try:
        conn = await global_pool.get_connection(2)
        print(f"  ✅ 获取连接成功: {conn}")
    except Exception as e:
        print(f"  ❌ 获取连接失败: {e}")

print("\n模拟第一次 asyncio.run():")
try:
    asyncio.run(collection_task_1())
    print("✅ 第一次采集任务完成")
except Exception as e:
    print(f"❌ 第一次采集失败: {e}")

print("\n模拟第二次 asyncio.run():")
try:
    asyncio.run(collection_task_2())
    print("✅ 第二次采集任务完成")
except Exception as e:
    print(f"❌ 第二次采集失败: {e}")

# ============================================
# 最终结论
# ============================================
print("\n" + "=" * 60)
print("验证结论")
print("=" * 60)
print("""
关键发现：

1. asyncio.Lock 在 Python 3.12 中的行为：
   - 创建时不绑定到特定事件循环（_loop = None）
   - 可以在不同的事件循环中使用
   - 懒初始化 Lock 在 Python 3.12 中可行！

2. asyncio.create_task() 的问题：
   - 在无事件循环时会失败（RuntimeError: no running event loop）
   - SSH 连接池第 72 行的问题需要修复
   - 需要在事件循环内创建清理任务

3. 方案一（懒初始化 Lock）的可行性：
   - 在 Python 3.12 中，Lock 不严格绑定到事件循环
   - 但 create_task() 在 __init__ 中会失败
   - 需要同时处理 Lock 和 create_task 的问题

修复建议：
- 使用懒初始化 Lock：可行
- 使用懒初始化清理任务：必须在事件循环内创建
- 或使用 threading.Timer 替代 asyncio.create_task
""")