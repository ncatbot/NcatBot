"""
Mock 服务器客户端

提供连接到 MockServer 的客户端包装器。
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional

HAS_WEBSOCKETS = False
websockets = None  # type: ignore
try:
    import websockets as _websockets  # type: ignore
    import websockets.exceptions  # type: ignore

    websockets = _websockets
    HAS_WEBSOCKETS = True
except ImportError:
    pass


class MockServerClient:
    """
    改进后的 MockServerClient
    保持接口完全不变，但支持高并发调用并提升了性能。
    """

    def __init__(self, uri: str):
        if not HAS_WEBSOCKETS:
            raise ImportError("需要安装 websockets 库: pip install websockets")

        self.uri = uri
        self._ws: Any = None
        # 核心改进：使用 Future 字典代替 Queue
        self._pending_futures: Dict[str, asyncio.Future] = {}
        self._event_callback: Optional[Callable[..., Any]] = None
        self._listen_task: Optional[asyncio.Task[None]] = None
        self._echo_counter = 0

    async def connect(self) -> None:
        """连接到服务器"""
        if websockets is None:
            raise ImportError("需要安装 websockets 库: pip install websockets")
        self._ws = await websockets.connect(self.uri)
        self._listen_task = asyncio.create_task(self._listen())

    async def disconnect(self) -> None:
        """断开连接"""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            await self._ws.close()
            self._ws = None

        # 清理未完成的请求，防止调用方永久挂起
        for fut in self._pending_futures.values():
            if not fut.done():
                fut.set_exception(ConnectionError("客户端已断开连接"))
        self._pending_futures.clear()

    async def _listen(self) -> None:
        """监听消息并精确分发"""
        if not self._ws:
            return

        try:
            async for message in self._ws:
                data = json.loads(message)
                echo = data.get("echo")

                # 优先处理 API 响应
                if echo is not None and echo in self._pending_futures:
                    fut = self._pending_futures.pop(echo)
                    if not fut.done():
                        fut.set_result(data)
                # 其次处理事件回调
                elif self._event_callback:
                    # 如果你确定回调不会阻塞，直接 await 是安全的
                    await self._event_callback(data)
        except Exception as e:
            if websockets and isinstance(e, websockets.exceptions.ConnectionClosed):
                pass
            else:
                # 可以在这里增加 log
                pass

    def set_event_callback(self, callback: Callable[..., Any]) -> None:
        """设置事件回调"""
        self._event_callback = callback

    async def call_api(
        self,
        action: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> dict:
        """调用 API (并发安全版)"""
        if not self._ws:
            raise ConnectionError("未连接到服务器")

        self._echo_counter += 1
        echo = str(self._echo_counter)

        # 为当前请求创建一个 Future 对象
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_futures[echo] = fut

        request = {
            "action": action,
            "params": params or {},
            "echo": echo,
        }

        try:
            await self._ws.send(json.dumps(request))
            # 等待特定的 Future 完成，不再涉及 Queue 的抢占
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"API {action} 调用超时 (echo: {echo})")
        finally:
            # 无论成功、失败或超时，都要确保清理字典
            self._pending_futures.pop(echo, None)

    async def __aenter__(self) -> "MockServerClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()
