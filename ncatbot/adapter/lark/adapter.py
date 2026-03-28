"""LarkAdapter — 飞书平台适配器

通过 lark-oapi SDK 的 WebSocket 长连接接收事件，
封装 lark-oapi Client 发送消息。

SDK 的 ws.Client.start() 是阻塞调用，内部在独立线程运行。
事件回调在 SDK 内部线程触发，需要通过 run_coroutine_threadsafe
安全地调度到主事件循环。
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, Optional, TYPE_CHECKING

from ..base import BaseAdapter
from ncatbot.utils import get_log
from .api import LarkBotAPI
from .config import LarkConfig
from .parser import LarkEventParser

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient
    from ncatbot.types import BaseEventData

LOG = get_log("LarkAdapter")


class LarkAdapter(BaseAdapter):
    name = "lark"
    description = "飞书 (Lark) 适配器 (WebSocket)"
    supported_protocols = ["lark_ws"]
    platform = "lark"
    pip_dependencies = {"lark-oapi": ">=1.5.3"}

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        bot_uin: str = "",
        websocket_timeout: int = 15,
    ) -> None:
        super().__init__(
            config=config,
            bot_uin=bot_uin,
            websocket_timeout=websocket_timeout,
        )
        self._config = LarkConfig.model_validate(self._raw_config)
        self._client: Any = None
        self._ws_client: Any = None
        self._api: Optional[LarkBotAPI] = None
        self._parser: Optional[LarkEventParser] = None
        self._connected = False
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._stop_event = asyncio.Event()

    async def setup(self) -> None:
        """验证飞书配置"""
        if not self._config.app_id or not self._config.app_secret:
            raise ValueError("飞书适配器需要配置 app_id 和 app_secret")
        LOG.info("飞书配置已就绪: app_id=%s", self._config.app_id)

    async def connect(self) -> None:
        import lark_oapi as lark

        self._main_loop = asyncio.get_running_loop()
        self._parser = LarkEventParser(self_id=self._config.app_id)

        # 创建 lark Client（用于 API 调用）
        self._client = (
            lark.Client.builder()
            .app_id(self._config.app_id)
            .app_secret(self._config.app_secret)
            .log_level(lark.LogLevel.ERROR)
            .build()
        )

        self._api = LarkBotAPI(self._client)

        # 创建事件处理器
        event_handler = (
            lark.EventDispatcherHandler.builder(
                self._config.verification_token,
                self._config.encrypt_key,
            )
            .register_p2_im_message_receive_v1(self._on_sdk_message)
            .register_p2_im_message_message_read_v1(self._on_sdk_message_read)
            .register_p2_im_message_recalled_v1(self._on_sdk_message_recalled)
            .build()
        )

        # 创建 WebSocket 客户端
        self._ws_client = lark.ws.Client(
            self._config.app_id,
            self._config.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.ERROR,
        )

        self._connected = True
        LOG.info("飞书适配器已连接")

    async def listen(self) -> None:
        """启动 SDK WebSocket 监听（在独立线程中运行）"""

        def _run_ws():
            LOG.info("飞书 WebSocket 线程启动")
            try:
                import lark_oapi.ws.client as _ws_mod

                # SDK 在模块级缓存了 asyncio event loop，
                # 但那个 loop 是主线程正在运行的 loop，
                # 子线程中 run_until_complete 会报 "already running"。
                # 解决：为子线程创建独立 loop 并替换 SDK 模块级变量。
                thread_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(thread_loop)
                _ws_mod.loop = thread_loop

                self._ws_client.start()
            except Exception:
                LOG.exception("飞书 WebSocket 线程异常退出")

        self._ws_thread = threading.Thread(
            target=_run_ws,
            name="LarkWSClient",
            daemon=True,
        )
        self._ws_thread.start()
        LOG.info("飞书 WebSocket 已在后台线程启动")

        # 阻塞直到 stop
        await self._stop_event.wait()

    async def disconnect(self) -> None:
        self._stop_event.set()
        self._connected = False
        LOG.info("飞书适配器已断开")

    def get_api(self) -> "IAPIClient":
        return self._api

    @property
    def connected(self) -> bool:
        return self._connected

    def _on_sdk_message(self, data) -> None:
        """SDK 消息回调（在 SDK 内部线程中触发）

        通过 run_coroutine_threadsafe 安全地调度到主事件循环。
        """
        if self._main_loop is None or not self._main_loop.is_running():
            LOG.warning("主事件循环未运行，丢弃飞书消息")
            return

        asyncio.run_coroutine_threadsafe(self._handle_message(data), self._main_loop)

    def _on_sdk_message_read(self, data) -> None:
        """SDK 消息已读回调"""
        if self._main_loop is None or not self._main_loop.is_running():
            LOG.warning("主事件循环未运行，丢弃飞书已读事件")
            return
        asyncio.run_coroutine_threadsafe(
            self._handle_message_read(data), self._main_loop
        )

    def _on_sdk_message_recalled(self, data) -> None:
        """SDK 消息撤回回调"""
        if self._main_loop is None or not self._main_loop.is_running():
            LOG.warning("主事件循环未运行，丢弃飞书撤回事件")
            return
        asyncio.run_coroutine_threadsafe(
            self._handle_message_recalled(data), self._main_loop
        )

    async def _handle_message(self, data) -> None:
        """解析飞书事件并回调给分发器（在主事件循环中执行）"""
        parsed: Optional["BaseEventData"] = self._parser.parse_message(data)
        if parsed is not None and self._event_callback is not None:
            await self._event_callback(parsed)

    async def _handle_message_read(self, data) -> None:
        """解析飞书消息已读事件并回调给分发器"""
        parsed: Optional["BaseEventData"] = self._parser.parse_message_read(data)
        if parsed is not None and self._event_callback is not None:
            await self._event_callback(parsed)

    async def _handle_message_recalled(self, data) -> None:
        """解析飞书消息撤回事件并回调给分发器"""
        parsed: Optional["BaseEventData"] = self._parser.parse_message_recalled(data)
        if parsed is not None and self._event_callback is not None:
            await self._event_callback(parsed)
