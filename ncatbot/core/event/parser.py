from typing import Dict, Type, Tuple, Any, Union
from enum import Enum
from .events import *
from .enums import *
from .context import IBotAPI

class EventParser:
    """
    事件分发器
    """
    # Key: (PostType, SecondaryKey)
    _registry: Dict[Tuple[str, str], Type[BaseEvent]] = {}

    @classmethod
    def register(cls, post_type: Union[PostType, str], secondary_key: str):
        """装饰器注册"""
        def wrapper(event_cls):
            p_val = post_type.value if isinstance(post_type, Enum) else post_type
            cls._registry[(p_val, secondary_key)] = event_cls
            return event_cls
        return wrapper

    @staticmethod
    def _get_secondary_key(data: Dict[str, Any]) -> str:
        """
        根据数据特征提取二级索引 Key
        """
        pt = data.get("post_type")
        
        if pt == PostType.MESSAGE:
            return str(data.get("message_type") or "") # private / group
        
        elif pt == PostType.REQUEST:
            return str(data.get("request_type") or "") # friend / group
        
        elif pt == PostType.META_EVENT:
            return str(data.get("meta_event_type") or "") # lifecycle / heartbeat
        
        elif pt == PostType.NOTICE:
            n_type = data.get("notice_type")
            # 特殊处理 notify 类型，因为它们共享 notice_type 但 sub_type 不同
            if n_type == NoticeType.NOTIFY:
                return str(data.get("sub_type") or "") # poke / lucky_king / honor
            return str(n_type or "") # group_upload / group_decrease ...
            
        return "default"

    @classmethod
    def parse(cls, data: Dict[str, Any], api_instance: IBotAPI) -> BaseEvent:
        post_type = data.get("post_type")
        if not post_type:
            raise ValueError("Data missing 'post_type'")

        sec_key = cls._get_secondary_key(data)
        
        # 1. 查找注册的类
        event_cls = cls._registry.get((post_type, sec_key))
        
        # 2. 如果未找到具体的类，尝试降级处理或抛出
        if not event_cls:
            # 你可以在这里返回一个 GenericEvent 用于调试
            raise ValueError(f"Unknown event type: {post_type} -> {sec_key}")

        # 3. 实例化并注入 API
        try:
            event = event_cls(**data)
            event.bind_api(api_instance)
            return event
        except Exception as e:
            raise ValueError(f"Event parsing failed for {event_cls.__name__}: {e}")

# --- 初始化注册表 ---
# 建议放在 __init__.py 或显式调用 setup()

def register_builtin_events():
    # Message
    EventParser.register(PostType.MESSAGE, MessageType.PRIVATE)(PrivateMessageEvent)
    EventParser.register(PostType.MESSAGE, MessageType.GROUP)(GroupMessageEvent)
    
    # Request
    EventParser.register(PostType.REQUEST, RequestType.FRIEND)(FriendRequestEvent)
    EventParser.register(PostType.REQUEST, RequestType.GROUP)(GroupRequestEvent)
    
    # Meta
    EventParser.register(PostType.META_EVENT, MetaEventType.LIFECYCLE)(LifecycleMetaEvent)
    EventParser.register(PostType.META_EVENT, MetaEventType.HEARTBEAT)(HeartbeatMetaEvent)
    
    # Notice - Standard
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_UPLOAD)(GroupUploadNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_ADMIN)(GroupAdminNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_DECREASE)(GroupDecreaseNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_INCREASE)(GroupIncreaseNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_BAN)(GroupBanNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.FRIEND_ADD)(FriendAddNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.GROUP_RECALL)(GroupRecallNoticeEvent)
    EventParser.register(PostType.NOTICE, NoticeType.FRIEND_RECALL)(FriendRecallNoticeEvent)
    
    # Notice - Notify Subtypes
    EventParser.register(PostType.NOTICE, NotifySubType.POKE)(PokeNotifyEvent)
    EventParser.register(PostType.NOTICE, NotifySubType.LUCKY_KING)(LuckyKingNotifyEvent)
    EventParser.register(PostType.NOTICE, NotifySubType.HONOR)(HonorNotifyEvent)

# 执行注册
register_builtin_events()