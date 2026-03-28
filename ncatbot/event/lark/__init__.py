"""飞书平台专用事件实体"""

from .message import LarkMessageEvent, LarkGroupMessageEvent, LarkPrivateMessageEvent
from .notice import LarkMessageReadEvent, LarkMessageRecalledEvent
from .factory import create_lark_entity

# 自动注册飞书平台工厂和 secondary keys 到通用工厂
from ..common.factory import (
    register_platform_factory as _register,
    register_platform_secondary_keys as _register_keys,
)

_register("lark", create_lark_entity)
_register_keys(
    "lark",
    {
        "message": "message_type",
        "notice": "notice_type",
    },
)
del _register, _register_keys

__all__ = [
    "LarkMessageEvent",
    "LarkGroupMessageEvent",
    "LarkPrivateMessageEvent",
    "LarkMessageReadEvent",
    "LarkMessageRecalledEvent",
    "create_lark_entity",
]
