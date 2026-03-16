"""
Registrar 堆叠装饰器去重测试

规范:
  R-07: 堆叠装饰器 pending 去重
  R-08: 堆叠装饰器 flush 去重
  R-09: 堆叠装饰器端到端分发去重
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
from ncatbot.testing import factory

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def clean_pending():
    _pending_handlers.clear()
    yield
    _pending_handlers.clear()


# ---- R-07: 堆叠装饰器 pending 去重 ----


def test_stacked_decorators_pending_count():
    """R-07: 堆叠 on_group_message + on_command → pending 只收集 1 次"""
    reg = Registrar()

    @reg.on_group_message()
    @reg.on_command("loli")
    async def handle_loli(event):
        pass

    pending = _pending_handlers.get("__global__", [])
    assert len(pending) == 1


# ---- R-08: 堆叠装饰器 flush 去重 ----


def test_stacked_decorators_register_count():
    """R-08: flush 后同一函数只注册 1 个 entry"""
    reg = Registrar()
    hd = HandlerDispatcher(api=MockBotAPI())

    @reg.on_group_message()
    @reg.on_command("loli")
    async def handle_loli(event):
        pass

    count = flush_pending(hd, "__global__")
    assert count == 1
    assert len(hd.get_handlers("message")) == 1


# ---- R-09: 堆叠装饰器端到端分发去重 ----


async def test_stacked_decorators_dispatch_count():
    """R-09: 注入一条群消息，handler 只执行 1 次"""
    reg = Registrar()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=MockBotAPI())
    hd.start(ed)

    call_count = 0

    @reg.on_group_message()
    @reg.on_command("loli")
    async def handle_loli(event):
        nonlocal call_count
        call_count += 1

    flush_pending(hd, "__global__")

    await ed.callback(factory.group_message("loli", group_id="701784439"))
    await asyncio.sleep(0.1)

    assert call_count == 1

    await hd.stop()
    await ed.close()

    await ed.close()
