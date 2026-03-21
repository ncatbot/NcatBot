"""Bilibili 平台事件工厂"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

from ncatbot.types.common.base import BaseEventData
from ncatbot.types.bilibili.enums import BiliPostType
from ncatbot.types.bilibili.events import (
    DanmuMsgEventData,
    SuperChatEventData,
    GiftEventData,
    GuardBuyEventData,
    InteractEventData,
    LikeEventData,
    BiliPrivateMessageEventData,
    BiliPrivateMessageWithdrawEventData,
    BiliCommentEventData,
    BiliDynamicEventData,
)
from ncatbot.event.common.base import BaseEvent
from .live import (
    BiliLiveEvent,
    DanmuMsgEvent,
    SuperChatEvent,
    GiftEvent,
    GuardBuyEvent,
    InteractEvent,
    LikeEvent,
)
from .session import BiliPrivateMessageEvent, BiliPrivateMessageWithdrawEvent
from .comment import BiliCommentEvent
from .dynamic import BiliDynamicEvent

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient

__all__ = [
    "create_bili_entity",
]

# 精确映射：数据模型类 → 实体类
_BILI_ENTITY_MAP: Dict[Type[BaseEventData], Type[BaseEvent]] = {
    DanmuMsgEventData: DanmuMsgEvent,
    SuperChatEventData: SuperChatEvent,
    GiftEventData: GiftEvent,
    GuardBuyEventData: GuardBuyEvent,
    InteractEventData: InteractEvent,
    LikeEventData: LikeEvent,
    BiliPrivateMessageEventData: BiliPrivateMessageEvent,
    BiliPrivateMessageWithdrawEventData: BiliPrivateMessageWithdrawEvent,
    BiliCommentEventData: BiliCommentEvent,
    BiliDynamicEventData: BiliDynamicEvent,
}

# post_type → 降级实体基类
_BILI_FALLBACK_MAP: Dict[str, Type[BaseEvent]] = {
    BiliPostType.LIVE: BiliLiveEvent,
    BiliPostType.MESSAGE: BaseEvent,
    BiliPostType.COMMENT: BaseEvent,
    BiliPostType.DYNAMIC: BaseEvent,
    BiliPostType.SYSTEM: BaseEvent,
}


def create_bili_entity(data: BaseEventData, api: "IAPIClient") -> Optional[BaseEvent]:
    """Bilibili 平台事件工厂"""
    entity_cls = _BILI_ENTITY_MAP.get(type(data))
    if entity_cls is None:
        entity_cls = _BILI_FALLBACK_MAP.get(data.post_type)
    if entity_cls is None:
        return None
    return entity_cls(data, api)
