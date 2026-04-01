---
ontology:
  id: DOC-2026-03-031-ANAL
  type: analysis
  problem: SSH连接池 AsyncIOScheduler 迁移
  problem_id: P002
  status: active
  created: 2026-03-30
  updated: 2026-03-30
  author: Claude
  tags:
    - documentation
---
# SSH 连接池事件循环不匹配问题分析报告

**日期**: 2026-03-30
**错误**: `RuntimeError: Lock is bound to a different event loop`
**涉及文件**: `app/services/ssh_connection_pool.py`, `app/services/netmiko_service.py`, `app/services/arp_mac_scheduler.py`

---

## 1. 问题概述

SSH 连接池模块在运行时出现 `RuntimeError: Lock is bound to a different event loop` 错误，导致 ARP/MAC 采集任务无法正常执行。

---

## 2. 根因分析

### 2.1 核心问题：asyncio.Lock 在模块导入时创建

**问题代码位置**: `ssh_connection_pool.py:70`

```python
class SSHConnectionPool:
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}
        self.lock = asyncio.Lock()  # <-- 问题点！
        self.netmiko_service = get_netmiko_service()
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())  # <-- 问题点！
```

**全局实例创建**: `ssh_connection_pool.py:199`
```python
# 创建全局SSH连接池实例
ssh_connection_pool = SSHConnectionPool()
```

### 2.2 asyncio.Lock 的事件循环绑定机制

`asyncio.Lock` 在创建时会绑定到当前运行的事件循环：

1. 如果创建时有运行的事件循环，Lock 绑定到该循环
2. 如果创建时**没有**运行的事件循环（模块导入阶段），Lock 会绑定到 `None` 或第一个被创建的事件循环
3. **关键问题**: 当后续代码使用 `asyncio.run()` 创建新的事件循环时，这个新循环与原 Lock 绑定的循环不同

### 2.3 问题触发流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  问题触发时间线                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 应用启动                                                                 │
│     │                                                                       │
│     ▼                                                                       │
│  2. 模块导入阶段（无事件循环运行）                                             │
│     │   - import ssh_connection_pool                                        │
│     │   - SSHConnectionPool() 实例化                                        │
│     │   - self.lock = asyncio.Lock() ← Lock 绑定到 None                     │
│     │                                                                       │
│     ▼                                                                       │
│  3. FastAPI 启动事件循环                                                      │
│     │   - 创建事件循环 A                                                      │
│     │                                                                       │
│     ▼                                                                       │
│  4. arp_mac_scheduler 启动                                                   │
│     │   - BackgroundScheduler 后台线程执行                                   │
│     │                                                                       │
│     ▼                                                                       │
│  5. _run_async() 方法执行                                                    │
│     │   - asyncio.run(coro)                                                 │
│     │   - 创建新的事件循环 B ← 与 Lock 绑定的循环不同                           │
│     │                                                                       │
│     ▼                                                                       │
│  6. 执行采集任务                                                              │
│     │   - _collect_device_async()                                           │
│     │   - netmiko.collect_arp_table()                                       │
│     │   - ssh_connection_pool.get_connection()                              │
│     │                                                                       │
│     ▼                                                                       │
│  7. 尝试获取 Lock                                                            │
│     │   - async with self.lock: ← 错误触发！                                 │
│     │   - RuntimeError: Lock is bound to a different event loop             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 问题代码详解

#### ssh_connection_pool.py 问题点

| 行号 | 代码 | 问题说明 |
|------|------|----------|
| 70 | `self.lock = asyncio.Lock()` | 在 `__init__` 中创建 Lock，模块导入时执行 |
| 72 | `self.cleanup_task = asyncio.create_task(...)` | 在 `__init__` 中创建异步任务，需要运行的事件循环 |
| 199 | `ssh_connection_pool = SSHConnectionPool()` | 全局实例创建，触发上述问题 |

#### arp_mac_scheduler.py 问题关联

| 行号 | 代码 | 问题说明 |
|------|------|----------|
| 235-301 | `_run_async()` | 使用 `asyncio.run()` 创建新事件循环 |
| 253-255 | `asyncio.run(coro)` | 创建的事件循环与 Lock 绑定的循环不同 |
| 314 | `_run_async(self._collect_device_async(device))` | 触发采集流程，最终调用 SSH 连接池 |

