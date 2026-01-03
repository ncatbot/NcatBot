"""
事件分发器

负责接收原始事件数据，解析并分发到 EventBus。
"""

import traceback
from typing import TYPE_CHECKING, Optional

from ncatbot.utils import get_log
from ..event.parser import EventParser
from ..event.enums import PostType, EventType

if TYPE_CHECKING:
    from .event_bus import EventBus
    from ncatbot.core.api import BotAPI

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

    def __init__(self, event_bus: "EventBus", api: "BotAPI"):
        """
        初始化分发器

        Args:
            event_bus: 事件总线实例
            api: Bot API 实例（用于绑定到事件对象）
        """
        self.event_bus = event_bus
        self.api = api

    async def dispatch(self, data: dict) -> None:
        """
        分发原始事件数据

        1. 解析事件类型
        2. 解析为事件对象
        3. 发布到 EventBus

        Args:
            data: 原始事件数据（来自 WebSocket）
        """
        event_type = parse_event_type(data)
        if not event_type:
            LOG.debug(f"未知事件类型: {data.get('post_type')}")
            return

        try:
            # 解析为事件对象
            event = EventParser.parse(data, self.api)

            # 构造 NcatBotEvent 并发布
            ncatbot_event = NcatBotEvent(f"ncatbot.{event_type.value}", event)
            await self.event_bus.publish(ncatbot_event)

        except ValueError as e:
            LOG.warning(f"事件解析失败: {e}")
        except Exception as e:
            LOG.error(f"事件处理出错: {e}\n{traceback.format_exc()}")

    async def __call__(self, data: dict) -> None:
        """支持作为回调函数使用"""
        await self.dispatch(data)
