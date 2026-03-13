"""
事件分发器

负责接收事件，分发到 EventBus。
支持两种模式：
1. 接收原始 dict 数据（传统模式）
2. 接收已转换的 BaseEvent 对象（新 Adapter 模式）
"""

import traceback
from typing import TYPE_CHECKING, Optional, Union

from ncatbot.utils import get_log
from ..event.parser import EventParser
from ..event.enums import PostType, EventType
from ..event.events import BaseEvent

if TYPE_CHECKING:
    from .event_bus import EventBus
    from ncatbot.core.api.interface import IBotAPI

from .ncatbot_event import NcatBotEvent

LOG = get_log("Dispatcher")


def parse_event_type(data: dict) -> Optional[EventType]:
    """
    从原始事件数据解析事件类型

    Args:
        data: OneBot 原始事件数据

    Returns:
        对应的 EventType，无法解析时返回 None
    """
    post_type = data.get("post_type")

    if post_type == PostType.MESSAGE:
        return EventType.MESSAGE

    if post_type == PostType.MESSAGE_SENT or post_type == "message_sent":
        return EventType.MESSAGE_SENT

    if post_type == PostType.NOTICE:
        return EventType.NOTICE

    if post_type == PostType.REQUEST:
        return EventType.REQUEST

    if post_type == PostType.META_EVENT:
        return EventType.META

    return None


class EventDispatcher:
    """
    事件分发器

    职责：
    - 接收来自 Adapter 的原始事件数据
    - 解析事件类型
    - 解析为事件对象
    - 发布到 EventBus
    """

    def __init__(self, event_bus: "EventBus", api: "IBotAPI"):
        """
        初始化分发器

        Args:
            event_bus: 事件总线实例
            api: Bot API 实例（用于绑定到事件对象）
        """
        self.event_bus = event_bus
        self.api = api

    async def dispatch(self, data_or_event: Union[dict, BaseEvent]) -> None:
        """
        分发事件数据

        支持两种输入：
        1. dict: 原始事件数据（传统模式，内部解析）
        2. BaseEvent: 已转换的事件对象（新 Adapter 模式）

        Args:
            data_or_event: 原始数据 dict 或已转换的 BaseEvent
        """
        if isinstance(data_or_event, BaseEvent):
            # 新 Adapter 模式：事件已转换
            event = data_or_event
            event_type = self._get_event_type_from_event(event)
            if not event_type:
                LOG.debug(f"未知事件类型: {event.post_type}")
                return

            ncatbot_event = NcatBotEvent(f"ncatbot.{event_type.value}", event)
            await self.event_bus.publish(ncatbot_event)
            return

        # 传统模式：从 dict 解析
        data = data_or_event
        event_type = parse_event_type(data)
        if not event_type:
            LOG.debug(f"未知事件类型: {data.get('post_type')}")
            return

        try:
            event = EventParser.parse(data, self.api)
            ncatbot_event = NcatBotEvent(f"ncatbot.{event_type.value}", event)
            await self.event_bus.publish(ncatbot_event)

        except ValueError as e:
            LOG.warning(f"事件解析失败: {e}")
        except Exception as e:
            LOG.error(f"事件处理出错: {e}\n{traceback.format_exc()}")

    @staticmethod
    def _get_event_type_from_event(event: BaseEvent) -> Optional[EventType]:
        """从 BaseEvent 对象获取事件类型"""
        post_type = getattr(event, "post_type", None)
        if not post_type:
            return None

        if post_type == PostType.MESSAGE or post_type == "message":
            return EventType.MESSAGE
        if post_type == "message_sent":
            return EventType.MESSAGE_SENT
        if post_type == PostType.NOTICE or post_type == "notice":
            return EventType.NOTICE
        if post_type == PostType.REQUEST or post_type == "request":
            return EventType.REQUEST
        if post_type == PostType.META_EVENT or post_type == "meta_event":
            return EventType.META
        return None

    async def __call__(self, data_or_event: Union[dict, BaseEvent]) -> None:
        """支持作为回调函数使用"""
        await self.dispatch(data_or_event)
