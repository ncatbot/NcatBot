"""
OneBot 11 事件系统

提供完整的 OneBot 11 标准事件解析和处理功能。
"""

from .message_segments import *  # noqa: F401,F403 - 消息段类型
from .parser import EventParser  # noqa: F401
from .models import *  # noqa: F401,F403 - 数据模型
from .enums import *  # noqa: F401,F403 - 枚举类型
from .events import *  # noqa: F401,F403 - 事件类

# 兼容别名 (Pylance: re-export for type checking)
from .message_segments import Text as PlainText  # noqa: F401
from .events import MessageEvent as BaseMessageEvent  # noqa: F401
from .events import MessageEvent as MessageSentEvent  # noqa: F401

__all__ = [
    # 解析器
    "EventParser",
    # 消息段 (from message_segments)
    "MessageSegment", "MessageArray", "Text", "PlainText", "At", "AtAll",
    "Face", "Reply", "Image", "Record", "Video", "File", "Node", "Forward",
    "Share", "Location", "Music", "Json", "Markdown",
    # 模型 (from models)
    "GroupSender", "BaseSender", "Anonymous", "FileInfo", "Status",
    # 枚举 (from enums)
    "PostType", "MessageType", "NoticeType", "RequestType",
    "MetaEventType", "NotifySubType", "EventType",
    # 事件类 (from events)
    "BaseEvent", "MessageEvent", "BaseMessageEvent", "MessageSentEvent",
    "PrivateMessageEvent", "GroupMessageEvent",
    "NoticeEvent", "GroupUploadNoticeEvent", "GroupAdminNoticeEvent",
    "GroupDecreaseNoticeEvent", "GroupIncreaseNoticeEvent", "GroupBanNoticeEvent",
    "FriendAddNoticeEvent", "GroupRecallNoticeEvent", "FriendRecallNoticeEvent",
    "NotifyEvent", "PokeNotifyEvent", "LuckyKingNotifyEvent", "HonorNotifyEvent",
    "RequestEvent", "FriendRequestEvent", "GroupRequestEvent",
    "MetaEvent", "LifecycleMetaEvent", "HeartbeatMetaEvent",
]


