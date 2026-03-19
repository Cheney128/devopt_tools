
# Phase1 - 主循环引用管理

## 概述
在应用启动时保存 FastAPI 主事件循环的全局引用，供备份调度器使用。

## 变更文件
- `app/main.py`

## 设计详情

### 1. 添加全局变量
在 `app/main.py` 顶部添加全局变量：
```python
import asyncio

# 全局主事件循环引用
_main_event_loop = None
```

### 2. 提供获取函数
添加获取主事件循环的函数：
```python
def get_main_event_loop() -&gt; asyncio.AbstractEventLoop:
    """
    获取主事件循环引用
    
    Returns:
        asyncio.AbstractEventLoop: 主事件循环对象
        
    Raises:
        RuntimeError: 如果主事件循环未初始化
    """
    if _main_event_loop is None:
        raise RuntimeError("Main event loop not initialized. Call init_main_event_loop() first.")
    return _main_event_loop


def init_main_event_loop() -&gt; None:
    """
    初始化主事件循环引用
    应该在 FastAPI startup 事件中调用
    """
    global _main_event_loop
    _main_event_loop = asyncio.get_running_loop()
    logger.info(f"[MainLoop] Main event loop initialized: {_main_event_loop}")
```

### 3. 在 startup 事件中初始化
在 `startup_event()` 函数开头调用初始化函数：
```python
@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    # 初始化主事件循环引用
    init_main_event_loop()
    
    # ... 其余原有代码 ...
```

## 验证要点
- 应用启动时日志应显示 "Main event loop initialized"
- `get_main_event_loop()` 能够正确返回主循环对象
- 在非启动状态下调用应抛出 RuntimeError

