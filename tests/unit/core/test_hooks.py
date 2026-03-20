"""
Hook 系统规范测试

规范:
  K-01: Hook 作为装饰器绑定到 func.__hooks__
  K-02: add_hooks() 批量添加
  K-03: get_hooks() 按 priority 降序返回
  K-04: HookContext 正确传递
  K-04: 内置 MessageTypeFilter 过滤
  K-05: 内置 SelfFilter 过滤自身消息
"""

from ncatbot.core.registry.hook import (
    Hook,
    HookAction,
    HookContext,
    HookStage,
    add_hooks,
    get_hooks,
)
from ncatbot.core.registry.builtin_hooks import MessageTypeFilter, PostTypeFilter
from ncatbot.core.dispatcher.event import Event
from ncatbot.core.registry.dispatcher import HandlerEntry
from ncatbot.testing import factory
from unittest.mock import MagicMock


_mock_api = MagicMock()


class SampleBeforeHook(Hook):
    stage = HookStage.BEFORE_CALL
    priority = 5

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.CONTINUE


class SampleAfterHook(Hook):
    stage = HookStage.AFTER_CALL
    priority = 3

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.CONTINUE


class HighPriorityHook(Hook):
    stage = HookStage.BEFORE_CALL
    priority = 10

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.CONTINUE


class LowPriorityHook(Hook):
    stage = HookStage.BEFORE_CALL
    priority = 1

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.CONTINUE


# ---- K-01: Hook 装饰器 ----


def test_hook_as_decorator():
    """K-01: @hook_instance 将 self 绑定到 func.__hooks__"""
    hook = SampleBeforeHook()

    @hook
    async def handler(event):
        pass

    assert hasattr(handler, "__hooks__")
    assert hook in handler.__hooks__


def test_hook_decorator_preserves_function():
    """K-01 补充: 装饰后函数本体不变"""
    hook = SampleBeforeHook()

    async def original(event):
        return 42

    decorated = hook(original)
    assert decorated is original


# ---- K-02: add_hooks() ----


def test_add_hooks_batch():
    """K-02: add_hooks() 批量添加多个 Hook"""
    h1 = SampleBeforeHook()
    h2 = SampleAfterHook()

    @add_hooks(h1, h2)
    async def handler(event):
        pass

    assert h1 in handler.__hooks__
    assert h2 in handler.__hooks__


# ---- K-03: get_hooks 按 priority 降序 ----


def test_get_hooks_sorted_by_priority():
    """K-03: get_hooks() 按 priority 降序排列"""
    high = HighPriorityHook()
    low = LowPriorityHook()
    mid = SampleBeforeHook()  # priority=5

    @add_hooks(low, mid, high)
    async def handler(event):
        pass

    hooks = get_hooks(handler)
    priorities = [h.priority for h in hooks]
    assert priorities == sorted(priorities, reverse=True)


# ---- K-04: HookContext ----


def test_hook_context_fields():
    """K-04: HookContext 正确传递 event / handler_entry"""
    data = factory.group_message("test")
    event = Event(type="message.group", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="message.group")

    ctx = HookContext(
        event=event, event_type="message.group", handler_entry=entry, api=_mock_api
    )
    assert ctx.event is event
    assert ctx.event_type == "message.group"
    assert ctx.handler_entry is entry
    assert ctx.result is None
    assert ctx.error is None
    assert ctx.kwargs == {}


def test_hook_context_error_field():
    """K-04 补充: HookContext.error 可设置"""
    data = factory.group_message("test")
    event = Event(type="message.group", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="message.group")
    err = ValueError("test")
    ctx = HookContext(
        event=event,
        event_type="message.group",
        handler_entry=entry,
        api=_mock_api,
        error=err,
    )
    assert ctx.error is err


# ---- K-05: MessageTypeFilter ----


async def test_message_type_filter_group_pass():
    """K-05: group 消息通过 group filter"""
    f = MessageTypeFilter("group")
    data = factory.group_message("test", group_id="1")
    event = Event(type="message.group", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="message")
    ctx = HookContext(
        event=event, event_type="message.group", handler_entry=entry, api=_mock_api
    )

    result = await f.execute(ctx)
    assert result == HookAction.CONTINUE


async def test_message_type_filter_group_rejects_private():
    """K-05 补充: private 消息被 group filter 拒绝"""
    f = MessageTypeFilter("group")
    data = factory.private_message("test", user_id="1")
    event = Event(type="message.private", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="message")
    ctx = HookContext(
        event=event, event_type="message.private", handler_entry=entry, api=_mock_api
    )

    result = await f.execute(ctx)
    assert result == HookAction.SKIP


# ---- K-06: PostTypeFilter ----


async def test_post_type_filter():
    """K-06 (替代 SelfFilter): PostTypeFilter 正确过滤"""
    f = PostTypeFilter("message")
    data = factory.group_message("test", group_id="1")
    event = Event(type="message.group", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="message")
    ctx = HookContext(
        event=event, event_type="message.group", handler_entry=entry, api=_mock_api
    )

    result = await f.execute(ctx)
    assert result == HookAction.CONTINUE


async def test_post_type_filter_rejects():
    """K-06 补充: notice 事件被 message PostTypeFilter 拒绝"""
    f = PostTypeFilter("message")
    data = factory.group_increase(user_id="1", group_id="2")
    event = Event(type="notice.group_increase", data=data)

    async def dummy(e):
        pass

    entry = HandlerEntry(func=dummy, event_type="notice")
    ctx = HookContext(
        event=event,
        event_type="notice.group_increase",
        handler_entry=entry,
        api=_mock_api,
    )

    result = await f.execute(ctx)
    assert result == HookAction.SKIP


# ---- Hook subclass 必须定义 stage ----


def test_hook_subclass_inherits_default_stage():
    """Hook 子类继承默认 stage 属性 (BEFORE_CALL)"""

    class MinimalHook(Hook):
        async def execute(self, ctx):
            return HookAction.CONTINUE

    h = MinimalHook()
    assert h.stage == HookStage.BEFORE_CALL
