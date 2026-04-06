from .dispatcher import (
    AsyncEventDispatcher,
    Event,
    EventStream,
    # Predicate DSL
    P,
    AndP,
    OrP,
    NotP,
    same_user,
    same_group,
    is_private,
    is_group,
    is_message,
    has_keyword,
    msg_equals,
    msg_in,
    msg_matches,
    event_type,
    from_event,
)

from .registry import (
    # ContextVar
    set_current_plugin,
    get_current_plugin,
    _current_plugin_ctx,
    # Hook
    Hook,
    HookStage,
    HookAction,
    HookContext,
    add_hooks,
    get_hooks,
    # 内置 Hook (低级过滤)
    MessageTypeFilter,
    PostTypeFilter,
    SubTypeFilter,
    SelfFilter,
    StartsWithHook,
    KeywordHook,
    RegexHook,
    NoticeTypeFilter,
    RequestTypeFilter,
    PlatformFilter,
    RateLimitHook,
    group_only,
    private_only,
    non_self,
    startswith,
    keyword,
    regex,
    rate_limit,
    # 命令 Hook
    CommandHook,
    CommandGroup,
    CommandGroupHook,
    # 分发过滤 Hook
    DispatchFilterHook,
    # Dispatcher
    HandlerDispatcher,
    HandlerEntry,
    # Registrar
    Registrar,
    registrar,
    flush_pending,
    clear_pending,
    _pending_handlers,
)

# Session 便利类型（从 plugin 层 re-export，方便用户导入）
from ncatbot.plugin import SessionCancelled, SessionResult

__all__ = [
    "AsyncEventDispatcher",
    "Event",
    "EventStream",
    # Predicate DSL
    "P",
    "AndP",
    "OrP",
    "NotP",
    "same_user",
    "same_group",
    "is_private",
    "is_group",
    "is_message",
    "has_keyword",
    "msg_equals",
    "msg_in",
    "msg_matches",
    "event_type",
    "from_event",
    # Registry — ContextVar
    "set_current_plugin",
    "get_current_plugin",
    "_current_plugin_ctx",
    # Registry — Hook
    "Hook",
    "HookStage",
    "HookAction",
    "HookContext",
    "add_hooks",
    "get_hooks",
    # Registry — 内置 Hook
    "MessageTypeFilter",
    "PostTypeFilter",
    "SubTypeFilter",
    "SelfFilter",
    "StartsWithHook",
    "KeywordHook",
    "RegexHook",
    "NoticeTypeFilter",
    "RequestTypeFilter",
    "PlatformFilter",
    "group_only",
    "private_only",
    "non_self",
    "startswith",
    "keyword",
    "regex",
    "RateLimitHook",
    "rate_limit",
    # Registry — 命令 Hook
    "CommandHook",
    "CommandGroup",
    "CommandGroupHook",
    # Registry — 分发过滤 Hook
    "DispatchFilterHook",
    # Registry — Dispatcher
    "HandlerDispatcher",
    "HandlerEntry",
    # Registry — Registrar
    "Registrar",
    "registrar",
    "flush_pending",
    "clear_pending",
    "_pending_handlers",
    # Session 便利类型
    "SessionCancelled",
    "SessionResult",
]
