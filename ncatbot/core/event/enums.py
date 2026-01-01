# enums.py
from enum import Enum

__all__ = [
    "PostType", "MessageType", "NoticeType", "NotifySubType",
    "RequestType", "MetaEventType", "EventType"
]

class PostType(str, Enum):
    MESSAGE = "message"
    MESSAGE_SENT = "message_sent"  # 自己发送的消息
    NOTICE = "notice"
    REQUEST = "request"
    META_EVENT = "meta_event"

class MessageType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"

class NoticeType(str, Enum):
    GROUP_UPLOAD = "group_upload"
    GROUP_ADMIN = "group_admin"
    GROUP_DECREASE = "group_decrease"
    GROUP_INCREASE = "group_increase"
    GROUP_BAN = "group_ban"
    FRIEND_ADD = "friend_add"
    GROUP_RECALL = "group_recall"
    FRIEND_RECALL = "friend_recall"
    NOTIFY = "notify"

class NotifySubType(str, Enum):
    POKE = "poke"
    LUCKY_KING = "lucky_king"
    HONOR = "honor"

class RequestType(str, Enum):
    FRIEND = "friend"
    GROUP = "group"

class MetaEventType(str, Enum):
    LIFECYCLE = "lifecycle"
    HEARTBEAT = "heartbeat"


class EventType(str, Enum):
    """
    统一的事件类型枚举
    
    简化为四大类事件：消息、通知、请求、元事件
    """
    MESSAGE = "message_event"
    NOTICE = "notice_event"
    REQUEST = "request_event"
    META = "meta_event"