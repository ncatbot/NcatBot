"""BilibiliAdapter — B 站平台适配器

支持直播间弹幕 (WebSocket)、私信 (轮询)、视频评论 (轮询)。
单 adapter 通过 SourceManager 管理多数据源。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from ncatbot.adapter.base import BaseAdapter
from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient
    from ncatbot.types import BaseEventData

LOG = get_log("BilibiliAdapter")


class BilibiliAdapter(BaseAdapter):
    name = "bilibili"
    description = "Bilibili 适配器 (直播/私信/评论/动态)"
    supported_protocols = [
        "bilibili_live",
        "bilibili_session",
        "bilibili_comment",
        "bilibili_dynamic",
    ]
    platform = "bilibili"
    pip_dependencies = {"bilibili-api-python": ">=17.0.0"}

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
        from .config import BilibiliConfig

        self._config = BilibiliConfig.model_validate(self._raw_config)
        self._credential: Any = None
        self._source_manager: Any = None
        self._api: Any = None
        self._parser: Any = None
        self._connected = False

    async def setup(self) -> None:
        from bilibili_api import Credential
        from .auth import qrcode_login
        from .credential_store import has_valid_credential, save_credential_to_config

        if has_valid_credential(self._config):
            self._credential = Credential(
                sessdata=self._config.sessdata,
                bili_jct=self._config.bili_jct,
                buvid3=self._config.buvid3,
                dedeuserid=self._config.dedeuserid,
                ac_time_value=self._config.ac_time_value,
            )
            # 验证凭据是否仍然有效
            try:
                valid = await self._credential.check_valid()
            except Exception:
                valid = False
            if not valid:
                LOG.warning("Bilibili 凭据已失效，需要重新扫码登录")
                self._credential = await qrcode_login()
                save_credential_to_config(self._credential)
            else:
                LOG.debug("Bilibili 凭据验证通过")
        else:
            LOG.info("未检测到 Bilibili 凭据，启动扫码登录...")
            self._credential = await qrcode_login()
            save_credential_to_config(self._credential)

        LOG.info("Bilibili 凭据已就绪")

    async def connect(self) -> None:
        from .source.manager import SourceManager
        from .api import BiliBotAPI
        from .parser import BiliEventParser

        self._parser = BiliEventParser(self_id=self._bot_uin)

        self._source_manager = SourceManager(
            callback=self._on_source_event,
            max_retry=self._config.max_retry,
            retry_after=self._config.retry_after,
            session_poll_interval=self._config.session_poll_interval,
            comment_poll_interval=self._config.comment_poll_interval,
            dynamic_poll_interval=self._config.dynamic_poll_interval,
        )

        self._api = BiliBotAPI(self._credential, self._source_manager)

        # 从配置添加初始数据源
        for room_id in self._config.live_rooms:
            await self._source_manager.add_live_room(room_id, self._credential)

        if self._config.enable_session:
            await self._source_manager.start_session(self._credential)

        for watch in self._config.comment_watches:
            await self._source_manager.add_comment_watch(
                watch.id, watch.type, self._credential
            )

        for watch in self._config.dynamic_watches:
            await self._source_manager.add_dynamic_watch(watch.uid, self._credential)

        self._connected = True
        LOG.info(
            "Bilibili 适配器已连接 (直播间: %d, 私信: %s, 评论: %d, 动态: %d)",
            len(self._config.live_rooms),
            self._config.enable_session,
            len(self._config.comment_watches),
            len(self._config.dynamic_watches),
        )

    async def listen(self) -> None:
        await self._source_manager.run_forever()

    async def disconnect(self) -> None:
        if self._source_manager is not None:
            await self._source_manager.stop_all()
        self._connected = False
        LOG.debug("Bilibili 适配器已断开")

    def get_api(self) -> "IAPIClient":
        return self._api

    @property
    def connected(self) -> bool:
        return self._connected

    async def _on_source_event(self, source_type: str, raw_data: dict) -> None:
        """数据源回调 → 解析 → 事件回调"""
        parsed: Optional["BaseEventData"] = self._parser.parse(source_type, raw_data)
        if parsed is not None and self._event_callback is not None:
            await self._event_callback(parsed)
