from typing import Dict, Type, Tuple, Any, Optional
from .events import *  # noqa: F403
from .enums import *  # noqa: F403
from .context import IBotAPI


class EventParser:
    """
    事件解析器

    使用 (post_type, secondary_key) 管理事件类型到事件类的映射。
    """

    # Key: (post_type, secondary_key) -> Type[BaseEvent]
    _registry: Dict[Tuple[str, str], Type[BaseEvent]] = {}

    @classmethod
    def register(cls, post_type: str, secondary_key: str = ""):
        """
        装饰器注册事件类

        Args:
            post_type: 主事件类型 (message, notice, request, meta_event)
            secondary_key: 次级键 (message_type, notice_type, request_type, meta_event_type 等)
        """

        def wrapper(event_cls: Type[BaseEvent]) -> Type[BaseEvent]:
            cls._registry[(post_type, secondary_key)] = event_cls
            return event_cls

        return wrapper

    @classmethod
    def _get_registry_key(cls, data: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        从原始数据获取注册表查找键

        Args:
            data: OneBot 原始事件数据

        Returns:
            (post_type, secondary_key) 元组
        """
        post_type = data.get("post_type", "")

        if post_type == PostType.MESSAGE or post_type == "message_sent":
            message_type = data.get("message_type", "")
            return (PostType.MESSAGE, message_type)

        if post_type == PostType.NOTICE:
            notice_type = data.get("notice_type", "")
            # notify 子类型需要进一步细分
            if notice_type == NoticeType.NOTIFY:
                sub_type = data.get("sub_type", "")
                return (PostType.NOTICE, sub_type)
            return (PostType.NOTICE, notice_type)

        if post_type == PostType.REQUEST:
            request_type = data.get("request_type", "")
            return (PostType.REQUEST, request_type)

        if post_type == PostType.META_EVENT:
            meta_event_type = data.get("meta_event_type", "")
            return (PostType.META_EVENT, meta_event_type)

        return None

    @classmethod
    def parse(cls, data: Dict[str, Any], api_instance: IBotAPI) -> BaseEvent:
        """
        解析原始事件数据为事件对象

        Args:
            data: OneBot 原始事件数据
            api_instance: API 实例，用于绑定到事件对象

        Returns:
            解析后的事件对象

        Raises:
            ValueError: 无法识别的事件类型或解析失败
        """
        key = cls._get_registry_key(data)
        if not key:
            post_type = data.get("post_type")
            raise ValueError(f"Unknown event type: post_type={post_type}")

        # 查找注册的事件类
        event_cls = cls._registry.get(key)

        if not event_cls:
            raise ValueError(f"No event class registered for {key}")

        # 实例化并注入 API
        try:
            event = event_cls(**data)
            event.bind_api(api_instance)
            return event
        except Exception as e:
            raise ValueError(f"Event parsing failed for {event_cls.__name__}: {e}")


# --- 初始化注册表 ---
def register_builtin_events():
    """注册内置事件类"""
    # Message
    EventParser.register(PostType.MESSAGE, MessageType.PRIVATE)(PrivateMessageEvent)
    EventParser.register(PostType.MESSAGE, MessageType.GROUP)(GroupMessageEvent)

    # Request
    EventParser.register(PostType.REQUEST, RequestType.FRIEND)(FriendRequestEvent)
    EventParser.register(PostType.REQUEST, RequestType.GROUP)(GroupRequestEvent)

    # Meta
    EventParser.register(PostType.META_EVENT, MetaEventType.LIFECYCLE)(
        LifecycleMetaEvent
    )
    EventParser.register(PostType.META_EVENT, MetaEventType.HEARTBEAT)(
        HeartbeatMetaEvent
    )

    # Notice - Standard
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_UPLOAD)(
        GroupUploadNoticeEvent
    )
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_ADMIN)(GroupAdminNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_DECREASE)(
        GroupDecreaseNoticeEvent
    )
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_INCREASE)(
        GroupIncreaseNoticeEvent
    )
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_BAN)(GroupBanNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.FRIEND_ADD)(FriendAddNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_RECALL)(
        GroupRecallNoticeEvent
    )
    EventParser.register(PostType.NOTICE, NoticeType.FRIEND_RECALL)(
        FriendRecallNoticeEvent
    )

    # Notice - Notify Subtypes
    EventParser.register(PostType.NOTICE, NotifySubType.POKE)(PokeNotifyEvent)
    EventParser.register(PostType.NOTICE, NotifySubType.LUCKY_KING)(
        LuckyKingNotifyEvent
    )
    EventParser.register(PostType.NOTICE, NotifySubType.HONOR)(HonorNotifyEvent)


# 执行注册
register_builtin_events()
