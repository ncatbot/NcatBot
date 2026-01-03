import asyncio
import uuid
from typing import Dict, Optional, Callable, Awaitable

from ..base import BaseService
from ncatbot.core.adapter.nc import NapCatWebSocket
from ncatbot.utils import get_log

LOG = get_log("MessageRouter")


class MessageRouter(BaseService):
    """
    消息路由服务 (异步优化版)

    改进点：
    1. 移除 threading.Lock 和 queue.Queue，消除线程阻塞风险。
    2. 使用 asyncio.Future 实现高效的请求-响应匹配。
    3. 移除 asyncio.to_thread，大幅降低并发开销。
    """

    name = "message_router"
    description = "消息路由服务"

    def __init__(
        self,
        uri: Optional[str] = None,
        event_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
        **config,
    ):
        super().__init__(**config)
        self._uri = uri
        self._event_callback = event_callback

        self._ws: Optional[NapCatWebSocket] = None

        # 核心改进：使用 Future 存储挂起的请求
        # Key: echo (str), Value: asyncio.Future
        self._pending_futures: Dict[str, asyncio.Future] = {}

    async def on_load(self) -> None:
        self._ws = NapCatWebSocket(
            uri=self._uri,
            message_callback=self._on_message,
        )
        await self._ws.connect()
        LOG.info("消息路由服务已加载")

    async def on_close(self) -> None:
        # 清理所有正在等待的 Future，防止调用方永久卡死
        for future in self._pending_futures.values():
            if not future.done():
                future.cancel()
        self._pending_futures.clear()

        if self._ws:
            await self._ws.disconnect()
            self._ws = None

        LOG.info("消息路由服务已关闭")

    @property
    def connected(self) -> bool:
        return self._ws is not None and self._ws.connected

    @property
    def websocket(self) -> Optional[NapCatWebSocket]:
        return self._ws

    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self._event_callback = callback

    async def send(
        self,
        action: str,
        params: Optional[dict] = None,
        timeout: float = 30.0,  # 建议默认超时不要设置太长，30秒足够
    ) -> dict:
        if not self._ws:
            raise ConnectionError("服务未连接")

        echo = str(uuid.uuid4())

        # 1. 创建一个 Future 对象，代表“未来的结果”
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        # 2. 存入字典，准备接收
        self._pending_futures[echo] = future

        try:
            # 3. 发送 WebSocket 消息
            await self._ws.send(
                {
                    "action": action.replace("/", ""),
                    "params": params or {},
                    "echo": echo,
                }
            )

            # 4. 非阻塞等待 Future 完成
            # 这里没有任何线程切换，纯异步挂起
            return await asyncio.wait_for(future, timeout=timeout)

        except asyncio.TimeoutError:
            raise TimeoutError(f"API请求超时: {action}")
        finally:
            # 5. 无论成功、失败还是超时，都要清理字典
            # dict.pop 是原子操作（在单线程 async 循环中），不需要 Lock
            self._pending_futures.pop(echo, None)

    def start_listening(self):
        if self._ws:
            return self._ws.start_listening()

    async def _on_message(self, data: dict) -> None:
        """处理收到的消息"""
        echo = data.get("echo")

        # 1. 优先检查是否是 API 响应
        if echo:
            # 从字典中查找对应的 Future
            future = self._pending_futures.get(echo)
            if future and not future.done():
                # 2. 填入结果，唤醒 send 中的 await
                future.set_result(data)
                return

        # 2. 如果不是响应，或者找不到 echo，则视为事件
        if self._event_callback:
            # 建议使用 create_task 防止用户回调阻塞 WebSocket 接收循环
            asyncio.create_task(self._event_callback(data))
