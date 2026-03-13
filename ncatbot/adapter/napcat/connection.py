"""
NapCat WebSocket 连接管理

从 core/adapter/nc/websocket.py 迁移，负责 WebSocket 连接的建立、维护和数据收发。
"""

import asyncio
import json
from typing import Optional, Callable, Awaitable

import websockets
from websockets.exceptions import ConnectionClosedError

from ncatbot.utils import get_log, ncatbot_config
from ncatbot.utils.error import NcatBotConnectionError

LOG = get_log("NapCatConnection")


class NapCatConnection:
    """NapCat WebSocket 连接管理器

    职责：
    - 建立/维护 WebSocket 连接
    - 发送原始数据
    - 接收数据并通过回调传递
    """

    def __init__(
        self,
        uri: str,
        message_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ):
        self._uri = uri
        self._client: Optional[websockets.ClientConnection] = None
        self._message_callback = message_callback
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._send_lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        self._client = await websockets.connect(
            self._uri, close_timeout=0.2, max_size=2**30, open_timeout=1
        )
        self._running = True
        self._loop = asyncio.get_running_loop()
        LOG.info("WebSocket 已连接")

    async def disconnect(self) -> None:
        """关闭 WebSocket 连接"""
        self._running = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self._client:
            await self._client.close()
            self._client = None

        LOG.info("WebSocket 连接已关闭")

    @property
    def connected(self) -> bool:
        return self._client is not None and self._running

    @property
    def uri(self) -> Optional[str]:
        return self._uri

    def set_message_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self._message_callback = callback

    async def send(self, data: dict) -> None:
        """发送数据（协程安全，线程不安全）"""
        async with self._send_lock:
            if not self._client:
                raise ConnectionError("WebSocket 未连接")
            await self._client.send(json.dumps(data))

    async def listen(self) -> None:
        """阻塞监听消息，直到连接断开或停止"""
        if not self._client:
            raise ConnectionError("WebSocket 未连接")

        while self._running:
            try:
                async for raw in self._client:
                    if not self._running:
                        break

                    data = json.loads(raw)

                    if self._message_callback:
                        await self._message_callback(data)

            except asyncio.CancelledError:
                break

            except ConnectionClosedError:
                if not self._running:
                    break

                LOG.info("连接断开，尝试重连...")
                if await self._reconnect():
                    continue
                else:
                    raise NcatBotConnectionError("重连失败")

            except Exception as e:
                LOG.error(f"WebSocket 错误: {e}")
                raise

    async def _reconnect(self) -> bool:
        """尝试重连"""
        from ncatbot.core.adapter.nc.service import NapCatService

        if NapCatService().is_service_ok(ncatbot_config.websocket_timeout):
            try:
                self._client = await websockets.connect(
                    self._uri, close_timeout=0.2, max_size=2**30, open_timeout=1
                )
                LOG.info("重连成功")
                return True
            except Exception as e:
                LOG.error(f"重连失败: {e}")
        return False