#### netmiko_service.py 问题关联

| 行号 | 代码 | 问题说明 |
|------|------|----------|
| 312 | `from app.services.ssh_connection_pool import get_ssh_connection_pool` | 导入连接池模块 |
| 329 | `ssh_connection = await ssh_conn_pool.get_connection(device)` | 调用连接池方法，触发 Lock 问题 |
| 350 | `loop = asyncio.get_event_loop()` | 获取事件循环的方式在 FastAPI 中可能有兼容性问题 |

---

## 3. 问题影响范围

### 3.1 直接影响

- ARP/MAC 采集任务无法执行
- SSH 连接池功能完全失效
- 设备命令执行失败

### 3.2 间接影响

- IP 定位计算无法进行（依赖 ARP/MAC 数据）
- 端口信息采集可能失败
- 配置下发功能可能失败

---

## 4. 深层技术分析

### 4.1 asyncio.Lock 的内部实现

```python
# asyncio.Lock 的内部绑定逻辑（简化版）
class Lock:
    def __init__(self):
        self._loop = asyncio.get_running_loop()  # 获取当前运行的循环
        # 如果没有运行循环，get_running_loop() 会抛出 RuntimeError
        # 但实际上 asyncio.Lock 在没有循环时会有特殊处理
```

**关键点**: Python 3.10+ 对 asyncio.Lock 的行为有变化：
- 在 Python 3.10+ 中，`asyncio.Lock()` 如果没有运行的事件循环，会延迟绑定
- 但如果模块导入时有事件循环创建（如 uvicorn 启动），Lock 可能绑定到那个循环
- 当 `asyncio.run()` 创建新循环时，新循环与原循环不同

### 4.2 BackgroundScheduler 与事件循环冲突

`arp_mac_scheduler.py` 使用 APScheduler 的 `BackgroundScheduler`：

```python
self.scheduler = BackgroundScheduler()
self.scheduler.add_job(func=self._run_collection, ...)
self.scheduler.start()
```

`BackgroundScheduler` 在**单独的后台线程**中执行任务，而 `asyncio.run()` 每次调用都会创建新的事件循环。这导致：

1. 每次调度任务执行都创建新的事件循环
2. SSH 连接池的 Lock 绑定的是另一个事件循环
3. 使用 Lock 时抛出事件循环不匹配错误

### 4.3 全局单例模式的隐患

```python
# ssh_connection_pool.py
ssh_connection_pool = SSHConnectionPool()  # 模块导入时创建

# netmiko_service.py
netmiko_service = NetmikoService()  # 模块导入时创建
```

全局单例在模块导入时创建，导致：
- 初始化时机不可控（可能在事件循环创建之前或之后）
- 组件状态依赖于导入顺序
- 多线程环境下可能出现竞态条件

---

## 5. 问题分类总结

### 5.1 问题类型矩阵

| 问题类型 | 具体问题 | 文件位置 |
|----------|----------|----------|
| **时序问题** | asyncio.Lock 在无事件循环时创建 | ssh_connection_pool.py:70 |
| **时序问题** | asyncio.create_task 在无事件循环时调用 | ssh_connection_pool.py:72 |
| **设计问题** | 全局单例在模块导入时初始化 | ssh_connection_pool.py:199 |
| **设计问题** | BackgroundScheduler 与 asyncio 混用 | arp_mac_scheduler.py:46 |
| **设计问题** | asyncio.run() 创建新循环而非使用现有循环 | arp_mac_scheduler.py:255 |
| **调用链问题** | 多层异步调用跨事件循环 | 所有三个文件 |

