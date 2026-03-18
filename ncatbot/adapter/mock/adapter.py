"""
MockAdapter — BaseAdapter 的内存实现

不连接任何外部服务，支持通过 inject_event() 注入事件，
所有 API 调用被 MockBotAPI 记录。
"""

from __future__ import annotations

import asyncio
from typing import Optional

from ..base import BaseAdapter
from ncatbot.api import IAPIClient
from ncatbot.types import BaseEventData

from .api import MockBotAPI


class MockAdapter(BaseAdapter):
    """Mock 适配器 — 用于无网络环境下的集成测试

    使用方式::

        adapter = MockAdapter()
        bot = BotClient(adapter=adapter)

        # 在 bot 启动后注入事件
        await adapter.inject_event(some_event_data)

        # 检查 API 调用
        assert adapter.mock_api.called("send_group_msg")

        # 停止 listen 循环
        adapter.stop()
    """

    name = "mock"
    description = "Mock 适配器（测试用）"
    supported_protocols = ["mock"]
    platform = "mock"

    def __init__(self, platform: str = "mock", **kwargs) -> None:
        super().__init__(**kwargs)
        self.platform = platform
        self._mock_api = MockBotAPI()
        self._connected = False
        self._stop_event: Optional[asyncio.Event] = None

    @property
    def mock_api(self) -> MockBotAPI:
        return self._mock_api

    # ---- 生命周期 ----

    async def setup(self) -> None:
        pass

    async def connect(self) -> None:
        self._connected = True
        self._stop_event = asyncio.Event()

    async def disconnect(self) -> None:
        self._connected = False
        if self._stop_event:
            self._stop_event.set()

    async def listen(self) -> None:
        """阻塞直到 stop() 被调用"""
        if self._stop_event is None:
            raise RuntimeError("MockAdapter 尚未 connect")
        await self._stop_event.wait()

    def get_api(self) -> IAPIClient:
        return self._mock_api

    @property
    def connected(self) -> bool:
        return self._connected

    # ---- 测试专用 ----

    async def inject_event(self, data: BaseEventData) -> None:
        """注入事件，触发 dispatcher 回调"""
        if self._event_callback is None:
            raise RuntimeError("事件回调未设置（BotClient 尚未启动）")
        await self._event_callback(data)

    def stop(self) -> None:
        """停止 listen 循环"""
        if self._stop_event:
            self._stop_event.set()
