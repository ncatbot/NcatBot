"""NapCat 事件解析

将 OB11 原始 JSON 转换为 BaseEventData 数据模型。
只产出纯数据模型，不创建实体。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Type

from ncatbot.types import (
    BaseEventData,
    FriendRequestEventData,
    GroupMessageEventData,
    GroupRequestEventData,
    HeartbeatMetaEventData,
    LifecycleMetaEventData,
    MetaEventType,
    MessageType,
    NoticeType,
    NotifySubType,
    PostType,
    PrivateMessageEventData,
    RequestType,
    # notice
    FriendAddNoticeEventData,
    FriendRecallNoticeEventData,
    GroupAdminNoticeEventData,
    GroupBanNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupIncreaseNoticeEventData,
    GroupRecallNoticeEventData,
    GroupUploadNoticeEventData,
    HonorNotifyEventData,
    LuckyKingNotifyEventData,
    PokeNotifyEventData,
)
from ncatbot.utils import get_log

LOG = get_log("NapCatEventParser")


class EventParser:
    """事件解析器 — dict → types/ 数据模型

    使用 (post_type, secondary_key) 二元组管理注册表。
    """

    _registry: Dict[Tuple[str, str], Type[BaseEventData]] = {}

    @classmethod
    def register(cls, post_type: str, secondary_key: str = "") -> Any:
        def wrapper(data_cls: Type[BaseEventData]) -> Type[BaseEventData]:
            cls._registry[(post_type, secondary_key)] = data_cls
            return data_cls

        return wrapper

    @classmethod
    def _get_key(cls, data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        post_type = data.get("post_type", "")

        if post_type in (PostType.MESSAGE, "message_sent"):
            return (PostType.MESSAGE, data.get("message_type", ""))

        if post_type == PostType.NOTICE:
            notice_type = data.get("notice_type", "")
            if notice_type == NoticeType.NOTIFY:
                return (PostType.NOTICE, data.get("sub_type", ""))
            return (PostType.NOTICE, notice_type)

        if post_type == PostType.REQUEST:
            return (PostType.REQUEST, data.get("request_type", ""))

        if post_type == PostType.META_EVENT:
            return (PostType.META_EVENT, data.get("meta_event_type", ""))

        return None

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> BaseEventData:
        """解析 raw dict → 数据模型实例"""
        key = cls._get_key(data)
        if not key:
            raise ValueError(f"Unknown event: post_type={data.get('post_type')}")
        data_cls = cls._registry.get(key)
        if not data_cls:
            raise ValueError(f"No data class registered for {key}")
        return data_cls.model_validate(data)


def _register_builtin() -> None:
    """注册内置事件数据模型"""
    r = EventParser.register

    # Message
    r(PostType.MESSAGE, MessageType.PRIVATE)(PrivateMessageEventData)
    r(PostType.MESSAGE, MessageType.GROUP)(GroupMessageEventData)

    # Request
    r(PostType.REQUEST, RequestType.FRIEND)(FriendRequestEventData)
    r(PostType.REQUEST, RequestType.GROUP)(GroupRequestEventData)

    # Meta
    r(PostType.META_EVENT, MetaEventType.LIFECYCLE)(LifecycleMetaEventData)
    r(PostType.META_EVENT, MetaEventType.HEARTBEAT)(HeartbeatMetaEventData)

    # Notice
    r(PostType.NOTICE, NoticeType.GROUP_UPLOAD)(GroupUploadNoticeEventData)
    r(PostType.NOTICE, NoticeType.GROUP_ADMIN)(GroupAdminNoticeEventData)
    r(PostType.NOTICE, NoticeType.GROUP_DECREASE)(GroupDecreaseNoticeEventData)
    r(PostType.NOTICE, NoticeType.GROUP_INCREASE)(GroupIncreaseNoticeEventData)
    r(PostType.NOTICE, NoticeType.GROUP_BAN)(GroupBanNoticeEventData)
    r(PostType.NOTICE, NoticeType.FRIEND_ADD)(FriendAddNoticeEventData)
    r(PostType.NOTICE, NoticeType.GROUP_RECALL)(GroupRecallNoticeEventData)
    r(PostType.NOTICE, NoticeType.FRIEND_RECALL)(FriendRecallNoticeEventData)

    # Notice - Notify
    r(PostType.NOTICE, NotifySubType.POKE)(PokeNotifyEventData)
    r(PostType.NOTICE, NotifySubType.LUCKY_KING)(LuckyKingNotifyEventData)
    r(PostType.NOTICE, NotifySubType.HONOR)(HonorNotifyEventData)


_register_builtin()


class NapCatEventParser:
    """将 OB11 原始 JSON 转换为 BaseEventData"""

    def parse(self, raw_data: dict) -> Optional[BaseEventData]:
        if "post_type" not in raw_data:
            return None
        try:
            return EventParser.parse(raw_data)
        except ValueError as e:
            LOG.debug(f"事件解析跳过: {e}")
            return None
        except Exception as e:
            LOG.warning(f"事件解析失败: {e}")
            return None