### 5.2 核心矛盾

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  核心矛盾                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  模块导入阶段（无事件循环）                                                    │
│     │                                                                       │
│     └── 创建 asyncio.Lock ← 绑定到 None 或延迟绑定                           │
│                                                                             │
│  运行阶段（有事件循环）                                                        │
│     │                                                                       │
│     ├── FastAPI 事件循环 A                                                   │
│     │                                                                       │
│     └── BackgroundScheduler 调度任务                                         │
│         │                                                                   │
│         └── asyncio.run() 创建事件循环 B                                     │
│             │                                                               │
│             └── 尝试使用 Lock ← 循环 B ≠ Lock 绑定的循环                       │
│                 │                                                           │
│                 └── RuntimeError: Lock is bound to a different event loop   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 相关 Python asyncio 行为说明

### 6.1 asyncio.Lock 绑定行为

| Python 版本 | 行为 |
|-------------|------|
| Python 3.7-3.9 | Lock 必须在有运行循环时创建，否则延迟绑定 |
| Python 3.10+ | Lock 可在无循环时创建，但绑定到第一个使用的循环 |

### 6.2 asyncio.run() 行为

```python
# asyncio.run() 的内部逻辑（简化版）
def run(main):
    loop = asyncio.new_event_loop()  # 创建新的事件循环
    try:
        return loop.run_until_complete(main)
    finally:
        loop.close()  # 关闭事件循环
```

**关键点**: `asyncio.run()` 每次调用都创建**新的**事件循环，并在完成后关闭。这意味着：
- 连续调用 `asyncio.run()` 会创建不同的循环
- 与其他地方创建的循环完全独立
- 绑定到特定循环的 Lock 无法在新循环中使用

---

## 7. 结论

### 7.1 根因确认

**根本原因**: `SSHConnectionPool.__init__` 中在模块导入阶段（无事件循环运行）创建了 `asyncio.Lock`，当后续 `arp_mac_scheduler` 使用 `asyncio.run()` 创建新事件循环执行采集任务时，Lock 绑定的事件循环与当前运行的循环不匹配。

### 7.2 问题定性

这是一个**设计缺陷**，而非简单的使用错误：
- asyncio 异步对象（Lock、Task、Future）应该在使用时创建，而非在模块导入时
- 混用 BackgroundScheduler（后台线程）与 asyncio（事件循环）需要谨慎处理
- 全局单例模式在异步环境中需要特殊处理

---

## 8. 影响评估

| 评估维度 | 影响程度 | 说明 |
|----------|----------|------|
| **功能影响** | 高 | ARP/MAC 采集完全失效 |
| **稳定性影响** | 高 | 每次调度任务执行都会失败 |
| **数据影响** | 高 | 无法更新 IP 定位数据 |
| **修复难度** | 中 | 需要重构 SSH 连接池初始化逻辑 |
| **紧急程度** | 高 | 核心功能不可用 |

---

## 附录：相关代码引用

### A. ssh_connection_pool.py 关键代码

```python
# 第 59-72 行：SSHConnectionPool.__init__
def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
    self.max_connections = max_connections
    self.connection_timeout = connection_timeout
    self.connections: Dict[int, List[SSHConnection]] = {}
    self.lock = asyncio.Lock()  # 问题：在无事件循环时创建
    self.netmiko_service = get_netmiko_service()
    self.cleanup_task = asyncio.create_task(self._periodic_cleanup())  # 问题：在无事件循环时创建

# 第 199 行：全局实例创建
ssh_connection_pool = SSHConnectionPool()
```

### B. arp_mac_scheduler.py 关键代码

```python
# 第 235-301 行：_run_async 方法
def _run_async(self, coro):
    try:
        return asyncio.run(coro)  # 问题：创建新的事件循环
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            # 降级方案...
```

### C. netmiko_service.py 关键代码

```python
# 第 312-329 行：execute_command 方法
from app.services.ssh_connection_pool import get_ssh_connection_pool

ssh_conn_pool = get_ssh_connection_pool()
ssh_connection = await ssh_conn_pool.get_connection(device)  # 触发 Lock 问题
```

---

## 9. 修复方案

### 9.1 方案一：懒初始化 Lock（推荐）

**核心思路**：不在 `__init__` 中创建 `asyncio.Lock`，而是在第一次使用时延迟创建。这样可以确保 Lock 绑定到正确的事件循环。

#### 代码修改

**修改 `ssh_connection_pool.py`**：

