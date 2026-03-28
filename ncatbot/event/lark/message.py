"""飞书消息事件实体"""

from __future__ import annotations

from typing import Any, Union, TYPE_CHECKING

from ..common.base import BaseEvent
from ..common.mixins import Replyable, HasSender

if TYPE_CHECKING:
    from ncatbot.adapter.lark.api import LarkBotAPI
    from ncatbot.types import MessageArray
    from ncatbot.types.lark.events import (
        LarkMessageEventData,
        LarkGroupMessageEventData,
        LarkPrivateMessageEventData,
    )

__all__ = [
    "LarkMessageEvent",
    "LarkGroupMessageEvent",
    "LarkPrivateMessageEvent",
]


class LarkMessageEvent(BaseEvent, Replyable, HasSender):
    """飞书消息事件基类"""

    _data: "LarkMessageEventData"
    _api: "LarkBotAPI"

    @property
    def api(self) -> "LarkBotAPI":
        return self._api

    @property
    def user_id(self) -> str:
        return self._data.user_id

    @property
    def sender(self) -> Any:
        return self._data.sender

    @property
    def message_id(self) -> str:
        return self._data.message_id

    @property
    def content(self) -> str:
        return self._data.content

    @property
    def chat_id(self) -> str:
        return self._data.chat_id

    async def post_message(
        self, content: Union[str, "MessageArray"], title: str = ""
    ) -> Any:
        """主动发送消息到当前会话（非引用回复）

        Args:
            content: 文本字符串或 MessageArray
            title: 富文本标题（仅 MessageArray 含非文本段时生效）
        """
        if isinstance(content, str):
            return await self._api.send_text(
                receive_id=self._data.chat_id,
                text=content,
                receive_id_type="chat_id",
            )
        return await self._api.send_msg_array(
            receive_id=self._data.chat_id,
            msg=content,
            title=title,
            receive_id_type="chat_id",
        )

    async def reply(
        self, content: Union[str, "MessageArray"] = "", title: str = "", **kwargs: Any
    ) -> Any:
        """引用回复原消息

        Args:
            content: 文本字符串或 MessageArray
            title: 富文本标题（仅 MessageArray 含非文本段时生效）
        """
        if isinstance(content, str):
            return await self._api.reply_text(
                message_id=self._data.message_id,
                text=content,
            )
        return await self._api.reply_msg_array(
            message_id=self._data.message_id,
            msg=content,
            title=title,
        )


class LarkGroupMessageEvent(LarkMessageEvent):
    """飞书群消息事件"""

    _data: "LarkGroupMessageEventData"

    @property
    def group_id(self) -> str:
        return self._data.chat_id


class LarkPrivateMessageEvent(LarkMessageEvent):
    """飞书私聊消息事件"""

    _data: "LarkPrivateMessageEventData"

    async def post_message(
        self, content: Union[str, "MessageArray"], title: str = ""
    ) -> Any:
        """主动发送消息给用户（非引用回复）"""
        if isinstance(content, str):
            return await self._api.send_text(
                receive_id=self._data.user_id,
                text=content,
                receive_id_type="open_id",
            )
        return await self._api.send_msg_array(
            receive_id=self._data.user_id,
            msg=content,
            title=title,
            receive_id_type="open_id",
        )
