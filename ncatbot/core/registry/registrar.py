"""
Registrar — ContextVar 驱动的装饰器注册器

提供 .on() 装饰器用于标记 handler + 附加 hooks。
通过 ContextVar 读取当前正在加载的插件名称，将 handler 按插件隔离收集。
flush_pending() 将指定插件的 handler 批量注册到 HandlerDispatcher。

事件类型格式统一使用 AsyncEventDispatcher 的 resolved 格式:
  "message"、"message.group"、"notice.group_increase" 等。

平台专属装饰器通过子注册器提供:
  registrar.qq.on_poke()、registrar.bilibili.on_danmu()、registrar.github.on_push()
"""

from functools import cached_property
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from ncatbot.utils import get_log

from .context import get_current_plugin
from .hook import Hook
from .builtin_hooks import MessageTypeFilter, PlatformFilter
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

    平台子注册器:
    - registrar.qq — QQ 专属装饰器
    - registrar.bilibili — Bilibili 专属装饰器
    - registrar.github — GitHub 专属装饰器
    """

    def __init__(self, default_hooks: Optional[List[Hook]] = None):
        self._default_hooks = list(default_hooks or [])

    def on(
        self,
        event_type: str,
        priority: int = 0,
        platform: Optional[str] = None,
        **metadata: Any,
    ) -> Callable:
        """注册 handler 的装饰器

        Args:
            event_type: 事件类型，如 "message"、"message.group"、"notice" 等
            priority: 优先级，越大越先执行
            platform: 平台过滤，None 接收所有平台，"qq" 仅 QQ
            **metadata: 附加元信息
        """

        def decorator(func: Callable) -> Callable:
            # 附加默认 hooks
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            for hook in self._default_hooks:
                if hook not in func.__hooks__:
                    func.__hooks__.append(hook)

            # 平台过滤 hook
            if platform is not None:
                func.__hooks__.append(PlatformFilter(platform))

            # 标记元信息
            func.__handler_meta__ = {
                "event_type": event_type,
                "priority": priority,
                **metadata,
            }

            # ContextVar 隔离收集（去重：同一函数只收集一次，后续装饰器只更新 meta/hooks）
            plugin_name = get_current_plugin() or "__global__"
            pending_list = _pending_handlers.setdefault(plugin_name, [])
            if func not in pending_list:
                pending_list.append(func)
            LOG.debug(
                "on() 收集 handler: %s → %s (plugin=%s, pending_count=%d)",
                func.__name__,
                event_type,
                plugin_name,
                len(pending_list),
            )

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

    # ==================== 平台子注册器 ====================

    @cached_property
    def qq(self):
        """QQ 平台子注册器"""
        from .platform import QQRegistrar

        return QQRegistrar(self)

    @cached_property
    def bilibili(self):
        """Bilibili 平台子注册器"""
        from .platform import BilibiliRegistrar

        return BilibiliRegistrar(self)

    @cached_property
    def github(self):
        """GitHub 平台子注册器"""
        from .platform import GitHubRegistrar

        return GitHubRegistrar(self)

    # ==================== 跨平台便捷装饰器 ====================
    # 事件类型使用 AsyncEventDispatcher._resolve_type() 产出的格式

    def on_group_message(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册群消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("group"))
            return self.on("message", priority=priority, platform=platform, **metadata)(
                func
            )

        return decorator

    def on_private_message(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册私聊消息 handler"""

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(MessageTypeFilter("private"))
            return self.on("message", priority=priority, platform=platform, **metadata)(
                func
            )

        return decorator

    def on_message(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册所有消息 handler (群+私聊)"""
        return self.on("message", priority=priority, platform=platform, **metadata)

    def on_message_sent(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册消息发送 handler"""
        return self.on("message_sent", priority=priority, platform=platform, **metadata)

    def on_notice(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册通知事件 handler"""
        return self.on("notice", priority=priority, platform=platform, **metadata)

    def on_request(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册请求事件 handler"""
        return self.on("request", priority=priority, platform=platform, **metadata)

    def on_meta(
        self, priority: int = 0, platform: Optional[str] = None, **metadata: Any
    ) -> Callable:
        """注册元事件 handler"""
        return self.on("meta_event", priority=priority, platform=platform, **metadata)

    # ==================== 命令装饰器 (匹配 + 参数绑定) ====================

    def on_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        platform: Optional[str] = None,
        **metadata: Any,
    ) -> Callable:
        """注册命令 handler (群+私聊)

        匹配 message.text，支持注解式参数绑定。
        """

        def decorator(func: Callable) -> Callable:
            if not hasattr(func, "__hooks__"):
                func.__hooks__ = []
            func.__hooks__.append(CommandHook(*names, ignore_case=ignore_case))
            return self.on("message", priority=priority, platform=platform, **metadata)(
                func
            )

        return decorator

    def on_group_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        platform: Optional[str] = None,
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
            return self.on("message", priority=priority, platform=platform, **metadata)(
                func
            )

        return decorator

    def on_private_command(
        self,
        *names: str,
        priority: int = 0,
        ignore_case: bool = False,
        platform: Optional[str] = None,
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
            return self.on("message", priority=priority, platform=platform, **metadata)(
                func
            )

        return decorator


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
    LOG.debug(
        "flush_pending(%s): 待注册 %d 个 handler (funcs: %s)",
        plugin_name,
        len(handlers),
        [f.__name__ for f in handlers],
    )
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