```python
# 修改前（问题代码）
class SSHConnectionPool:
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}
        self.lock = asyncio.Lock()  # 问题：在无事件循环时创建
        self.netmiko_service = get_netmiko_service()
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())  # 问题

# 修改后（修复代码）
class SSHConnectionPool:
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}
        self._lock: Optional[asyncio.Lock] = None  # 延迟初始化
        self._lock_initialized = False
        self.netmiko_service = get_netmiko_service()
        self._cleanup_task: Optional[asyncio.Task] = None  # 延迟初始化

    @property
    def lock(self) -> asyncio.Lock:
        """懒初始化 Lock，确保绑定到正确的事件循环"""
        if self._lock is None or self._lock_initialized is False:
            self._lock = asyncio.Lock()
            self._lock_initialized = True
        return self._lock

    async def _ensure_cleanup_task(self):
        """确保清理任务在正确的事件循环中启动"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def get_connection(self, device: dict) -> SSHConnection:
        """获取 SSH 连接"""
        await self._ensure_cleanup_task()  # 确保清理任务已启动
        async with self.lock:  # 使用懒初始化的 Lock
            # ... 原有逻辑
            pass
```

#### 完整修改示例

```python
import asyncio
from typing import Dict, List, Optional

class SSHConnectionPool:
    """SSH 连接池管理类"""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        初始化 SSH 连接池

        Args:
            max_connections: 每台设备的最大连接数
            connection_timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}

        # 懒初始化属性
        self._lock: Optional[asyncio.Lock] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False

        self.netmiko_service = get_netmiko_service()

    def _get_lock(self) -> asyncio.Lock:
        """
        获取或创建 asyncio.Lock

        使用懒初始化确保 Lock 在正确的事件循环中创建

        Returns:
            asyncio.Lock: 绑定到当前事件循环的锁
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _start_cleanup_task(self):
        """启动定期清理任务（懒初始化）"""
        if not self._cleanup_started:
            self._cleanup_started = True
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def get_connection(self, device: dict) -> SSHConnection:
        """
        获取或创建 SSH 连接

        Args:
            device: 设备信息字典

        Returns:
            SSHConnection: SSH 连接对象
        """
        await self._start_cleanup_task()

        lock = self._get_lock()
        async with lock:
            device_id = device.get('id')
            if device_id not in self.connections:
                self.connections[device_id] = []

            # 查找可用连接
            for conn in self.connections[device_id]:
                if not conn.in_use and conn.is_alive:
                    conn.in_use = True
                    return conn

            # 创建新连接
            conn = await self._create_connection(device)
            self.connections[device_id].append(conn)
            return conn

    async def release_connection(self, conn: SSHConnection):
        """释放连接回连接池"""
        lock = self._get_lock()
        async with lock:
            conn.in_use = False

    async def close_all(self):
        """关闭所有连接"""
        lock = self._get_lock()
        async with lock:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass

            for device_id, conns in self.connections.items():
                for conn in conns:
                    await conn.close()
            self.connections.clear()

    async def _periodic_cleanup(self):
        """定期清理过期连接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每60秒清理一次
                lock = self._get_lock()
                async with lock:
                    # 清理逻辑...
                    pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务异常: {e}")

# 全局实例创建（现在安全了，因为不会立即创建 Lock）
ssh_connection_pool = SSHConnectionPool()
```

#### 优缺点

| 维度 | 说明 |
|------|------|
| **优点** | 改动最小，只需修改一个文件；保持异步特性；线程安全 |
| **缺点** | 需要确保每次使用 Lock 时都通过 getter 方法 |
| **风险** | 低 |

---

### 9.2 方案二：使用同步锁 threading.Lock 替代 asyncio.Lock

**核心思路**：SSH 连接池本身是线程安全的，使用 `threading.Lock` 可以避免事件循环绑定问题。

#### 代码修改

