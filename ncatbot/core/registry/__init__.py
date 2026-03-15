"""
注册系统 (Registry)

Hook 驱动 + HandlerDispatcher 分发 + Registrar 装饰器 + ContextVar 隔离。

核心组件:
- Hook: 绑定在 handler 上的拦截器 (BEFORE_CALL / AFTER_CALL / ON_ERROR)
- HandlerDispatcher: 纯机械分发器，通过 listener 接收 Event → 收集 handler → 执行 Hook 链
- Registrar: ContextVar 驱动的装饰器集合，按插件隔离收集 handler
- ContextVar: PluginLoader 在 exec_module 前后设置/重置，装饰器内读取

事件类型格式统一使用 AsyncEventDispatcher._resolve_type() 产出的格式:
  "message.group"、"notice.group_increase"、"request.friend" 等。
"""

# ContextVar
from .context import set_current_plugin, get_current_plugin

# Hook 系统
from .hook import Hook, HookStage, HookAction, HookContext, add_hooks, get_hooks

# 内置 Hook
from .builtin_hooks import (
    MessageTypeFilter,
    PostTypeFilter,
    SubTypeFilter,
    SelfFilter,
    StartsWithHook,
    KeywordHook,
    RegexHook,
    NoticeTypeFilter,
    RequestTypeFilter,
    group_only,
    private_only,
    non_self,
    startswith,
    keyword,
    regex,
)

# 命令 Hook
from .command_hook import CommandHook

# Dispatcher
from .dispatcher import HandlerDispatcher, HandlerEntry

# Registrar
from .registrar import Registrar, registrar, flush_pending, clear_pending

__all__ = [
    # ContextVar
    "set_current_plugin",
    "get_current_plugin",
    # Hook
    "Hook",
    "HookStage",
    "HookAction",
    "HookContext",
    "add_hooks",
    "get_hooks",
    # 内置 Hook (低级过滤)
    "MessageTypeFilter",
    "PostTypeFilter",
    "SubTypeFilter",
    "SelfFilter",
    "StartsWithHook",
    "KeywordHook",
    "RegexHook",
    "NoticeTypeFilter",
    "RequestTypeFilter",
    "group_only",
    "private_only",
    "non_self",
    "startswith",
    "keyword",
    "regex",
    # 命令 Hook (高级匹配 + 参数绑定)
    "CommandHook",
    # Dispatcher
    "HandlerDispatcher",
    "HandlerEntry",
    # Registrar
    "Registrar",
    "registrar",
    "flush_pending",
    "clear_pending",
]
