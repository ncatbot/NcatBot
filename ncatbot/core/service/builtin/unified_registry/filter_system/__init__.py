"""过滤器系统 v2.0

全新设计的过滤器系统：
- 过滤器函数只接受 event 参数
- 支持过滤器实例直接应用到命令
- 统一注册管理
"""

from .registry import filter_registry
from .event_registry import event_registry
from .base import *  # noqa: F403
from .builtin import *  # noqa: F403
from .decorators import *  # noqa: F403
from . import base, builtin, decorators

# 动态构建 __all__
__all__ = ["filter_registry", "event_registry"]
__all__.extend(
    (getattr(base, "__all__", []))
    + (getattr(builtin, "__all__", []))
    + (getattr(decorators, "__all__", []))
)  # type: ignore