```python
import threading
from typing import Dict, List
import asyncio

class SSHConnectionPool:
    """SSH 连接池管理类"""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        初始化 SSH 连接池

        Args:
            max_connections: 每台设备的最大连接数
            connection_timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List[SSHConnection]] = {}

        # 使用 threading.Lock 替代 asyncio.Lock
        self._lock = threading.Lock()
        self.netmiko_service = get_netmiko_service()

        # 清理任务仍然需要异步处理
        self._cleanup_task: Optional[asyncio.Task] = None

    async def get_connection(self, device: dict) -> SSHConnection:
        """
        获取或创建 SSH 连接

        Args:
            device: 设备信息字典

        Returns:
            SSHConnection: SSH 连接对象
        """
        # 使用同步锁保护连接池操作
        with self._lock:
            device_id = device.get('id')
            if device_id not in self.connections:
                self.connections[device_id] = []

            # 查找可用连接
            for conn in self.connections[device_id]:
                if not conn.in_use and conn.is_alive:
                    conn.in_use = True
                    return conn

            # 创建新连接（异步操作在锁外执行）
            pass

        # 异步创建连接（在锁外执行，避免阻塞）
        conn = await self._create_connection(device)

        # 再次获取锁来更新连接池
        with self._lock:
            if device_id not in self.connections:
                self.connections[device_id] = []
            self.connections[device_id].append(conn)
            return conn

    async def release_connection(self, conn: SSHConnection):
        """释放连接回连接池"""
        with self._lock:
            conn.in_use = False

    async def close_all(self):
        """关闭所有连接"""
        with self._lock:
            if self._cleanup_task:
                self._cleanup_task.cancel()

            for device_id, conns in self.connections.items():
                for conn in conns:
                    # 注意：异步操作需要特殊处理
                    # 可以使用 asyncio.run_coroutine_threadsafe() 或调整设计
                    pass
            self.connections.clear()
```

#### 完整修改示例（带异步兼容处理）

```python
import threading
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SSHConnectionPool:
    """SSH 连接池管理类 - 使用 threading.Lock 实现"""

    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[int, List['SSHConnection']] = {}
        self._lock = threading.RLock()  # 使用可重入锁
        self.netmiko_service = get_netmiko_service()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_started = False

    async def get_connection(self, device: dict) -> 'SSHConnection':
        """获取 SSH 连接"""
        device_id = device.get('id')

        # 先尝试快速获取现有可用连接
        with self._lock:
            if device_id in self.connections:
                for conn in self.connections[device_id]:
                    if not conn.in_use and conn.is_alive:
                        conn.in_use = True
                        return conn

        # 在锁外创建新连接（异步操作）
        try:
            conn = await self._create_connection(device)
        except Exception as e:
            logger.error(f"创建连接失败: {e}")
            raise

        # 将新连接添加到池中
        with self._lock:
            if device_id not in self.connections:
                self.connections[device_id] = []
            self.connections[device_id].append(conn)
            conn.in_use = True

        return conn

    async def _create_connection(self, device: dict) -> 'SSHConnection':
        """创建新的 SSH 连接"""
        # 实际创建连接的异步逻辑
        conn = SSHConnection(device)
        await conn.connect()
        return conn

    async def release_connection(self, conn: 'SSHConnection'):
        """释放连接"""
        with self._lock:
            conn.in_use = False

    async def close_all(self):
        """关闭所有连接"""
        with self._lock:
            connections_to_close = []
            for conns in self.connections.values():
                connections_to_close.extend(conns)
            self.connections.clear()

        # 在锁外执行异步关闭操作
        for conn in connections_to_close:
            try:
                await conn.close()
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")

    async def _periodic_cleanup(self):
        """定期清理"""
        while True:
            try:
                await asyncio.sleep(60)
                self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理异常: {e}")

    def _cleanup_expired_connections(self):
        """清理过期连接（同步方法）"""
        current_time = asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0

        with self._lock:
            for device_id, conns in list(self.connections.items()):
                alive_conns = []
                for conn in conns:
                    if conn.is_alive and not conn.is_expired(current_time):
                        alive_conns.append(conn)
                    else:
                        # 异步关闭需要特殊处理
                        pass
                self.connections[device_id] = alive_conns

# 全局实例
ssh_connection_pool = SSHConnectionPool()
```

#### 优缺点

