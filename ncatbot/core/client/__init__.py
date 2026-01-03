"""
Client 模块

提供 Bot 客户端及相关组件。
"""

from .ncatbot_event import NcatBotEvent, NcatBotEventFactory
from .event_bus import EventBus, HandlerTimeoutError
from .dispatcher import EventDispatcher, parse_event_type
from .registry import EventRegistry
from .lifecycle import LifecycleManager, StartArgs, LEGAL_ARGS
from .client import BotClient

from ..event.enums import EventType

__all__ = [
    # 核心类
    "BotClient",
    "EventBus",
    "EventDispatcher",
    "EventRegistry",
    "LifecycleManager",
    # 事件
    "NcatBotEvent",
    "NcatBotEventFactory",
    "HandlerTimeoutError",
    # 类型定义
    "StartArgs",
    "LEGAL_ARGS",
    # 事件类型
    "EventType",
    "parse_event_type",
]
