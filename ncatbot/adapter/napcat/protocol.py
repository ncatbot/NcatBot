"""
NapCat 协议层：echo/Future 请求-响应匹配

从 core/service/builtin/message_router.py 提取核心的请求-响应匹配逻辑。
"""

import asyncio
import threading
import uuid
from typing import Dict, Optional, Callable, Awaitable

from ncatbot.utils import get_log

from .connection import NapCatConnection

LOG = get_log("NapCatProtocol")


class NapCatProtocol:
    """请求-响应匹配协议层

    使用 echo/UUID + asyncio.Future 实现 API 请求的请求-响应匹配。
    同时将非响应消息（事件）转发给事件回调。
    """

    def __init__(self, connection: NapCatConnection):
        self._connection = connection
        self._event_callback: Optional[Callable[[dict], Awaitable[None]]] = None

        # echo -> Future 映射
        self._pending_futures: Dict[str, asyncio.Future] = {}
        self._futures_lock = threading.Lock()

        # 记录创建时所在的事件循环
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # 将自身设置为 connection 的消息回调
        self._connection.set_message_callback(self._on_message)

    def bind_loop(self) -> None:
        """绑定当前事件循环"""
        self._loop = asyncio.get_running_loop()

    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """设置事件回调（非 API 响应的消息）"""
        self._event_callback = callback

    async def send(
        self,
        action: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> dict:
        """发送 API 请求并等待响应

        Args:
            action: API 动作名称
            params: 请求参数
            timeout: 超时时间（秒）

        Returns:
            API 响应数据
        """
        echo = str(uuid.uuid4())

        current_loop = asyncio.get_running_loop()
        future = current_loop.create_future()

        with self._futures_lock:
            self._pending_futures[echo] = future

        async def _do_send():
            await self._connection.send(
                {
                    "action": action.replace("/", ""),
                    "params": params or {},
                    "echo": echo,
                }
            )

        try:
            # 确保在正确的事件循环上发送
            if self._loop and current_loop == self._loop:
                await _do_send()
            elif self._loop:
                asyncio.run_coroutine_threadsafe(_do_send(), self._loop)
            else:
                await _do_send()

            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"API请求超时: {action}")
        finally:
            with self._futures_lock:
                self._pending_futures.pop(echo, None)

    def cancel_all(self) -> None:
        """取消所有挂起的请求"""
        with self._futures_lock:
            for future in self._pending_futures.values():
                if not future.done():
                    future.cancel()
            self._pending_futures.clear()

    async def _on_message(self, data: dict) -> None:
        """处理收到的消息：区分 API 响应和事件"""
        echo = data.get("echo")

        # 优先检查是否是 API 响应
        if echo:
            with self._futures_lock:
                future = self._pending_futures.get(echo)
            if future and not future.done():
                future.get_loop().call_soon_threadsafe(future.set_result, data)
                return

        # 非响应消息视为事件
        if self._event_callback:
            asyncio.ensure_future(self._event_callback(data))
