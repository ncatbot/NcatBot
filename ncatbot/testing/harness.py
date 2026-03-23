"""
TestHarness — 多平台测试编排器

提供 async with 上下文管理器，在后台运行 BotClient（多 MockAdapter），
支持事件注入、fluent 断言、平台作用域。
"""

from __future__ import annotations

import asyncio
from typing import Callable, Dict, List, Optional, Sequence, TYPE_CHECKING

from ncatbot.adapter.mock import MockAdapter, MockAPIBase
from ncatbot.app import BotClient
from ncatbot.core import AsyncEventDispatcher, Event

from .assertions import APICallAssertion, PlatformScope

if TYPE_CHECKING:
    from ncatbot.types import BaseEventData


class TestHarness:
    """多平台测试编排器 — 启动 BotClient + MockAdapter，提供注入与断言。"""

    __test__ = False

    def __init__(self, platforms: Sequence[str] = ("qq",)) -> None:
        adapters = [MockAdapter(platform=p) for p in platforms]
        self._bot = BotClient(adapters=adapters)
        self._adapters: Dict[str, MockAdapter] = {a.platform: a for a in adapters}

    @property
    def bot(self) -> BotClient:
        return self._bot

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
        """注入事件到对应平台的 adapter（走真实链路）"""
        platform = getattr(event_data, "platform", "unknown")
        adapter = self._adapters.get(platform)
        if adapter:
            await adapter.inject_event(event_data)
        else:
            raise ValueError(f"未注册平台 '{platform}'，已注册: {list(self._adapters)}")

    async def inject_many(self, events: List["BaseEventData"]) -> None:
        """依次注入多个事件"""
        for ev in events:
            await self.inject(ev)

    # ---- 等待/同步 ----

    async def settle(self, delay: float = 0.05) -> None:
        """给 handler 一点时间执行"""
        await asyncio.sleep(delay)

    async def wait_event(
        self,
        predicate: Optional[Callable[[Event], bool]] = None,
        timeout: float = 2.0,
    ) -> Event:
        """等待 dispatcher 产出的下一个事件"""
        return await self._bot._dispatcher.wait_event(predicate, timeout)

    # ---- 平台访问 ----

    def mock_api_for(self, platform: str) -> MockAPIBase:
        """获取指定平台的 Mock API"""
        return self._adapters[platform].mock_api

    @property
    def mock_api(self) -> MockAPIBase:
        """单平台快捷访问（返回第一个平台的 mock）"""
        return next(iter(self._adapters.values())).mock_api

    def adapter_for(self, platform: str) -> MockAdapter:
        return self._adapters[platform]

    # ---- Fluent 断言 ----

    def assert_api(self, action: str) -> APICallAssertion:
        """全平台范围断言"""
        all_calls = [c for a in self._adapters.values() for c in a.mock_api.calls]
        return APICallAssertion(action, all_calls)

    def on(self, platform: str) -> PlatformScope:
        """限定平台范围"""
        return PlatformScope(self, platform)

    # ---- 重置 ----

    def reset_api(self, platform: Optional[str] = None) -> None:
        """清空 API 调用记录"""
        if platform:
            self._adapters[platform].mock_api.reset()
        else:
            for a in self._adapters.values():
                a.mock_api.reset()
