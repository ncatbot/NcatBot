# enums.py
from enum import Enum

class PostType(str, Enum):
    MESSAGE = "message"
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