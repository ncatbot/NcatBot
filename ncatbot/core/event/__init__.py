"""
OneBot 11 事件系统

提供完整的 OneBot 11 标准事件解析和处理功能。
"""

from . import message_segments  # noqa: F401
from . import models  # noqa: F401
from . import enums  # noqa: F401
from . import events  # noqa: F401

from .message_segments import *  # noqa: F401,F403 - 消息段类型
from .parser import EventParser  # noqa: F401
from .models import *  # noqa: F401,F403 - 数据模型
from .enums import *  # noqa: F401,F403 - 枚举类型
from .events import *  # noqa: F401,F403 - 事件类

# 兼容别名 (Pylance: re-export for type checking)
from .events import MessageEvent as MessageSentEvent  # noqa: F401

__all__ = [
    # 解析器
    "EventParser",
    "MessageSentEvent",
]

__all__.extend(getattr(message_segments, "__all__", []))
__all__.extend(getattr(models, "__all__", []))
__all__.extend(getattr(enums, "__all__", []))
__all__.extend(getattr(events, "__all__", []))
