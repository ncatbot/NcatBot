"""
NapCat WebSocket 连接器

负责与 NapCat 服务的底层 WebSocket 连接。
只负责连接管理、发送数据、接收数据，不做任何消息类型区分。
"""

import asyncio
import json
from typing import Optional, Callable, Awaitable

import websockets
from websockets.exceptions import ConnectionClosedError

from ncatbot.utils import get_log, ncatbot_config
from ncatbot.utils.error import NcatBotConnectionError

LOG = get_log("NapCatWebSocket")


class NapCatWebSocket:
    """
    NapCat WebSocket 连接器

    职责：
    - 建立/维护 WebSocket 连接
    - 发送原始数据
    - 接收数据并通过回调传递（不区分事件/响应）

    可以同时创建多个实例连接到不同的 NapCat 服务。
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        message_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ):
        """
        Args:
            uri: WebSocket URI，不提供则从配置读取
            message_callback: 收到任何消息时的回调
        """
        self._uri = uri
        self._client: Optional[websockets.ClientConnection] = None
        self._message_callback = message_callback
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """建立 WebSocket 连接"""
        uri = self._uri or ncatbot_config.get_uri_with_token()
        self._client = await websockets.connect(
            uri, close_timeout=0.2, max_size=2**30, open_timeout=1
        )
        self._running = True
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

    # ------------------------------------------------------------------
    # 状态属性
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """是否已连接"""
        return self._client is not None and self._running

    @property
    def uri(self) -> Optional[str]:
        """当前连接的 URI"""
        return self._uri

    # ------------------------------------------------------------------
    # 回调设置
    # ------------------------------------------------------------------

    def set_message_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        """设置消息回调（收到任何消息时调用）"""
        self._message_callback = callback

    # ------------------------------------------------------------------
    # 数据发送
    # ------------------------------------------------------------------

    async def send(self, data: dict) -> None:
        """
        发送数据

        Args:
            data: 要发送的数据字典
        """
        if not self._client:
            raise ConnectionError("WebSocket 未连接")
        await self._client.send(json.dumps(data))

    # ------------------------------------------------------------------
    # 消息接收
    # ------------------------------------------------------------------

    async def listen(self) -> None:
        """
        开始监听消息

        此方法会阻塞，持续接收消息直到连接断开或停止。
        收到的所有消息都通过 message_callback 传递，不做区分。
        """
        if not self._client:
            raise ConnectionError("WebSocket 未连接")

        uri = self._uri or ncatbot_config.get_uri_with_token()

        while self._running:
            try:
                async for raw in self._client:
                    if not self._running:
                        break

                    data = json.loads(raw)

                    # 所有消息都通过回调传递，不区分类型
                    if self._message_callback:
                        await self._message_callback(data)

            except asyncio.CancelledError:
                break

            except ConnectionClosedError:
                if not self._running:
                    break

                LOG.info("连接断开，尝试重连...")
                if await self._reconnect(uri):
                    continue
                else:
                    raise NcatBotConnectionError("重连失败")

            except Exception as e:
                LOG.error(f"WebSocket 错误: {e}")
                raise

    def start_listening(self) -> asyncio.Task:
        """
        启动监听任务（非阻塞）

        Returns:
            监听任务
        """
        self._listen_task = asyncio.create_task(self.listen())
        return self._listen_task

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _reconnect(self, uri: str) -> bool:
        """尝试重连"""
        from .service import napcat_service_ok

        if napcat_service_ok(ncatbot_config.websocket_timeout):
            try:
                self._client = await websockets.connect(
                    uri, close_timeout=0.2, max_size=2**30, open_timeout=1
                )
                LOG.info("重连成功")
                return True
            except Exception as e:
                LOG.error(f"重连失败: {e}")
        return False
