"""QQ 平台事件工厂"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

from ncatbot.types import BaseEventData
from ncatbot.types.qq import (
    PostType,
    GroupMessageEventData,
    PrivateMessageEventData,
    GroupUploadNoticeEventData,
    GroupAdminNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupIncreaseNoticeEventData,
    GroupBanNoticeEventData,
    FriendAddNoticeEventData,
    GroupRecallNoticeEventData,
    FriendRecallNoticeEventData,
    GroupMsgEmojiLikeNoticeEventData,
    FriendRequestEventData,
    GroupRequestEventData,
)
from ncatbot.types.qq import (
    NotifyEventData,
    PokeNotifyEventData,
    LuckyKingNotifyEventData,
    HonorNotifyEventData,
)

from ..common.base import BaseEvent
from .message import MessageEvent, GroupMessageEvent, PrivateMessageEvent
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
from .request import FriendRequestEvent, GroupRequestEvent, RequestEvent
from .meta import MetaEvent

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient

__all__ = [
    "create_qq_entity",
]

# 精确映射：数据模型类 → 实体类
_QQ_ENTITY_MAP: Dict[Type[BaseEventData], Type[BaseEvent]] = {
    # Message
    PrivateMessageEventData: PrivateMessageEvent,
    GroupMessageEventData: GroupMessageEvent,
    # Request
    FriendRequestEventData: FriendRequestEvent,
    GroupRequestEventData: GroupRequestEvent,
    # Notice
    GroupUploadNoticeEventData: GroupUploadEvent,
    GroupAdminNoticeEventData: GroupAdminEvent,
    GroupDecreaseNoticeEventData: GroupDecreaseEvent,
    GroupIncreaseNoticeEventData: GroupIncreaseEvent,
    GroupBanNoticeEventData: GroupBanEvent,
    FriendAddNoticeEventData: FriendAddEvent,
    GroupRecallNoticeEventData: GroupRecallEvent,
    FriendRecallNoticeEventData: FriendRecallEvent,
    GroupMsgEmojiLikeNoticeEventData: GroupMsgEmojiLikeEvent,
    # Notify (基类映射 + 具体子类映射)
    NotifyEventData: NotifyEvent,
    PokeNotifyEventData: PokeNotifyEvent,
    LuckyKingNotifyEventData: LuckyKingNotifyEvent,
    HonorNotifyEventData: HonorNotifyEvent,
}

# post_type → 降级实体基类
_QQ_FALLBACK_MAP: Dict[str, Type[BaseEvent]] = {
    PostType.MESSAGE: MessageEvent,
    PostType.MESSAGE_SENT: MessageEvent,
    PostType.NOTICE: NoticeEvent,
    PostType.REQUEST: RequestEvent,
    PostType.META_EVENT: MetaEvent,
}


def create_qq_entity(data: BaseEventData, api: "IAPIClient") -> Optional[BaseEvent]:
    """QQ 平台事件工厂"""
    entity_cls = _QQ_ENTITY_MAP.get(type(data))
    if entity_cls is None:
        entity_cls = _QQ_FALLBACK_MAP.get(data.post_type)
    if entity_cls is None:
        return None
    return entity_cls(data, api)
