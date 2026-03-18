"""BiliBotAPI — Bilibili 平台 API 主实现

组合所有 Mixin 并实现 IBiliAPIClient 接口。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from ncatbot.api.bilibili import IBiliAPIClient
from ncatbot.utils import get_log

from .source_manage import SourceManageAPIMixin
from .danmu import DanmuAPIMixin
from .room_manage import RoomManageAPIMixin
from .session import SessionAPIMixin
from .comment import CommentAPIMixin
from .query import QueryAPIMixin

if TYPE_CHECKING:
    from bilibili_api.live import LiveRoom
    from ncatbot.adapter.bilibili.source.manager import SourceManager

LOG = get_log("BiliBotAPI")


class BiliBotAPI(
    SourceManageAPIMixin,
    DanmuAPIMixin,
    RoomManageAPIMixin,
    SessionAPIMixin,
    CommentAPIMixin,
    QueryAPIMixin,
    IBiliAPIClient,
):
    """Bilibili 平台 IBiliAPIClient 实现"""

    @property
    def platform(self) -> str:
        return "bilibili"

    def __init__(
        self,
        credential: Any,
        source_manager: "SourceManager",
    ) -> None:
        self._credential = credential
        self._source_manager = source_manager
        self._rooms: Dict[int, "LiveRoom"] = {}

    async def call(self, action: str, params: Optional[dict] = None) -> Any:
        """通用 API 调用入口 — 按 action 名分派到对应方法"""
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"未知的 API action: {action}")
        if params:
            return await method(**params)
        return await method()
