"""
Registrar — ContextVar 驱动的装饰器注册器

提供 .on() 装饰器用于标记 handler + 附加 hooks。
通过 ContextVar 读取当前正在加载的插件名称，将 handler 按插件隔离收集。
flush_pending() 将指定插件的 handler 批量注册到 HandlerDispatcher。

事件类型格式统一使用 AsyncEventDispatcher 的 resolved 格式:
  "message"、"message.group"、"notice.group_increase" 等。
"""

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from ncatbot.utils import get_log

from .context import get_current_plugin
from .hook import Hook
from .builtin_hooks import MessageTypeFilter
from .command_hook import CommandHook

if TYPE_CHECKING:
    from .dispatcher import HandlerDispatcher

LOG = get_log("Registrar")

# 按 plugin_name 隔离的 pending 队列
# key "__global__" 用于非插件上下文（如 bot.on）
_pending_handlers: Dict[str, List[Callable]] = {}


class Registrar:
    """
    ContextVar 驱动的装饰器注册器

    .on() 装饰器:
    - 将默认 hooks setattr 到 func.__hooks__
    - 标记 func.__handler_meta__ 元信息
    - 读取 ContextVar 获取当前 plugin name，按 name 隔离收集
    """

    def __init__(self, default_hooks: Optional[List[Hook]] = None):
        self._default_hooks = list(default_hooks or [])

    def on(
        self,
        event_type: str,
        priority: int = 0,
        **metadata: Any,
    ) -> Callable:
        """注册 handler 的装饰器

        Args:
            event_type: 事件类型，如 "message"、"message.group"、"notice" 等
            priority: 优先级，越大越先执行
            **metadata: 附加元信息
        """

        def decorator(func: Callable) -> Callable:
            # 附加默认 hooks
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            for hook in self._default_hooks:
                if hook not in func.__hooks__:
                    func.__hooks__.append(hook)

            # 标记元信息
            func.__handler_meta__ = {
                "event_type": event_type,
                "priority": priority,
                **metadata,
            }

            # ContextVar 隔离收集
            plugin_name = get_current_plugin() or "__global__"
            _pending_handlers.setdefault(plugin_name, []).append(func)

            return func

        return decorator

    def fork(
        self,
        extra_hooks: Optional[List[Hook]] = None,
        remove_hooks: Optional[List[Hook]] = None,
    ) -> "Registrar":
        """创建带不同默认 hooks 的新 Registrar"""
        new_hooks = [h for h in self._default_hooks if h not in (remove_hooks or [])]
        new_hooks.extend(extra_hooks or [])
        return Registrar(default_hooks=new_hooks)

    # ==================== 便捷装饰器 ====================
    # 事件类型使用 AsyncEventDispatcher._resolve_type() 产出的格式

    def on_group_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("group"))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_private_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册私聊消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("private"))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_message(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册所有消息 handler (群+私聊)"""
        return self.on("message", priority=priority, **metadata)

    def on_message_sent(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册消息发送 handler"""
        return self.on("message_sent", priority=priority, **metadata)

    def on_notice(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册通知事件 handler"""
        return self.on("notice", priority=priority, **metadata)

    def on_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册请求事件 handler"""
        return self.on("request", priority=priority, **metadata)

    def on_meta(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册元事件 handler"""
        return self.on("meta_event", priority=priority, **metadata)

    # ==================== 命令装饰器 (匹配 + 参数绑定) ====================

    def on_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        **metadata: Any,
    ) -> Callable:
        """注册命令 handler (群+私聊)

        匹配 message.text，支持注解式参数绑定。
        """

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_group_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        **metadata: Any,
    ) -> Callable:
        """注册群命令 handler

        组合 MessageTypeFilter("group") + CommandHook 匹配 + 参数绑定。
        """

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("group"))
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    def on_private_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        **metadata: Any,
    ) -> Callable:
        """注册私聊命令 handler

        组合 MessageTypeFilter("private") + CommandHook 匹配 + 参数绑定。
        """

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("private"))
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, **metadata)(func)

        return decorator

    # ==================== 通知/请求精确类型 ====================

    def on_group_increase(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群成员增加事件 handler"""
        return self.on("notice.group_increase", priority=priority, **metadata)

    def on_group_decrease(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群成员减少事件 handler"""
        return self.on("notice.group_decrease", priority=priority, **metadata)

    def on_friend_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册好友请求 handler"""
        return self.on("request.friend", priority=priority, **metadata)

    def on_group_request(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册群请求 handler"""
        return self.on("request.group", priority=priority, **metadata)

    def on_poke(self, priority: int = 0, **metadata: Any) -> Callable:
        """注册戳一戳事件 handler"""
        return self.on("notice.poke", priority=priority, **metadata)


def flush_pending(
    dispatcher: "HandlerDispatcher",
    plugin_name: str,
    plugin_instance: object = None,
) -> int:
    """将指定插件的 pending handler 批量注册到 HandlerDispatcher。

    Args:
        dispatcher: HandlerDispatcher 实例
        plugin_name: 插件名称
        plugin_instance: 插件实例（用于实例方法注入）

    Returns:
        注册的 handler 数量
    """
    handlers = _pending_handlers.pop(plugin_name, [])
    count = 0

    for func in handlers:
        meta = dict(func.__handler_meta__)  # copy 避免修改原始
        event_type = meta.pop("event_type")
        priority = meta.pop("priority", 0)

        # 仅对插件类的实例方法注入 plugin_instance
        # 通过 __qualname__ 判断: "ClassName.method" 含有 ".";
        # 模块级函数的 __qualname__ == __name__，不含 "."
        if plugin_instance is not None and "." in getattr(func, "__qualname__", ""):
            meta["plugin_instance"] = plugin_instance

        dispatcher.register_handler(
            event_type=event_type,
            func=func,
            priority=priority,
            plugin_name=plugin_name,
            **meta,
        )
        count += 1

    if count:
        LOG.debug("flush_pending(%s): 注册 %d 个 handler", plugin_name, count)
    return count


def clear_pending(plugin_name: str) -> int:
    """清理指定插件的残留 pending handler（卸载时调用）。"""
    handlers = _pending_handlers.pop(plugin_name, [])
    return len(handlers)


# 全局默认 Registrar 实例
registrar = Registrar()
