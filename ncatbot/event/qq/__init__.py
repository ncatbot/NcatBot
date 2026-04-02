"""QQ 平台专用事件实体"""

from .message import MessageEvent, PrivateMessageEvent, GroupMessageEvent
from .notice import (
    NoticeEvent,
    GroupUploadEvent,
    GroupAdminEvent,
    GroupDecreaseEvent,
    GroupIncreaseEvent,
    GroupBanEvent,
    FriendAddEvent,
    GroupRecallEvent,
    FriendRecallEvent,
    GroupMsgEmojiLikeEvent,
    NotifyEvent,
    PokeNotifyEvent,
    LuckyKingNotifyEvent,
    HonorNotifyEvent,
)
from .request import RequestEvent, FriendRequestEvent, GroupRequestEvent
from .meta import MetaEvent
from .factory import create_qq_entity

# 自动注册 QQ 平台工厂和 secondary keys 到通用工厂
from ..common.factory import (
    register_platform_factory as _register,
    register_platform_secondary_keys as _register_keys,
)

_register("qq", create_qq_entity)
_register_keys(
    "qq",
    {
        "message": "message_type",
        "message_sent": "message_type",
        "notice": "notice_type",
        "request": "request_type",
        "meta_event": "meta_event_type",
    },
)
del _register, _register_keys

__all__ = [
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "GroupUploadEvent",
    "GroupAdminEvent",
    "GroupDecreaseEvent",
    "GroupIncreaseEvent",
    "GroupBanEvent",
    "FriendAddEvent",
    "GroupRecallEvent",
    "FriendRecallEvent",
    "GroupMsgEmojiLikeEvent",
    "NotifyEvent",
    "PokeNotifyEvent",
    "LuckyKingNotifyEvent",
    "HonorNotifyEvent",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "MetaEvent",
    "create_qq_entity",
]
