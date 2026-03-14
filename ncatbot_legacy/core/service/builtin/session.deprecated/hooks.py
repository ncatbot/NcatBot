"""
Session Hook 实现

Session 逻辑完全通过 Hook 实现:
- SessionStartHook (AFTER_CALL): handler 执行后创建 session
- SessionStepHook (BEFORE_CALL): 有 session → 注入; 无 → SKIP
- SessionEndHook (AFTER_CALL): handler 执行后关闭 session
"""

from typing import Any, Callable, List, Optional

from ncatbot.core.registry.hook import Hook, HookAction, HookContext, HookStage
from ncatbot.utils import get_log

LOG = get_log("SessionHook")


def default_key_func(event: Any) -> str:
    """默认 session key: plugin_name:group_id:user_id 或 plugin_name:user_id"""
    parts = []
    if hasattr(event, "group_id") and event.group_id:
        parts.append(str(event.group_id))
    if hasattr(event, "user_id") and event.user_id:
        parts.append(str(event.user_id))
    return ":".join(parts) if parts else "global"


class SessionStartHook(Hook):
    """AFTER_CALL hook: handler 执行后创建 session"""

    stage = HookStage.AFTER_CALL

    def __init__(
        self,
        key_func: Optional[Callable] = None,
        ttl: Optional[float] = None,
        priority: int = 0,
    ):
        self.key_func = key_func or default_key_func
        self.ttl = ttl
        self.priority = priority
        self.name = "session_start"

    async def execute(self, ctx: HookContext) -> HookAction:
        sm = _get_session_manager(ctx)
        if sm is None:
            LOG.warning("SessionManager 不可用，跳过 session_start")
            return HookAction.CONTINUE

        key = self.key_func(ctx.event)
        session = sm.get_or_create(
            session_key=key,
            plugin_name=ctx.handler_entry.plugin_name,
            ttl=self.ttl,
        )

        # 如果 handler 有返回值且是 dict, 存入 session.state
        if ctx.result and isinstance(ctx.result, dict):
            for k, v in ctx.result.items():
                session.set(k, v)

        return HookAction.CONTINUE


class SessionStepHook(Hook):
    """BEFORE_CALL hook: 有 session → 注入 ctx.kwargs['session']; 无 → SKIP"""

    stage = HookStage.BEFORE_CALL

    def __init__(
        self,
        key_func: Optional[Callable] = None,
        priority: int = 500,
    ):
        self.key_func = key_func or default_key_func
        self.priority = priority
        self.name = "session_step"

    async def execute(self, ctx: HookContext) -> HookAction:
        sm = _get_session_manager(ctx)
        if sm is None:
            return HookAction.SKIP

        key = self.key_func(ctx.event)
        session = sm.get(key)

        if session is None or session.is_expired():
            return HookAction.SKIP  # 没有 session → 跳过此 handler

        session.touch()
        ctx.kwargs["session"] = session

        # 如果 session 在 wait_for_event → feed
        if session.feed(ctx.event):
            return HookAction.SKIP  # 事件已 feed 给 wait_for_event

        return HookAction.CONTINUE


class SessionEndHook(Hook):
    """AFTER_CALL hook: handler 执行后关闭 session"""

    stage = HookStage.AFTER_CALL

    def __init__(
        self,
        key_func: Optional[Callable] = None,
        priority: int = 0,
    ):
        self.key_func = key_func or default_key_func
        self.priority = priority
        self.name = "session_end"

    async def execute(self, ctx: HookContext) -> HookAction:
        sm = _get_session_manager(ctx)
        if sm is None:
            return HookAction.CONTINUE

        key = self.key_func(ctx.event)
        sm.close_session(key)
        return HookAction.CONTINUE


# ==================== 便捷装饰器 ====================


def session_start(
    key_func: Optional[Callable] = None,
    ttl: Optional[float] = None,
) -> SessionStartHook:
    """头节点: 执行后创建 session"""
    return SessionStartHook(key_func=key_func, ttl=ttl)


def session_step(
    key_func: Optional[Callable] = None,
) -> SessionStepHook:
    """中间节点: 有 session 才执行, 注入 session"""
    return SessionStepHook(key_func=key_func)


def session_end(
    key_func: Optional[Callable] = None,
) -> List[Hook]:
    """尾节点: session_step + session_end (需要 session 存在才执行 + 执行后关闭)

    返回两个 hook，使用时:
        @add_hooks(*session_end(key_func=...))
        @registrar.on("ncatbot.group_message_event")
        async def handle_end(event, session=None): ...
    """
    return [
        SessionStepHook(key_func=key_func),
        SessionEndHook(key_func=key_func),
    ]


# ==================== 内部工具 ====================


def _get_session_manager(ctx: HookContext):
    """从事件上下文获取 SessionManager"""
    event = ctx.event
    # 通过 event.services 获取 (需要 Phase 5 的 context.py 修改)
    if hasattr(event, "services") and event.services:
        return event.services.get("session_manager")
    return None
