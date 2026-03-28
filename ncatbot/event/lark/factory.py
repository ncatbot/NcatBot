"""飞书平台事件工厂"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

from ncatbot.types import BaseEventData
from ncatbot.types.lark import (
    LarkGroupMessageEventData,
    LarkPrivateMessageEventData,
    LarkMessageReadEventData,
    LarkMessageRecalledEventData,
)
from ..common.base import BaseEvent
from .message import (
    LarkMessageEvent,
    LarkGroupMessageEvent,
    LarkPrivateMessageEvent,
)
from .notice import (
    LarkMessageReadEvent,
    LarkMessageRecalledEvent,
)

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient

__all__ = [
    "create_lark_entity",
]

# 精确映射：数据模型类 → 实体类
_LARK_ENTITY_MAP: Dict[Type[BaseEventData], Type[BaseEvent]] = {
    LarkGroupMessageEventData: LarkGroupMessageEvent,
    LarkPrivateMessageEventData: LarkPrivateMessageEvent,
    LarkMessageReadEventData: LarkMessageReadEvent,
    LarkMessageRecalledEventData: LarkMessageRecalledEvent,
}


def create_lark_entity(data: BaseEventData, api: "IAPIClient") -> Optional[BaseEvent]:
    """飞书平台事件工厂"""
    entity_cls = _LARK_ENTITY_MAP.get(type(data))
    if entity_cls is None:
        entity_cls = LarkMessageEvent
    return entity_cls(data, api)
