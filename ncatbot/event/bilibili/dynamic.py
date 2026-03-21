"""动态事件实体"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ncatbot.event.common.base import BaseEvent
from ncatbot.event.common.mixins import HasSender

if TYPE_CHECKING:
    from ncatbot.api.bilibili import IBiliAPIClient
    from ncatbot.types.bilibili.events import BiliDynamicEventData

__all__ = [
    "BiliDynamicEvent",
]


class BiliDynamicEvent(BaseEvent, HasSender):
    """B 站动态事件"""

    _data: "BiliDynamicEventData"
    _api: "IBiliAPIClient"

    @property
    def api(self) -> "IBiliAPIClient":
        return self._api

    @property
    def user_id(self) -> str:
        return self._data.uid

    @property
    def sender(self) -> Any:
        return self._data.sender

    @property
    def dynamic_id(self) -> str:
        return self._data.dynamic_id

    @property
    def dynamic_type(self) -> str:
        return self._data.dynamic_type

    @property
    def text(self) -> str | None:
        return self._data.text
