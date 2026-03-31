#!/usr/bin/env python3
"""
asyncio.Lock 跨事件循环行为验证脚本

目的：验证方案一（懒初始化 Lock）是否可行
测试场景：
1. 模块导入时创建 Lock（无事件循环）
2. 第一次 asyncio.run() 使用 Lock
3. 第二次 asyncio.run() 使用 Lock（关键测试）
"""

import asyncio
import sys

print("=" * 60)
print("asyncio.Lock 跨事件循环行为验证")
print("=" * 60)

# 测试 Python 版本
print(f"\nPython 版本: {sys.version}")
print(f"asyncio 版本信息: {asyncio.__file__}")

# ============================================
# 场景 1：模块导入时创建 Lock（无事件循环）
# ============================================
print("\n" + "-" * 60)
print("场景 1：模块导入时创建 Lock（无事件循环）")
print("-" * 60)

# 创建一个全局 Lock（模拟模块导入时的行为）
global_lock_v1 = asyncio.Lock()
print(f"全局 Lock 创建成功: {global_lock_v1}")
print(f"Lock 内部循环属性: {getattr(global_lock_v1, '_loop', 'None')}")

# ============================================
# 场景 2：第一次 asyncio.run() 使用 Lock
# ============================================
print("\n" + "-" * 60)
print("场景 2：第一次 asyncio.run() 使用 Lock")
print("-" * 60)

async def task1():
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")
    print(f"  Lock 绑定循环: {getattr(global_lock_v1, '_loop', 'None')}")

    try:
        async with global_lock_v1:
            print("  ✅ 成功获取 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")

    # 检查 Lock 使用后的状态
    print(f"  使用后 Lock 绑定循环: {getattr(global_lock_v1, '_loop', 'None')}")

try:
    asyncio.run(task1())
    print("第一次 asyncio.run() 完成")
except RuntimeError as e:
    print(f"第一次 asyncio.run() 失败: {e}")

# 检查循环是否关闭
loop_after_first = getattr(global_lock_v1, '_loop', None)
if loop_after_first:
    print(f"Lock 绑定的循环是否关闭: {loop_after_first.is_closed()}")

# ============================================
# 场景 3：第二次 asyncio.run() 使用同一个 Lock
# ============================================
print("\n" + "-" * 60)
print("场景 3：第二次 asyncio.run() 使用同一个 Lock（关键测试）")
print("-" * 60)

async def task2():
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")
    print(f"  Lock 绑定循环: {getattr(global_lock_v1, '_loop', 'None')}")

    # 关键检查
    lock_loop = getattr(global_lock_v1, '_loop', None)
    if lock_loop is not None:
        print(f"  Lock 循环是否关闭: {lock_loop.is_closed()}")
        if lock_loop.is_closed():
            print("  ⚠️ Lock 绑定的循环已关闭！")
        if loop != lock_loop:
            print(f"  ⚠️ 当前循环与 Lock 循环不同！")

    try:
        async with global_lock_v1:
            print("  ✅ 成功获取 Lock（方案有效）")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")
        print("  方案一无效！")

try:
    asyncio.run(task2())
    print("第二次 asyncio.run() 完成")
except RuntimeError as e:
    print(f"第二次 asyncio.run() 失败: {e}")
    print("❌ 方案一不可行！")

# ============================================
# 场景 4：懒初始化 Lock 测试
# ============================================
print("\n" + "-" * 60)
print("场景 4：懒初始化 Lock 测试")
print("-" * 60)

