"""事件模块

通用基础设施从此处导入：BaseEvent, create_entity, Mixin traits。
QQ 平台事件从 ncatbot.event.qq 导入。
"""

from .common import (
    BaseEvent,
    create_entity,
    register_platform_factory,
    # mixins
    Approvable,
    Bannable,
    Deletable,
    GroupScoped,
    HasSender,
    Kickable,
    Replyable,
)

# 确保平台工厂被注册
from . import qq as _qq  # noqa: F401
from . import bilibili as _bili  # noqa: F401
from . import github as _gh  # noqa: F401
from . import lark as _lark  # noqa: F401

del _qq
del _bili
del _gh
del _lark

__all__ = [
    # common
    "BaseEvent",
    "create_entity",
    "register_platform_factory",
    # mixins
    "Replyable",
    "Deletable",
    "HasSender",
    "GroupScoped",
    "Kickable",
    "Bannable",
    "Approvable",
]
