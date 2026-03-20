"""
HandlerDispatcher 规范测试

规范:
  H-01: 精确匹配
  H-02: 前缀匹配
  H-03: 不匹配
  H-04: 优先级排序
  H-05: BEFORE_CALL Hook SKIP
  H-06: BEFORE_CALL Hook CONTINUE
  H-07: AFTER_CALL Hook 执行顺序
  H-08: ON_ERROR Hook
  H-09: revoke_plugin
  H-10: handler 接收 EventEntity
  H-11: stop() 后不再消费
"""

import asyncio


from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.core.registry.dispatcher import HandlerDispatcher
from ncatbot.core.registry.hook import Hook, HookAction, HookContext, HookStage
from ncatbot.event.common.base import BaseEvent
from ncatbot.testing import factory


# ---- 辅助 ----


class SkipHook(Hook):
    stage = HookStage.BEFORE_CALL

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.SKIP


class PassHook(Hook):
    stage = HookStage.BEFORE_CALL

    async def execute(self, ctx: HookContext) -> HookAction:
        return HookAction.CONTINUE


class AfterHook(Hook):
    stage = HookStage.AFTER_CALL

    def __init__(self):
        self.called = False

    async def execute(self, ctx: HookContext) -> HookAction:
        self.called = True
        return HookAction.CONTINUE


class ErrorHook(Hook):
    stage = HookStage.ON_ERROR

    def __init__(self):
        self.caught_error = None

    async def execute(self, ctx: HookContext) -> HookAction:
        self.caught_error = ctx.error
        return HookAction.CONTINUE


async def _make_dispatcher_with_event(mock_api=None):
    """创建 dispatcher 对，注入一条群消息并返回 (handler_dispatcher, event_dispatcher)"""
    if mock_api is None:
        mock_api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=mock_api)
    hd.start(ed)
    return hd, ed, mock_api


# ---- H-01: 精确匹配 ----


async def test_exact_match():
    """H-01: 注册 'message.group' → 该类型事件触发 handler"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    async def handler(event):
        called.set()

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert called.is_set()
    await hd.stop()
    await ed.close()


# ---- H-02: 前缀匹配 ----


async def test_prefix_match():
    """H-02: 注册 'message' → 'message.group' 也触发"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    async def handler(event):
        called.set()

    hd.register_handler("message", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert called.is_set()
    await hd.stop()
    await ed.close()


# ---- H-03: 不匹配 ----


async def test_no_match():
    """H-03: 注册 'notice' → 'message.group' 不触发"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    async def handler(event):
        called.set()

    hd.register_handler("notice", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert not called.is_set()
    await hd.stop()
    await ed.close()


# ---- H-04: 优先级排序 ----


async def test_priority_order():
    """H-04: priority 大的先执行"""
    hd, ed, _ = await _make_dispatcher_with_event()
    order = []

    async def handler_low(event):
        order.append("low")

    async def handler_high(event):
        order.append("high")

    hd.register_handler("message.group", handler_low, priority=0)
    hd.register_handler("message.group", handler_high, priority=10)

    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert order == ["high", "low"]
    await hd.stop()
    await ed.close()


# ---- H-05: BEFORE_CALL SKIP ----


async def test_before_call_skip():
    """H-05: BEFORE_CALL 返回 SKIP → handler 不执行"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    @SkipHook()
    async def handler(event):
        called.set()

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert not called.is_set()
    await hd.stop()
    await ed.close()


# ---- H-06: BEFORE_CALL CONTINUE ----


async def test_before_call_continue():
    """H-06: BEFORE_CALL 返回 CONTINUE → handler 正常执行"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    @PassHook()
    async def handler(event):
        called.set()

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert called.is_set()
    await hd.stop()
    await ed.close()


# ---- H-07: AFTER_CALL ----


async def test_after_call_hook():
    """H-07: AFTER_CALL Hook 在 handler 后执行"""
    hd, ed, _ = await _make_dispatcher_with_event()
    after = AfterHook()

    @after
    async def handler(event):
        pass

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert after.called
    await hd.stop()
    await ed.close()


# ---- H-08: ON_ERROR ----


async def test_on_error_hook():
    """H-08: handler 抛异常 → ON_ERROR Hook 收到异常"""
    hd, ed, _ = await _make_dispatcher_with_event()
    error_hook = ErrorHook()

    @error_hook
    async def handler(event):
        raise ValueError("test error")

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert error_hook.caught_error is not None
    assert isinstance(error_hook.caught_error, ValueError)
    await hd.stop()
    await ed.close()


# ---- H-09: revoke_plugin ----


async def test_revoke_plugin():
    """H-09: revoke_plugin 移除该插件所有 handler"""
    hd, ed, _ = await _make_dispatcher_with_event()

    async def handler(event):
        pass

    hd.register_handler("message.group", handler, plugin_name="test_plugin")
    hd.register_handler("notice", handler, plugin_name="test_plugin")

    removed = hd.revoke_plugin("test_plugin")
    assert removed == 2
    assert hd.get_handlers("message.group") == []
    assert hd.get_handlers("notice") == []
    await hd.stop()
    await ed.close()


async def test_revoke_plugin_partial():
    """H-09 补充: 只移除指定插件的 handler"""
    hd, ed, _ = await _make_dispatcher_with_event()

    async def h1(event):
        pass

    async def h2(event):
        pass

    hd.register_handler("message", h1, plugin_name="keep")
    hd.register_handler("message", h2, plugin_name="remove")

    hd.revoke_plugin("remove")
    handlers = hd.get_handlers("message")
    assert len(handlers) == 1
    assert handlers[0].plugin_name == "keep"
    await hd.stop()
    await ed.close()


# ---- H-10: handler 接收 EventEntity ----


async def test_handler_receives_event_entity():
    """H-10: handler 接收 BaseEvent 实例（非原始数据）"""
    hd, ed, _ = await _make_dispatcher_with_event()
    received = []

    async def handler(event):
        received.append(event)

    hd.register_handler("message.group", handler)
    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert len(received) == 1
    assert isinstance(received[0], BaseEvent)
    await hd.stop()
    await ed.close()


# ---- H-11: stop() 后不再消费 ----


async def test_stop_prevents_consumption():
    """H-11: stop() 后注入事件 → handler 不被调用"""
    hd, ed, _ = await _make_dispatcher_with_event()
    called = asyncio.Event()

    async def handler(event):
        called.set()

    hd.register_handler("message.group", handler)
    await hd.stop()

    await ed.callback(factory.group_message("hi", group_id="1"))
    await asyncio.sleep(0.05)

    assert not called.is_set()
    await ed.close()
