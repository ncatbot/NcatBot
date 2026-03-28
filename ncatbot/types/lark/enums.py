"""飞书平台专用枚举"""

from enum import Enum

__all__ = [
    "LarkPostType",
    "LarkMessageType",
    "LarkNoticeType",
]


class LarkPostType(str, Enum):
    MESSAGE = "message"
    NOTICE = "notice"


class LarkMessageType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


class LarkNoticeType(str, Enum):
    MESSAGE_READ = "message_read"
    MESSAGE_RECALLED = "message_recalled"
