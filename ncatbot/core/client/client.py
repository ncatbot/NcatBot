"""BotClient — Bot 统一入口

负责引导 Adapter 启动、组装 BotAPIClient、接通事件流。
暂不涉及服务管理、注册器、插件加载等。
"""

from __future__ import annotations

import asyncio
from typing import Optional, TYPE_CHECKING

from ncatbot.adapter.base import BaseAdapter
from ncatbot.adapter.napcat.adapter import NapCatAdapter
from ncatbot.api.client import BotAPIClient
from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.utils import get_log, setup_logging

if TYPE_CHECKING:
    pass

LOG = get_log("BotClient")


class BotClient:
    """Bot 生命周期管理器

    用法::

        bot = BotClient()

        @bot.on("message.group")
        async def on_group_msg(event):
            await event.reply("hello")

        bot.run()
    """

    def __init__(self, adapter: Optional[BaseAdapter] = None) -> None:
        setup_logging()
        self._adapter = adapter or NapCatAdapter()
        self._api: Optional[BotAPIClient] = None
        self._dispatcher: Optional[AsyncEventDispatcher] = None
        self._running = False

        # 待注册的 handler（在 run 之前通过 @bot.on() 收集）
        self._pending_handlers: list[tuple[str, object, dict]] = []

    @property
    def api(self) -> BotAPIClient:
        if self._api is None:
            LOG.warning("API 不可用：BotClient 尚未启动")
            raise RuntimeError("API 不可用：BotClient 尚未启动")
        return self._api

    # ---- 启动 ----
    def run(self, **kwargs) -> None:
        """同步阻塞启动"""
        try:
            asyncio.run(self._run(**kwargs))
        except KeyboardInterrupt:
            LOG.info("收到 Ctrl+C，正在退出…")

    async def run_async(self, **kwargs) -> None:
        """异步启动（已有事件循环时使用）"""
        await self._run(**kwargs)

    async def _run(self, **kwargs) -> None:
        self._running = True
        try:
            await self._startup()
            LOG.info("Bot 已就绪，开始监听事件")
            await self._adapter.listen()
        except asyncio.CancelledError:
            LOG.info("Bot 被取消")
        finally:
            await self._shutdown()

    # ---- 内部生命周期 ----

    async def _startup(self) -> None:
        """引导启动：adapter setup → connect → 组装 API → 接通事件流"""
        # 1. 准备 + 连接
        LOG.info("正在启动 Adapter: %s", self._adapter.name)
        await self._adapter.setup()
        await self._adapter.connect()

        # 2. 从 adapter 取出底层 IBotAPI，包装为 BotAPIClient
        raw_api = self._adapter.get_api()
        self._api = BotAPIClient(raw_api)
        LOG.info("BotAPIClient 已就绪")

        # 3. 创建 dispatcher
        #    dispatcher 内部把 api 传给 handler，但我们用 _wrap_handler 桥接，
        #    所以传底层 raw_api（满足 IBotAPI 类型），实际 handler 用 self._api
        self._dispatcher = AsyncEventDispatcher(raw_api)

        # 5. 把 adapter 的事件回调接到 dispatcher
        self._adapter.set_event_callback(self._dispatcher.dispatch)

    async def _shutdown(self) -> None:
        self._running = False
        LOG.info("正在关闭…")
        try:
            await self._adapter.disconnect()
        except Exception as e:
            LOG.error("关闭 Adapter 异常: %s", e)
        LOG.info("已关闭")
