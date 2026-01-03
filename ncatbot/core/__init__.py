"""
NcatBot 核心模块

提供 Bot 客户端、事件系统和 API 接口。
"""

from .client import BotClient, EventBus, NcatBotEvent, EventType, NcatBotEventFactory
from .helper import ForwardConstructor  # noqa: F401
from .api import BotAPI

# 事件类型 (from event submodule)
from .event import *  # noqa: F401,F403

# 兼容别名 (Pylance: re-export for type checking)
from .event import MessageEvent as MessageSentEvent  # noqa: F401

from . import event

__all__ = [
    # 核心
    "BotAPI",
    "BotClient",
    "EventBus",
    "NcatBotEvent",
    "ForwardConstructor",
    "EventType",
    "MessageSentEvent",
    "NcatBotEventFactory",
]

__all__.extend(getattr(event, "__all__", []))  # type: ignore
