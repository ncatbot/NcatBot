"""
NcatBot 核心模块

提供 Bot 客户端、事件系统和 API 接口。
"""

from .client import BotClient, EventBus, NcatBotEvent, EventType  # noqa: F401
from .helper import ForwardConstructor  # noqa: F401

# 事件类型 (from event submodule)
from .event import (  # noqa: F401
    # 基础事件
    BaseEvent, MessageEvent, PrivateMessageEvent, GroupMessageEvent,
    NoticeEvent, RequestEvent, MetaEvent,
    # 消息段
    MessageArray, MessageSegment, Text, At, Image, Face, Reply,
    File, Record, Video, Node, Forward,
)

# 兼容别名 (Pylance: re-export for type checking)
from .event import MessageEvent as BaseMessageEvent  # noqa: F401
from .event import MessageEvent as MessageSentEvent  # noqa: F401

__all__ = [
    # 核心
    "BotClient", "EventBus", "NcatBotEvent", "ForwardConstructor", "EventType",
    # 事件
    "BaseEvent", "MessageEvent", "BaseMessageEvent", "MessageSentEvent",
    "PrivateMessageEvent", "GroupMessageEvent", "NoticeEvent", "RequestEvent", "MetaEvent",
    # 消息段
    "MessageArray", "MessageSegment", "Text", "At", "Image", "Face", "Reply",
    "File", "Record", "Video", "Node", "Forward",
]
