"""
插件生命周期集成测试

规范:
  I-10: Registrar.on() → flush_pending → HandlerDispatcher 注册
  I-11: revoke_plugin 后 handler 不再触发
  I-12: 多插件 handler 互不干扰
  I-13: ContextVar 隔离 → 不同插件 pending 分开
"""

import asyncio

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.core.registry.dispatcher import HandlerDispatcher
from ncatbot.core.registry.registrar import (
    Registrar,
    flush_pending,
    _pending_handlers,
)
from ncatbot.core.registry.context import set_current_plugin, _current_plugin_ctx
from ncatbot.testing import factory


@pytest.fixture(autouse=True)
def clean_pending():
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()


# ---- I-10: Registrar → flush → HandlerDispatcher ----


async def test_registrar_to_dispatcher():
    """I-10: from registrar.on() → flush_pending → handler 可接收事件"""
    reg = Registrar()
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api)
    hd.start(ed)

    received = []

    @reg.on("message.group")
    async def handler(event):
        received.append(event)

    flush_pending(hd, "__global__")

    await ed.callback(factory.group_message("test"))
    await asyncio.sleep(0.05)

    assert len(received) == 1

    await hd.stop()
    await ed.close()


# ---- I-11: revoke 后不触发 ----


async def test_revoke_stops_handler():
    """I-11: revoke_plugin 后 handler 不再触发"""
    reg = Registrar()
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api)
    hd.start(ed)

    received = []

    token = set_current_plugin("my_plugin")

    @reg.on("message.group")
    async def handler(event):
        received.append(event)

    _current_plugin_ctx.reset(token)

    flush_pending(hd, "my_plugin")

    # 第一次 — 应该触发
    await ed.callback(factory.group_message("first"))
    await asyncio.sleep(0.05)
    assert len(received) == 1

    # revoke
    hd.revoke_plugin("my_plugin")

    # 第二次 — 不应触发
    await ed.callback(factory.group_message("second"))
    await asyncio.sleep(0.05)
    assert len(received) == 1  # 仍然是 1

    await hd.stop()
    await ed.close()


# ---- I-12: 多插件互不干扰 ----


async def test_multi_plugin_isolation():
    """I-12: 不同插件的 handler 各自工作"""
    reg = Registrar()
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api)
    hd.start(ed)

    results_a = []
    results_b = []

    # Plugin A
    token_a = set_current_plugin("plugin_a")

    @reg.on("message.group")
    async def handler_a(event):
        results_a.append("A")

    _current_plugin_ctx.reset(token_a)

    # Plugin B
    token_b = set_current_plugin("plugin_b")

    @reg.on("message.group")
    async def handler_b(event):
        results_b.append("B")

    _current_plugin_ctx.reset(token_b)

    flush_pending(hd, "plugin_a")
    flush_pending(hd, "plugin_b")

    await ed.callback(factory.group_message("hello"))
    await asyncio.sleep(0.05)

    assert results_a == ["A"]
    assert results_b == ["B"]

    # revoke A 不影响 B
    hd.revoke_plugin("plugin_a")
    results_a.clear()
    results_b.clear()

    await ed.callback(factory.group_message("hello2"))
    await asyncio.sleep(0.05)

    assert results_a == []
    assert results_b == ["B"]

    await hd.stop()
    await ed.close()


# ---- I-13: ContextVar 隔离 ----


async def test_context_var_isolation():
    """I-13: 不同 ContextVar 上下文 → 不同 pending 分组"""
    reg = Registrar()

    token = set_current_plugin("isolated_plugin")

    @reg.on("message")
    async def handler(event):
        pass

    _current_plugin_ctx.reset(token)

    # handler 应被收集到 "isolated_plugin" 下
    assert "isolated_plugin" in _pending_handlers
    assert handler in _pending_handlers["isolated_plugin"]
    assert (
        "__global__" not in _pending_handlers
        or handler not in _pending_handlers.get("__global__", [])
    )