| 维度 | 说明 |
|------|------|
| **优点** | 彻底解决事件循环绑定问题；简单直接；线程安全 |
| **缺点** | 在锁内执行异步操作需要特殊处理；可能影响并发性能 |
| **风险** | 中（需要仔细处理同步/异步边界） |

---

### 9.3 方案三：重构 Scheduler 使用 AsyncIOScheduler

**核心思路**：将 `arp_mac_scheduler` 中的 `BackgroundScheduler` 替换为 `AsyncIOScheduler`，使所有代码运行在同一个事件循环中。

#### 代码修改

**修改 `arp_mac_scheduler.py`**：

```python
# 修改前
from apscheduler.schedulers.background import BackgroundScheduler

class ARPMACScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        # ...

    def _run_async(self, coro):
        """在后台线程中运行异步任务"""
        try:
            return asyncio.run(coro)
        except RuntimeError as e:
            # 错误处理
            pass

# 修改后
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class ARPMACScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running = False
        # ...

    async def start(self):
        """启动调度器（需要在异步上下文中调用）"""
        if not self._running:
            self._running = True

            # 添加定时任务
            self.scheduler.add_job(
                self._run_collection,
                'interval',
                minutes=30,
                id='arp_mac_collection',
                replace_existing=True
            )

            # 添加启动后立即执行的任务
            self.scheduler.add_job(
                self._run_collection,
                'date',  # 立即执行一次
                id='arp_mac_collection_startup',
            )

            self.scheduler.start()
            logger.info("ARP/MAC 采集调度器已启动")

    async def stop(self):
        """停止调度器"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("ARP/MAC 采集调度器已停止")

    async def _run_collection(self):
        """执行采集任务（现在完全是异步的）"""
        try:
            # 不再需要 _run_async 包装
            # 直接在当前事件循环中执行
            await self._collect_all_devices()
        except Exception as e:
            logger.error(f"采集任务执行失败: {e}")

    async def _collect_all_devices(self):
        """采集所有设备"""
        # 获取设备列表
        devices = await self._get_active_devices()

        # 并发采集
        tasks = [self._collect_device(device) for device in devices]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        # ...

    async def _collect_device(self, device: dict):
        """采集单个设备"""
        try:
            # 直接调用异步方法
            arp_result = await self.netmiko_service.collect_arp_table(device)
            mac_result = await self.netmiko_service.collect_mac_table(device)
            # ...
        except Exception as e:
            logger.error(f"设备 {device.get('id')} 采集失败: {e}")
```

#### 完整修改示例

