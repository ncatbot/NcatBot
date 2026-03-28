"""飞书平台事件数据模型"""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from ..common.base import BaseEventData
from ..common.segment.array import MessageArray
from .enums import LarkPostType, LarkMessageType, LarkNoticeType
from .sender import LarkSender

__all__ = [
    "LarkMessageEventData",
    "LarkGroupMessageEventData",
    "LarkPrivateMessageEventData",
    "LarkMessageReadEventData",
    "LarkMessageRecalledEventData",
]


class LarkMessageEventData(BaseEventData):
    """飞书消息事件基类"""

    platform: str = "lark"
    post_type: str = LarkPostType.MESSAGE
    message_type: str = ""
    message_id: str = ""
    chat_id: str = ""
    chat_type: str = ""
    content: str = ""
    message: MessageArray = Field(default_factory=MessageArray)
    sender: Optional[LarkSender] = None
    user_id: str = ""


class LarkGroupMessageEventData(LarkMessageEventData):
    """飞书群消息事件"""

    message_type: str = LarkMessageType.GROUP
    chat_id: str = ""
    group_id: str = ""


class LarkPrivateMessageEventData(LarkMessageEventData):
    """飞书私聊消息事件"""

    message_type: str = LarkMessageType.PRIVATE


# ---- 通知事件 ----


class LarkMessageReadEventData(BaseEventData):
    """飞书消息已读事件"""

    platform: str = "lark"
    post_type: str = LarkPostType.NOTICE
    notice_type: str = LarkNoticeType.MESSAGE_READ
    message_id_list: List[str] = Field(default_factory=list)
    reader_open_id: str = ""
    reader_union_id: str = ""
    reader_user_id: str = ""
    read_time: str = ""
    tenant_key: str = ""


class LarkMessageRecalledEventData(BaseEventData):
    """飞书消息撤回事件"""

    platform: str = "lark"
    post_type: str = LarkPostType.NOTICE
    notice_type: str = LarkNoticeType.MESSAGE_RECALLED
    message_id: str = ""
    chat_id: str = ""
    recall_time: str = ""
    recall_type: str = ""
