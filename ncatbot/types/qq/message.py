"""QQ 平台消息事件数据模型"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import Field, field_validator

from ..common.base import BaseEventData
from ..common.segment.array import MessageArray
from .enums import PostType, MessageType
from .misc import Anonymous
from .sender import QQSender, GroupSender

__all__ = [
    "MessageEventData",
    "PrivateMessageEventData",
    "GroupMessageEventData",
]


class MessageEventData(BaseEventData):
    platform: str = "qq"
    post_type: PostType = Field(default=PostType.MESSAGE)
    message_type: MessageType
    sub_type: str
    message_id: str
    user_id: str
    message: MessageArray
    raw_message: str
    sender: QQSender
    font: int = 0

    @field_validator("message", mode="before")
    @classmethod
    def _convert_message(cls, v: Any) -> MessageArray:
        if isinstance(v, list):
            return MessageArray.from_list(v)
        if isinstance(v, MessageArray):
            return v
        return MessageArray.from_any(v)


class PrivateMessageEventData(MessageEventData):
    message_type: MessageType = Field(default=MessageType.PRIVATE)
    sub_type: str = Field(default="friend")
    sender: QQSender


class GroupMessageEventData(MessageEventData):
    message_type: MessageType = Field(default=MessageType.GROUP)
    sub_type: str = Field(default="normal")
    group_id: str
    group_name: Optional[str] = None
    anonymous: Optional[Anonymous] = None
    sender: GroupSender
