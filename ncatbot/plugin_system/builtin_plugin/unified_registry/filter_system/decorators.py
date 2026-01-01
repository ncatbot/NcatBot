"""过滤器装饰器 v2.0"""

from typing import Callable, Union, TYPE_CHECKING

from .builtin import (
    GroupFilter,
    PrivateFilter,
    MessageSentFilter,
    NonSelfFilter,
    AdminFilter,
    GroupAdminFilter,
    GroupOwnerFilter,
    RootFilter,
    CustomFilter,
)
from .base import BaseFilter
from .base import CombinedFilter

if TYPE_CHECKING:
    from .base import BaseFilter

__all__ = [
    # 权限装饰器
    "admin_only", "root_only", "private_only", "group_only",
    # 事件装饰器
    "on_message", "on_message_sent", "on_notice", "on_request",
    "on_group_at", "on_group_poke",
    "on_group_increase", "on_group_decrease", "on_group_request",
    # 过滤器装饰器
    "filter", "admin_filter", "group_admin_filter", "group_owner_filter", "root_filter",
    "private_filter", "group_filter", "admin_group_filter", "admin_private_filter",
    # 工具类
    "FilterDecorator",
]


def filter(*filters: Union[str, "BaseFilter"]):
    from .registry import filter_registry

    """为函数添加过滤器的装饰器

    Usage:
        @filter("my_filter")
        @filter(GroupFilter())
        @filter(GroupFilter(), AdminFilter())
        def my_command(event):
            pass
    """

    def decorator(func: Callable) -> Callable:
        filter_registry.add_filter_to_function(func, *filters)
        return func

    return decorator


# 专用事件过滤器
def on_request(func: Callable) -> Callable:
    """请求专用装饰器"""
    from ..legacy_registry import legacy_registry

    legacy_registry._request_event.append(func)
    return func


def on_notice(func: Callable) -> Callable:
    """通知专用装饰器"""
    from ..legacy_registry import legacy_registry

    legacy_registry._notice_event.append(func)
    return func


def on_group_poke(func: Callable) -> Callable:
    """群聊戳一戳专用装饰器"""
    from ncatbot.core.notice_event import NoticeEvent

    def poke_filter(event) -> bool:
        """检查是否是戳一戳事件"""
        return isinstance(event, NoticeEvent) and event.sub_type == "poke"

    decorated_func = filter(GroupFilter(), CustomFilter(poke_filter, "poke_filter"))(
        func
    )
    return on_notice(decorated_func)


def on_group_at(func: Callable) -> Callable:
    """群聊艾特专用装饰器"""
    from ncatbot.core.message_segments.message import GroupMessageEvent

    def at_filter(event) -> bool:
        """检查是否艾特了机器人"""
        if not isinstance(event, GroupMessageEvent):
            return False
        from ncatbot.core.event.message_segments.primitives import At

        bot_id = event.self_id
        for message_spiece in event.message.messages:
            if (
                isinstance(message_spiece, At)
                and getattr(message_spiece, "qq", None) == bot_id
            ):
                return True
        return False

    decorated_func = filter(GroupFilter(), CustomFilter(at_filter, "at_filter"))(func)
    return on_message(decorated_func)


def on_group_increase(func: Callable) -> Callable:
    """群聊人数增加专用装饰器"""

    def group_increase_filter(event) -> bool:
        """检查是否是群聊人数增加事件"""
        from ncatbot.core.notice_event import NoticeEvent

        return isinstance(event, NoticeEvent) and event.notice_type == "group_increase"

    decorated_func = filter(
        GroupFilter(), CustomFilter(group_increase_filter, "group_increase_filter")
    )(func)
    return on_notice(decorated_func)


def on_group_decrease(func: Callable) -> Callable:
    """群聊人数减少专用装饰器"""

    def group_decrease_filter(event) -> bool:
        """检查是否是群聊人数减少事件"""
        from ncatbot.core.notice_event import NoticeEvent

        return isinstance(event, NoticeEvent) and event.notice_type == "group_decrease"

    decorated_func = filter(
        GroupFilter(), CustomFilter(group_decrease_filter, "group_decrease_filter")
    )(func)
    return on_notice(decorated_func)


def on_group_request(func: Callable) -> Callable:
    """群聊请求专用装饰器"""

    def group_request_filter(event) -> bool:
        """检查是否是群聊请求事件"""
        from ncatbot.core.request_event import RequestEvent

        return isinstance(event, RequestEvent)

    decorated_func = filter(
        GroupFilter(), CustomFilter(group_request_filter, "group_request_filter")
    )(func)
    return on_request(decorated_func)


# 兼容与可组合包装器
class FilterDecorator:
    """将 BaseFilter 包装为既可用作装饰器也可进行 | & 组合的对象"""

    def __init__(self, filter_instance: BaseFilter):
        self.filter = filter_instance

    def __call__(self, func: Callable) -> Callable:
        from .registry import filter_registry

        filter_registry.add_filter_to_function(func, self.filter)
        return func

    def __or__(self, other):
        from .base import CombinedFilter

        other_filter = other.filter if isinstance(other, FilterDecorator) else other
        if not isinstance(other_filter, BaseFilter):
            raise TypeError("右操作数必须是 BaseFilter 或 FilterDecorator")
        return CombinedFilter(self.filter, other_filter, "or")

    def __and__(self, other):
        from .base import CombinedFilter

        other_filter = other.filter if isinstance(other, FilterDecorator) else other
        if not isinstance(other_filter, BaseFilter):
            raise TypeError("右操作数必须是 BaseFilter 或 FilterDecorator")
        return CombinedFilter(self.filter, other_filter, "and")


# 用包装器替换原始函数式装饰器以支持组合
group_filter = FilterDecorator(GroupFilter())
private_filter = FilterDecorator(PrivateFilter())
admin_filter = FilterDecorator(AdminFilter())
group_admin_filter = FilterDecorator(GroupAdminFilter())
group_owner_filter = FilterDecorator(GroupOwnerFilter())
root_filter = FilterDecorator(RootFilter())
on_message = FilterDecorator(NonSelfFilter())
on_message_sent = FilterDecorator(MessageSentFilter())
admin_only = admin_filter
root_only = root_filter
private_only = private_filter
group_only = group_filter
# 组合装饰器（保留“且”逻辑）
admin_group_filter = FilterDecorator(
    CombinedFilter(GroupFilter(), AdminFilter(), "and")
)
admin_private_filter = FilterDecorator(
    CombinedFilter(PrivateFilter(), AdminFilter(), "and")
)