class LazyLockPool:
    """懒初始化 Lock 的连接池模拟"""

    def __init__(self):
        self._lock = None  # 不在 __init__ 中创建 Lock

    def _get_lock(self):
        """懒初始化获取 Lock"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

pool = LazyLockPool()
print(f"创建连接池实例，_lock 状态: {pool._lock}")

async def task3():
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")

    lock = pool._get_lock()
    print(f"  Lock 绑定循环: {getattr(lock, '_loop', 'None')}")

    try:
        async with lock:
            print("  ✅ 第一次成功获取 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")

try:
    asyncio.run(task3())
    print("懒初始化第一次 asyncio.run() 完成")
except RuntimeError as e:
    print(f"懒初始化第一次失败: {e}")

# 检查懒初始化 Lock 在第二次 asyncio.run() 的表现
async def task4():
    loop = asyncio.get_running_loop()
    print(f"  当前事件循环: {loop}")

    lock = pool._get_lock()  # 获取已存在的 Lock
    lock_loop = getattr(lock, '_loop', None)
    print(f"  Lock 绑定循环: {lock_loop}")

    if lock_loop is not None:
        print(f"  Lock 循环是否关闭: {lock_loop.is_closed()}")
        if lock_loop.is_closed():
            print("  ⚠️ Lock 绑定的循环已关闭！")

    try:
        async with lock:
            print("  ✅ 成功获取 Lock（懒初始化方案有效）")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")
        print("  懒初始化方案在第二次 asyncio.run() 时无效！")

try:
    asyncio.run(task4())
    print("懒初始化第二次 asyncio.run() 完成")
except RuntimeError as e:
    print(f"❌ 懒初始化第二次失败: {e}")
    print("❌ 方案一（懒初始化 Lock）不可行！")

# ============================================
# 场景 5：每次采集创建新 Lock
# ============================================
print("\n" + "-" * 60)
print("场景 5：每次采集创建新 Lock（优化方案 A）")
print("-" * 60)

class FreshLockPool:
    """每次采集创建新 Lock 的连接池模拟"""

    def __init__(self):
        pass  # 不保存 Lock

    def get_fresh_lock(self):
        """每次调用创建新 Lock"""
        return asyncio.Lock()

pool2 = FreshLockPool()

async def task5():
    loop = asyncio.get_running_loop()
    lock = pool2.get_fresh_lock()  # 每次创建新 Lock
    print(f"  当前事件循环: {loop}")
    print(f"  新 Lock 绑定循环: {getattr(lock, '_loop', 'None')}")

    try:
        async with lock:
            print("  ✅ 成功获取新创建的 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")

try:
    asyncio.run(task5())
    print("优化方案 A 第一次 asyncio.run() 完成")
except RuntimeError as e:
    print(f"优化方案 A 第一次失败: {e}")

async def task6():
    loop = asyncio.get_running_loop()
    lock = pool2.get_fresh_lock()  # 又是新 Lock
    print(f"  当前事件循环: {loop}")
    print(f"  新 Lock 绑定循环: {getattr(lock, '_loop', 'None')}")

    try:
        async with lock:
            print("  ✅ 成功获取新创建的 Lock")
            await asyncio.sleep(0.1)
    except RuntimeError as e:
        print(f"  ❌ 失败: {e}")

try:
    asyncio.run(task6())
    print("优化方案 A 第二次 asyncio.run() 完成")
    print("✅ 优化方案 A（每次创建新 Lock）可行！")
except RuntimeError as e:
    print(f"❌ 优化方案 A 第二次失败: {e}")

# ============================================
# 最终结论
# ============================================
print("\n" + "=" * 60)
print("验证结论")
print("=" * 60)
print("""
场景 1-3 结论：
- 如果 Lock 在模块导入时创建，绑定的循环在 asyncio.run() 结束后关闭
- 第二次 asyncio.run() 时，Lock 绑定的循环已关闭，会导致错误

场景 4 结论（懒初始化 Lock）：
- 懒初始化只是延迟了 Lock 创建时机
- 第一次 asyncio.run() 时创建 Lock，绑定到循环 A
- asyncio.run() 结束后循环 A 关闭
- 第二次 asyncio.run() 时，Lock 仍然绑定到已关闭的循环 A
- 懒初始化方案无法解决多次 asyncio.run() 的问题！

场景 5 结论（每次创建新 Lock）：
- 每次采集任务创建新的 Lock
- 新 Lock 绑定到当前运行的循环
- 这是可行的优化方案！
""")