"""
事件注册器。

提供事件处理器的注册接口和装饰器。

NcatBot Event: 订阅的事件触发的回调是 NcatBotEvent(带类型 type 和数据 (Event)), 注册 Handler 传回的回调是 Event。
|
--- BotEvent
--- CustomEvent
"""

import inspect
from typing import Callable, Optional, Type, Literal, TYPE_CHECKING

from ..event.enums import EventType
from .ncatbot_event import NcatBotEvent
from ..event import (
    GroupMessageEvent,
    PrivateMessageEvent,
    GroupRequestEvent,
    FriendRequestEvent,
)
from ..event import MessageSegment

if TYPE_CHECKING:
    from .event_bus import EventBus


class EventRegistry:
    """
    事件注册器

    职责：
    - 提供事件处理器的注册方法
    - 提供装饰器风格的注册接口
    - 处理器包装（过滤、事件对象提取等）
    """

    def __init__(self, event_bus: "EventBus"):
        """
        初始化注册器

        Args:
            event_bus: 事件总线实例
        """
        self.event_bus = event_bus

    # ==================== 核心订阅方法 ====================

    def subscribe(
        self,
        event_type: str | EventType,
        handler: Callable,
        priority: int = 0,
        timeout: Optional[float] = None,
    ):
        """
        订阅事件（核心方法）

        处理器接收 NcatBotEvent 对象（包含 type 和 data）

        Args:
            event_type: 事件类型，支持 EventType 枚举或字符串
            handler: 事件处理函数，接收 NcatBotEvent 参数
            priority: 优先级，数值越大越先执行
            timeout: 超时时间
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self.event_bus.subscribe(key, handler, priority, timeout)

    def register_handler(
        self,
        event_type: str | EventType,
        handler: Callable,
        priority: int = 0,
        timeout: Optional[float] = None,
        filter_func: Optional[Callable] = None,
    ):
        """
        注册事件处理器（提取事件数据对象）

        负责从 NcatBotEvent 中提取 Event 数据对象并传递给用户的 handler

        Args:
            event_type: 事件类型
            handler: 用户的处理函数，接收 Event 对象
            priority: 优先级
            timeout: 超时时间
            filter_func: 可选的过滤函数，接收 Event，返回 bool
        """

        async def wrapper(ncatbot_event: NcatBotEvent):
            # 从 NcatBotEvent 提取真实的 Event
            event = ncatbot_event.data

            # 应用过滤器
            if filter_func and not filter_func(event):
                return

            # 调用用户的 handler
            if inspect.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

        self.subscribe(event_type, wrapper, priority, timeout)

    def add_handler(self, event_type: str, handler: Callable):
        """添加事件处理器（兼容旧接口）"""
        self.register_handler(event_type, handler)

    # ==================== 具体事件注册方法 ====================

    def add_group_message_handler(
        self, handler: Callable, filter: Optional[Type[MessageSegment]] = None
    ):
        """添加群消息处理器，自动过滤群消息事件"""

        def filter_func(event: GroupMessageEvent):
            # 检查是否为群消息
            if not (hasattr(event, "message_type") and event.message_type == "group"):
                return False
            # 应用消息段过滤器
            if filter is not None and hasattr(event, "message"):
                return len(event.message.filter(filter)) > 0
            return True

        self.register_handler(EventType.MESSAGE, handler, filter_func=filter_func)

    def add_private_message_handler(
        self, handler: Callable, filter: Optional[Type[MessageSegment]] = None
    ):
        """添加私聊消息处理器，自动过滤私聊消息事件"""

        def filter_func(event: PrivateMessageEvent):
            # 检查是否为私聊消息
            if not (hasattr(event, "message_type") and event.message_type == "private"):
                return False
            # 应用消息段过滤器
            if filter is not None and hasattr(event, "message"):
                return len(event.message.filter(filter)) > 0
            return True

        self.register_handler(EventType.MESSAGE, handler, filter_func=filter_func)

    def add_message_sent_handler(self, handler: Callable):
        """添加消息发送处理器（message_sent 事件）"""
        self.register_handler(EventType.MESSAGE_SENT, handler)

    def add_notice_handler(self, handler: Callable):
        """添加通知事件处理器"""
        self.register_handler(EventType.NOTICE, handler)

    def add_request_handler(
        self, handler: Callable, filter: Optional[Literal["group", "friend"]] = None
    ):
        """[弃用] 添加请求事件处理器

        .. deprecated::
            请使用 :meth:`add_group_request_handler` 或 :meth:`add_friend_request_handler` 代替
        """
        if filter == "group":
            self.add_group_request_handler(handler)
        elif filter == "friend":
            self.add_friend_request_handler(handler)
        else:
            self.register_handler(EventType.REQUEST, handler)

    def add_group_request_handler(
        self,
        handler: Callable,
        filter: Optional[Callable[[GroupRequestEvent], bool]] = None,
    ):
        """添加群请求处理器，自动过滤群请求事件"""

        def filter_func(event: GroupRequestEvent):
            if not (hasattr(event, "request_type") and event.request_type == "group"):
                return False
            return filter(event) if filter else True

        self.register_handler(EventType.REQUEST, handler, filter_func=filter_func)

    def add_friend_request_handler(self, handler: Callable):
        """添加好友请求处理器，自动过滤好友请求事件"""

        def filter_func(event: FriendRequestEvent):
            return hasattr(event, "request_type") and event.request_type == "friend"

        self.register_handler(EventType.REQUEST, handler, filter_func=filter_func)

    def add_startup_handler(self, handler: Callable):
        """添加启动事件处理器，自动过滤 lifecycle connect 事件"""

        def filter_func(event):
            return (
                event.meta_event_type == "lifecycle"
                and hasattr(event, "sub_type")
                and event.sub_type == "connect"
            )

        self.register_handler(EventType.META, handler, filter_func=filter_func)

    def add_shutdown_handler(self, handler: Callable):
        """添加关闭事件处理器（需要在应用层实现）"""
        self.register_handler(EventType.META, handler)

    def add_heartbeat_handler(self, handler: Callable):
        """添加心跳事件处理器，自动过滤心跳事件"""

        def filter_func(event):
            return (
                hasattr(event, "meta_event_type")
                and event.meta_event_type == "heartbeat"
            )

        self.register_handler(EventType.META, handler, filter_func=filter_func)

    # ==================== 装饰器接口 ====================

    def on_group_message(self, filter: Optional[Type[MessageSegment]] = None):
        def decorator(f):
            self.add_group_message_handler(f, filter)
            return f

        return decorator

    def on_private_message(self, filter: Optional[Type[MessageSegment]] = None):
        def decorator(f):
            self.add_private_message_handler(f, filter)
            return f

        return decorator

    def on_message_sent(self):
        def decorator(f):
            self.add_message_sent_handler(f)
            return f

        return decorator

    def on_notice(self, notice_type: Optional[str] = None, priority: int = 0):
        """
        注册通知处理器

        Args:
            notice_type: 可选，指定具体类型如 "group_increase"
            priority: 优先级
        """

        def decorator(f):
            if notice_type:
                # 直接使用 register_handler 而不是不存在的 _wrap_handler
                self.register_handler(f"notice.{notice_type}", f, priority=priority)
            else:
                self.add_notice_handler(f)
            return f

        return decorator

    def on_request(self, filter: Optional[Literal["group", "friend"]] = None):
        """[弃用] 注册请求处理器装饰器

        .. deprecated::
            请使用 :meth:`on_group_request` 或 :meth:`on_friend_request` 代替
        """

        def decorator(f):
            self.add_request_handler(f, filter)
            return f

        return decorator

    def on_group_request(
        self, filter: Optional[Callable[[GroupRequestEvent], bool]] = None
    ):
        def decorator(f):
            self.add_group_request_handler(f, filter)
            return f

        return decorator

    def on_friend_request(self):
        def decorator(f):
            self.add_friend_request_handler(f)
            return f

        return decorator

    def on_startup(self, priority: int = 0):
        def decorator(f):
            self.add_startup_handler(f)
            return f

        return decorator

    def on_shutdown(self, priority: int = 0):
        def decorator(f):
            self.add_shutdown_handler(f)
            return f

        return decorator

    def on_heartbeat(self, priority: int = 0):
        def decorator(f):
            self.add_heartbeat_handler(f)
            return f

        return decorator