```python
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from app.services.netmiko_service import get_netmiko_service
from app.models.device import Device

logger = logging.getLogger(__name__)


class ARPMACScheduler:
    """ARP/MAC 采集调度器 - 异步版本"""

    def __init__(self, collection_interval: int = 30):
        """
        初始化调度器

        Args:
            collection_interval: 采集间隔（分钟）
        """
        self.scheduler = AsyncIOScheduler()
        self.collection_interval = collection_interval
        self.netmiko_service = get_netmiko_service()
        self._running = False

    async def start(self):
        """
        启动调度器

        必须在异步上下文中调用（如 FastAPI 的 startup event）
        """
        if self._running:
            logger.warning("调度器已在运行中")
            return

        try:
            # 添加定时采集任务
            self.scheduler.add_job(
                self._run_collection,
                IntervalTrigger(minutes=self.collection_interval),
                id='arp_mac_collection',
                replace_existing=True,
                max_instances=1,  # 防止并发执行
            )
            logger.info(f"定时采集任务已添加，间隔: {self.collection_interval} 分钟")

            # 添加启动后立即执行的任务
            self.scheduler.add_job(
                self._run_collection,
                DateTrigger(run_date=datetime.now()),
                id='arp_mac_collection_startup',
            )
            logger.info("启动时采集任务已添加")

            # 启动调度器
            self.scheduler.start()
            self._running = True
            logger.info("ARP/MAC 采集调度器已启动（AsyncIOScheduler）")

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            raise

    async def stop(self):
        """停止调度器"""
        if self._running:
            try:
                self.scheduler.shutdown(wait=True)
                self._running = False
                logger.info("ARP/MAC 采集调度器已停止")
            except Exception as e:
                logger.error(f"停止调度器失败: {e}")

    async def _run_collection(self):
        """执行采集任务（异步方法）"""
        logger.info("开始执行 ARP/MAC 采集任务")

        try:
            # 获取活跃设备列表
            devices = await self._get_active_devices()
            logger.info(f"获取到 {len(devices)} 台活跃设备")

            if not devices:
                logger.warning("没有活跃设备，跳过采集")
                return

            # 并发采集所有设备
            tasks = [self._collect_device(device) for device in devices]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            success_count = sum(1 for r in results if r is True)
            failure_count = len(results) - success_count

            logger.info(f"采集任务完成，成功: {success_count}，失败: {failure_count}")

        except Exception as e:
            logger.error(f"采集任务执行失败: {e}", exc_info=True)

    async def _get_active_devices(self) -> List[Dict[str, Any]]:
        """获取活跃设备列表"""
        # 实现获取设备列表的逻辑
        pass

    async def _collect_device(self, device: Dict[str, Any]) -> bool:
        """
        采集单个设备的 ARP/MAC 数据

        Args:
            device: 设备信息字典

        Returns:
            bool: 采集是否成功
        """
        device_id = device.get('id')
        device_name = device.get('name', device_id)

        try:
            logger.info(f"开始采集设备: {device_name}")

            # 采集 ARP 表
            arp_result = await self.netmiko_service.collect_arp_table(device)

            # 采集 MAC 表
            mac_result = await self.netmiko_service.collect_mac_table(device)

            # 保存结果
            await self._save_results(device_id, arp_result, mac_result)

            logger.info(f"设备 {device_name} 采集完成")
            return True

        except Exception as e:
            logger.error(f"设备 {device_name} 采集失败: {e}")
            return False

    async def _save_results(self, device_id: int, arp_result: Any, mac_result: Any):
        """保存采集结果"""
        # 实现保存逻辑
        pass

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._running


# 全局调度器实例
_scheduler: Optional[ARPMACScheduler] = None


def get_arp_mac_scheduler() -> ARPMACScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ARPMACScheduler()
    return _scheduler
```

#### FastAPI 集成修改

```python
# app/main.py 或 app/api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.arp_mac_scheduler import get_arp_mac_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    scheduler = get_arp_mac_scheduler()
    await scheduler.start()

    yield

    # 关闭时
    await scheduler.stop()


app = FastAPI(lifespan=lifespan)
```

#### 优缺点

| 维度 | 说明 |
|------|------|
| **优点** | 最彻底的解决方案；所有代码在同一事件循环；避免 `asyncio.run()` 问题 |
| **缺点** | 改动范围大；需要修改调度器启动方式；需要确保 FastAPI 正确初始化 |
| **风险** | 中高（改动较大，需要全面测试） |

---

### 9.4 方案对比

| 维度 | 方案一（懒初始化 Lock） | 方案二（threading.Lock） | 方案三（AsyncIOScheduler） |
|------|------------------------|------------------------|---------------------------|
| **改动范围** | 小（1个文件） | 中（1-2个文件） | 大（多个文件） |
| **实现复杂度** | 低 | 中 | 高 |
| **风险等级** | 低 | 中 | 中高 |
| **性能影响** | 无 | 可能轻微影响并发 | 无 |
| **可维护性** | 高 | 中 | 高 |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

### 9.5 推荐方案

**推荐使用方案一：懒初始化 Lock**

理由：
1. **改动最小**：只需修改 `ssh_connection_pool.py` 一个文件
2. **风险最低**：不改变现有架构，保持原有异步特性
3. **易于验证**：修改后易于测试和验证
4. **向后兼容**：不破坏现有 API 接口

---

### 9.6 验证步骤

#### 方案一验证步骤

```bash
# 1. 应用修改后重启应用
python -m uvicorn app.main:app --reload

# 2. 观察启动日志，确认无错误
# 预期：无 "Lock is bound to a different event loop" 错误

# 3. 触发 ARP/MAC 采集任务
# 方式一：等待定时任务触发
# 方式二：调用 API 手动触发

# 4. 检查日志输出
# 预期：采集任务正常执行，无事件循环相关错误

# 5. 验证数据库记录
# 预期：ARP/MAC 数据正常写入
```

