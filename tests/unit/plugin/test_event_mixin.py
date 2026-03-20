"""
EventMixin 规范测试

规范:
  M-20: events() 返回 EventStream 并追踪
  M-21: wait_event(timeout) 超时 → TimeoutError
  M-22: _mixin_unload() 关闭所有活跃 stream
"""

import asyncio

import pytest
import pytest_asyncio

from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.plugin.mixin.event_mixin import EventMixin
from ncatbot.testing import factory


class FakePlugin(EventMixin):
    """最小 EventMixin 实例"""

    def __init__(self, dispatcher):
        self._dispatcher = dispatcher


@pytest_asyncio.fixture
async def mixin_env():
    """创建 dispatcher + plugin"""
    dispatcher = AsyncEventDispatcher()
    plugin = FakePlugin(dispatcher)
    yield plugin, dispatcher
    await dispatcher.close()


# ---- M-20: events() 返回 EventStream ----


async def test_events_returns_stream(mixin_env):
    """M-20: events() 创建 EventStream 并追踪"""
    plugin, dispatcher = mixin_env
    stream = plugin.events("message")

    assert stream is not None
    assert stream in plugin._active_streams

    data = factory.group_message("test")
    await dispatcher.callback(data)

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.data is data
    await stream.aclose()


async def test_events_multiple_streams(mixin_env):
    """M-20 补充: 多个 stream 都被追踪"""
    plugin, dispatcher = mixin_env
    s1 = plugin.events("message")
    s2 = plugin.events("notice")

    assert len(plugin._active_streams) == 2
    await s1.aclose()
    await s2.aclose()


# ---- M-21: wait_event timeout ----


async def test_wait_event_timeout(mixin_env):
    """M-21: wait_event 超时 → TimeoutError"""
    plugin, _ = mixin_env
    with pytest.raises(asyncio.TimeoutError):
        await plugin.wait_event(timeout=0.05)


async def test_wait_event_success(mixin_env):
    """M-21 补充: wait_event 满足条件 → 返回事件"""
    plugin, dispatcher = mixin_env

    async def inject():
        await asyncio.sleep(0.01)
        await dispatcher.callback(factory.group_message("target", group_id="999"))

    asyncio.create_task(inject())

    event = await plugin.wait_event(
        predicate=lambda e: getattr(e.data, "group_id", None) == "999",
        timeout=2.0,
    )
    assert event.data.group_id == "999"


# ---- M-22: _mixin_unload 关闭 streams ----


async def test_mixin_unload_closes_streams(mixin_env):
    """M-22: _mixin_unload() 关闭所有活跃 stream"""
    plugin, dispatcher = mixin_env
    s1 = plugin.events()
    _s2 = plugin.events()

    assert len(plugin._active_streams) == 2

    await plugin._mixin_unload()

    # close 后 stream 应终止
    with pytest.raises(StopAsyncIteration):
        await s1.__anext__()
