"""Bilibili 平台专用事件实体"""

from .live import (
    BiliLiveEvent,
    DanmuMsgEvent,
    SuperChatEvent,
    GiftEvent,
    GuardBuyEvent,
    InteractEvent,
    LikeEvent,
    LiveNoticeEvent,
)
from .session import BiliPrivateMessageEvent, BiliPrivateMessageWithdrawEvent
from .comment import BiliCommentEvent
from .dynamic import BiliDynamicEvent
from .factory import create_bili_entity

# 自动注册 Bilibili 平台工厂和 secondary keys 到通用工厂
from ncatbot.event.common.factory import (
    register_platform_factory as _register,
    register_platform_secondary_keys as _register_keys,
)

_register("bilibili", create_bili_entity)
_register_keys(
    "bilibili",
    {
        "live": "live_event_type",
        "comment": "comment_event_type",
        "dynamic": "dynamic_event_type",
    },
)
del _register, _register_keys

__all__ = [
    # live
    "BiliLiveEvent",
    "DanmuMsgEvent",
    "SuperChatEvent",
    "GiftEvent",
    "GuardBuyEvent",
    "InteractEvent",
    "LikeEvent",
    "LiveNoticeEvent",
    # session
    "BiliPrivateMessageEvent",
    "BiliPrivateMessageWithdrawEvent",
    # comment
    "BiliCommentEvent",
    # dynamic
    "BiliDynamicEvent",
    # factory
    "create_bili_entity",
]
