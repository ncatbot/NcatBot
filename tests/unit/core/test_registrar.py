"""
Registrar 规范测试

规范:
  R-01: @registrar.on() 收集 handler 到 pending → flush_pending 注册
  R-02: ContextVar 隔离不同 plugin_name
  R-03: fork() 创建独立 Registrar
  R-04: clear_pending() 清理残留
  R-08: registrar.bilibili.on_live_start() 路由到 live.live
  R-09: registrar.bilibili.on_live_end() 路由到 live.preparing
"""

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.core.registry.registrar import (
    Registrar,
    flush_pending,
    clear_pending,
    _pending_handlers,
)
from ncatbot.core.registry.context import set_current_plugin, _current_plugin_ctx
from ncatbot.core.registry.dispatcher import HandlerDispatcher


@pytest.fixture(autouse=True)
def clean_pending():
    """每个测试前清理全局 pending"""
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()


# ---- R-01: on() 收集 + flush ----


def test_on_collects_to_pending():
    """R-01: @registrar.on() 将 handler 收集到 __global__ pending"""
    reg = Registrar()

    @reg.on("message.group")
    async def my_handler(event):
        pass

    assert "__global__" in _pending_handlers
    assert my_handler in _pending_handlers["__global__"]


def test_flush_pending_registers_to_dispatcher():
    """R-01: flush_pending 将 pending 注册到 HandlerDispatcher"""
    reg = Registrar()
    hd = HandlerDispatcher(api=MockBotAPI())

    @reg.on("message", priority=5)
    async def my_handler(event):
        pass

    count = flush_pending(hd, "__global__")
    assert count == 1

    handlers = hd.get_handlers("message")
    assert len(handlers) == 1
    assert handlers[0].func is my_handler
    assert handlers[0].priority == 5


# ---- R-02: ContextVar 隔离 ----


def test_context_var_isolation():
    """R-02: 不同 plugin_name 的 pending 互不干扰"""
    reg = Registrar()

    token_a = set_current_plugin("plugin_a")

    @reg.on("message")
    async def handler_a(event):
        pass

    _current_plugin_ctx.reset(token_a)

    token_b = set_current_plugin("plugin_b")

    @reg.on("notice")
    async def handler_b(event):
        pass

    _current_plugin_ctx.reset(token_b)

    assert "plugin_a" in _pending_handlers
    assert "plugin_b" in _pending_handlers
    assert handler_a in _pending_handlers["plugin_a"]
    assert handler_b in _pending_handlers["plugin_b"]


# ---- R-03: fork() ----


def test_fork_creates_new_registrar():
    """R-03: fork() 创建的 Registrar 有独立的 default hooks"""
    from ncatbot.core.registry.hook import Hook, HookStage, HookAction, HookContext

    class DummyHook(Hook):
        stage = HookStage.BEFORE_CALL

        async def execute(self, ctx: HookContext) -> HookAction:
            return HookAction.CONTINUE

    original = Registrar(default_hooks=[DummyHook()])
    forked = original.fork(extra_hooks=[])

    assert len(forked._default_hooks) == len(original._default_hooks)

    # fork with remove
    forked2 = original.fork(remove_hooks=original._default_hooks)
    assert len(forked2._default_hooks) == 0


# ---- R-04: clear_pending ----


def test_clear_pending():
    """R-04: clear_pending() 清理残留后 flush 返回 0"""
    reg = Registrar()

    token = set_current_plugin("cleanup_test")

    @reg.on("message")
    async def handler(event):
        pass

    _current_plugin_ctx.reset(token)

    count = clear_pending("cleanup_test")
    assert count == 1

    # 再次 flush 应返回 0
    hd = HandlerDispatcher(api=MockBotAPI())
    assert flush_pending(hd, "cleanup_test") == 0


# ---- R-08 / R-09: BilibiliRegistrar 平台装饰器路由 ----


def test_bilibili_on_live_start_routes_to_live_live():
    """R-08: registrar.bilibili.on_live_start() 路由到 live.live"""
    reg = Registrar()
    hd = HandlerDispatcher(api=MockBotAPI())

    @reg.bilibili.on_live_start()
    async def handle_start(event):
        pass

    count = flush_pending(hd, "__global__")
    assert count == 1

    handlers = hd.get_handlers("live.live")
    funcs = [h.func for h in handlers]
    assert handle_start in funcs


def test_bilibili_on_live_end_routes_to_live_preparing():
    """R-09: registrar.bilibili.on_live_end() 路由到 live.preparing"""
    reg = Registrar()
    hd = HandlerDispatcher(api=MockBotAPI())

    @reg.bilibili.on_live_end()
    async def handle_end(event):
        pass

    count = flush_pending(hd, "__global__")
    assert count == 1

    handlers = hd.get_handlers("live.preparing")
    funcs = [h.func for h in handlers]
    assert handle_end in funcs
