"""事件处理器注册表

用于存储 notice 和 request 事件的处理器函数。
"""

from typing import List, Callable, Dict

from ncatbot.utils import get_log

LOG = get_log(__name__)


class EventRegistry:
    """事件注册表

    存储 notice 和 request 事件的处理器函数。
    """

    _current_plugin_name: str = ""

    def __init__(self):
        # handler -> plugin_name 映射
        self._notice_handlers: Dict[Callable, str] = {}
        self._request_handlers: Dict[Callable, str] = {}

    @classmethod
    def set_current_plugin_name(cls, plugin_name: str):
        cls._current_plugin_name = plugin_name

    def notice_handler(self, func: Callable) -> Callable:
        """注册 notice 事件处理器"""
        self._notice_handlers[func] = self._current_plugin_name
        return func

    def request_handler(self, func: Callable) -> Callable:
        """注册 request 事件处理器"""
        self._request_handlers[func] = self._current_plugin_name
        return func

    @property
    def notice_handlers(self) -> List[Callable]:
        """获取所有 notice 处理器"""
        return list(self._notice_handlers.keys())

    @property
    def request_handlers(self) -> List[Callable]:
        """获取所有 request 处理器"""
        return list(self._request_handlers.keys())

    def revoke_plugin(self, plugin_name: str) -> None:
        """撤销指定插件的所有处理器"""
        notice_to_remove = [
            func for func, name in self._notice_handlers.items() if name == plugin_name
        ]
        request_to_remove = [
            func for func, name in self._request_handlers.items() if name == plugin_name
        ]

        for func in notice_to_remove:
            del self._notice_handlers[func]
        for func in request_to_remove:
            del self._request_handlers[func]

        if notice_to_remove or request_to_remove:
            LOG.debug(
                f"撤销插件 {plugin_name} 的事件处理器: "
                f"notice={len(notice_to_remove)}, request={len(request_to_remove)}"
            )

    def clear(self):
        """清除所有处理器"""
        self._notice_handlers.clear()
        self._request_handlers.clear()


# 全局单例
event_registry = EventRegistry()
