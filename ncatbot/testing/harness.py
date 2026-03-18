"""
TestHarness — 编排 BotClient + MockAdapter 的测试工具

提供 async with 上下文管理器，在后台运行 BotClient，
支持注入事件和检查 API 调用。
"""

from __future__ import annotations

import asyncio
from typing import Callable, List, Optional, TYPE_CHECKING

from ncatbot.adapter import MockAdapter, MockBotAPI, APICall
from ncatbot.app import BotClient
from ncatbot.core import AsyncEventDispatcher, Event

if TYPE_CHECKING:
    from ncatbot.types import BaseEventData


class TestHarness:
    """测试编排器 — 在后台启动 BotClient（使用 MockAdapter），提供事件注入和断言 API。"""

    __test__ = False  # 告知 pytest 这不是测试类

    def __init__(self) -> None:
        self._adapter = MockAdapter(platform="qq")
        self._bot = BotClient(adapter=self._adapter)

    @property
    def bot(self) -> BotClient:
        return self._bot

    @property
    def adapter(self) -> MockAdapter:
        return self._adapter

    @property
    def mock_api(self) -> MockBotAPI:
        return self._adapter.mock_api

    @property
    def dispatcher(self) -> AsyncEventDispatcher:
        return self._bot._dispatcher

    # ---- 生命周期 ----

    async def start(self) -> None:
        """启动 BotClient（非阻塞），等待就绪"""
        await self._bot.run_async()

    async def stop(self) -> None:
        """停止 BotClient"""
        await self._bot.shutdown()

    async def __aenter__(self) -> "TestHarness":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    # ---- 事件注入 ----

    async def inject(self, event_data: "BaseEventData") -> None:
        """注入事件到 dispatcher"""
        await self._adapter.inject_event(event_data)

    async def inject_many(self, events: List["BaseEventData"]) -> None:
        """依次注入多个事件"""
        for ev in events:
            await self.inject(ev)

    # ---- 等待/同步 ----

    async def settle(self, delay: float = 0.05) -> None:
        """给 handler 一点时间执行

        如果测试不稳定可以适当增大 delay。
        """
        await asyncio.sleep(delay)

    async def wait_event(
        self,
        predicate: Optional[Callable[[Event], bool]] = None,
        timeout: float = 2.0,
    ) -> Event:
        """等待 dispatcher 产出的下一个事件"""
        return await self._bot._dispatcher.wait_event(predicate, timeout)

    # ---- API 调用断言 ----

    @property
    def api_calls(self) -> List[APICall]:
        return self.mock_api.calls

    def api_called(self, action: str) -> bool:
        return self.mock_api.called(action)

    def api_call_count(self, action: str) -> int:
        return self.mock_api.call_count(action)

    def get_api_calls(self, action: str) -> List[APICall]:
        return self.mock_api.get_calls(action)

    def last_api_call(self, action: Optional[str] = None) -> Optional[APICall]:
        return self.mock_api.last_call(action)

    def reset_api(self) -> None:
        """清空 API 调用记录"""
        self.mock_api.reset()
