"""飞书通知事件实体（已读 / 撤回）"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from ..common.base import BaseEvent

if TYPE_CHECKING:
    from ncatbot.adapter.lark.api import LarkBotAPI
    from ncatbot.types.lark.events import (
        LarkMessageReadEventData,
        LarkMessageRecalledEventData,
    )

__all__ = [
    "LarkMessageReadEvent",
    "LarkMessageRecalledEvent",
]


class LarkMessageReadEvent(BaseEvent):
    """飞书消息已读事件"""

    _data: "LarkMessageReadEventData"
    _api: "LarkBotAPI"

    @property
    def api(self) -> "LarkBotAPI":
        return self._api

    @property
    def message_id_list(self) -> List[str]:
        return self._data.message_id_list

    @property
    def reader_open_id(self) -> str:
        return self._data.reader_open_id

    @property
    def reader_union_id(self) -> str:
        return self._data.reader_union_id

    @property
    def read_time(self) -> str:
        return self._data.read_time

    @property
    def tenant_key(self) -> str:
        return self._data.tenant_key


class LarkMessageRecalledEvent(BaseEvent):
    """飞书消息撤回事件"""

    _data: "LarkMessageRecalledEventData"
    _api: "LarkBotAPI"

    @property
    def api(self) -> "LarkBotAPI":
        return self._api

    @property
    def message_id(self) -> str:
        return self._data.message_id

    @property
    def chat_id(self) -> str:
        return self._data.chat_id

    @property
    def recall_time(self) -> str:
        return self._data.recall_time

    @property
    def recall_type(self) -> str:
        return self._data.recall_type