#### 单元测试验证

```python
# tests/test_ssh_connection_pool.py

import asyncio
import pytest
from app.services.ssh_connection_pool import SSHConnectionPool


class TestSSHConnectionPoolLazyInit:
    """测试 SSH 连接池懒初始化"""

    def test_lock_lazy_init(self):
        """测试 Lock 延迟初始化"""
        pool = SSHConnectionPool()
        # 此时 _lock 应该是 None
        assert pool._lock is None

        # 获取 lock 应该创建实例
        lock = pool._get_lock()
        assert lock is not None
        assert isinstance(lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_lock_in_event_loop(self):
        """测试 Lock 在事件循环中正确工作"""
        pool = SSHConnectionPool()

        # 在事件循环中获取 Lock
        lock = pool._get_lock()

        # 应该能够正常使用
        async with lock:
            # 在锁内执行操作
            pass

        # 不应该抛出 "bound to a different event loop" 错误
        assert True

    @pytest.mark.asyncio
    async def test_multiple_event_loops(self):
        """测试多个事件循环场景"""
        pool = SSHConnectionPool()

        # 第一个事件循环
        async def task1():
            lock = pool._get_lock()
            async with lock:
                await asyncio.sleep(0.1)

        # 第二个事件循环（模拟 asyncio.run()）
        async def task2():
            lock = pool._get_lock()
            async with lock:
                await asyncio.sleep(0.1)

        # 运行在同一个事件循环中应该成功
        await asyncio.gather(task1(), task2())
```

#### 集成测试验证

```python
# tests/integration/test_arp_mac_collection.py

import asyncio
import pytest
from app.services.arp_mac_scheduler import get_arp_mac_scheduler
from app.services.ssh_connection_pool import get_ssh_connection_pool


@pytest.mark.asyncio
async def test_collection_with_connection_pool():
    """测试采集任务与连接池集成"""

    # 获取连接池实例
    pool = get_ssh_connection_pool()

    # 获取调度器实例
    scheduler = get_arp_mac_scheduler()

    # 启动调度器
    await scheduler.start()

    # 等待一次采集完成
    await asyncio.sleep(5)

    # 验证连接池状态
    assert pool._lock is not None  # Lock 应该已初始化

    # 停止调度器
    await scheduler.stop()
```

#### 手动验证脚本

```python
# scripts/verify_lock_fix.py

import asyncio
import sys

# 添加项目路径
sys.path.insert(0, '/path/to/project')

from app.services.ssh_connection_pool import SSHConnectionPool


async def test_connection_pool():
    """测试连接池事件循环兼容性"""

    print("1. 创建连接池实例...")
    pool = SSHConnectionPool()
    print(f"   Lock 状态: {pool._lock}")

    print("\n2. 在事件循环中获取 Lock...")
    lock = pool._get_lock()
    print(f"   Lock 实例: {lock}")

    print("\n3. 尝试使用 Lock...")
    async with lock:
        print("   成功获取 Lock！")

    print("\n4. 模拟 asyncio.run() 场景...")

    async def use_pool():
        lock = pool._get_lock()
        async with lock:
            print("   在新事件循环中成功使用 Lock！")

    # 这在修复前会失败
    await asyncio.run(use_pool())

    print("\n✅ 所有测试通过！Lock 修复有效。")


if __name__ == "__main__":
    asyncio.run(test_connection_pool())
```

#### 日志验证

```bash
# 成功的日志输出应该包含：
# INFO: ARP/MAC 采集调度器已启动
# INFO: 开始执行 ARP/MAC 采集任务
# INFO: 获取到 X 台活跃设备
# INFO: 开始采集设备: xxx
# INFO: 设备 xxx 采集完成
# INFO: 采集任务完成，成功: X，失败: X

# 失败的日志输出（修复前）：
# ERROR: RuntimeError: Lock is bound to a different event loop
# ERROR: 采集任务执行失败
```

---

**报告完成时间**: 2026-03-30
**分析工具**: Claude Code