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
import ncatbot.event.qq as _qq  # noqa: F401
import ncatbot.event.bilibili as _bili  # noqa: F401
import ncatbot.event.github as _gh  # noqa: F401

del _qq
del _bili
del _gh

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
