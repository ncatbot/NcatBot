"""QQ 平台专用枚举"""

from enum import Enum, IntEnum

__all__ = [
    "OnlineStatus",
    "PostType",
    "MessageType",
    "NoticeType",
    "NoticeNotifySubType",
    "GroupAdminSubType",
    "GroupDecreaseSubType",
    "GroupIncreaseSubType",
    "GroupBanSubType",
    "RequestType",
    "MetaEventType",
    "EventType",
]


class OnlineStatus(IntEnum):
    """QQ 基础在线状态，用于 ``set_online_status`` 的 ``status`` 参数。

    扩展状态仍通过 ``ext_status`` 指定；接口也接受普通整数。
    """

    ONLINE = 10
    Q_ME = 60
    AWAY = 30
    BUSY = 50
    DO_NOT_DISTURB = 70
    INVISIBLE = 40


class PostType(str, Enum):
    MESSAGE = "message"
    MESSAGE_SENT = "message_sent"
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
    GROUP_MSG_EMOJI_LIKE = "group_msg_emoji_like"
    NOTIFY = "notify"


class GroupAdminSubType(str, Enum):
    SET = "set"
    UNSET = "unset"


class GroupDecreaseSubType(str, Enum):
    LEAVE = "leave"
    KICK = "kick"
    KICK_ME = "kick_me"


class GroupIncreaseSubType(str, Enum):
    APPROVE = "approve"
    INVITE = "invite"


class GroupBanSubType(str, Enum):
    BAN = "ban"
    LIFT_BAN = "lift_ban"


class NoticeNotifySubType(str, Enum):
    POKE = "poke"
    LUCKY_KING = "lucky_king"
    HONOR = "honor"


class RequestType(str, Enum):
    FRIEND = "friend"
    GROUP = "group"


class MetaEventType(str, Enum):
    LIFECYCLE = "lifecycle"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_TIMEOUT = "heartbeat_timeout"


class EventType(str, Enum):
    MESSAGE = "message_event"
    MESSAGE_SENT = "message_sent_event"
    NOTICE = "notice_event"
    REQUEST = "request_event"
    META = "meta_event"
