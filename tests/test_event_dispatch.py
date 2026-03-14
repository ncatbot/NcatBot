"""
事件分发测试 — 验证事件从 MockAdapter 注入后能正确路由到 dispatcher
"""

import asyncio

import pytest

from ncatbot.testing import TestHarness
from ncatbot.testing import factory


pytestmark = pytest.mark.asyncio


# ---- 基础路由 ----


async def test_group_message_dispatched(harness: TestHarness):
    """群消息事件能被 dispatcher 正确接收"""
    stream = harness.dispatcher.events("message.group")

    msg = factory.group_message("你好", group_id="12345", user_id="67890")
    await harness.inject(msg)

    event = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
    assert event.type == "message.group"
    assert event.data.group_id == "12345"
    assert event.data.raw_message == "你好"

    await stream.aclose()


async def test_private_message_dispatched(harness: TestHarness):
    """私聊消息事件能被 dispatcher 正确接收"""
    stream = harness.dispatcher.events("message.private")

    msg = factory.private_message("hello", user_id="11111")
    await harness.inject(msg)

    event = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
    assert event.type == "message.private"
    assert event.data.user_id == "11111"
    assert event.data.raw_message == "hello"

    await stream.aclose()


async def test_notice_dispatched(harness: TestHarness):
    """通知事件能被 dispatcher 正确路由"""
    stream = harness.dispatcher.events("notice")

    notice = factory.group_increase(user_id="55555", group_id="12345")
    await harness.inject(notice)

    event = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
    assert event.type == "notice.group_increase"
    assert event.data.user_id == "55555"

    await stream.aclose()


async def test_request_dispatched(harness: TestHarness):
    """请求事件能被 dispatcher 正确路由"""
    stream = harness.dispatcher.events("request")

    req = factory.friend_request(user_id="77777", comment="加我好友")
    await harness.inject(req)

    event = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
    assert event.type == "request.friend"

    await stream.aclose()


# ---- 过滤 ----


async def test_stream_filters_by_prefix(harness: TestHarness):
    """事件流按前缀过滤：'message.group' 不接收 'message.private'"""
    group_stream = harness.dispatcher.events("message.group")

    # 注入私聊消息 — 不应被 group_stream 接收
    await harness.inject(factory.private_message("私聊"))
    # 注入群消息 — 应被接收
    await harness.inject(factory.group_message("群消息"))

    event = await asyncio.wait_for(group_stream.__anext__(), timeout=2.0)
    assert event.type == "message.group"
    assert event.data.raw_message == "群消息"

    await group_stream.aclose()


# ---- wait_event ----


async def test_wait_event_with_predicate(harness: TestHarness):
    """dispatcher.wait_event 能按条件等待特定事件"""

    async def inject_later():
        await asyncio.sleep(0.02)
        await harness.inject(factory.group_message("target", group_id="999"))

    asyncio.create_task(inject_later())

    event = await harness.dispatcher.wait_event(
        predicate=lambda e: e.type == "message.group",
        timeout=2.0,
    )
    assert event.data.group_id == "999"


# ---- 多事件 ----


async def test_multiple_events_in_order(harness: TestHarness):
    """多个事件按注入顺序到达"""
    stream = harness.dispatcher.events("message.group")

    for i in range(5):
        await harness.inject(factory.group_message(f"msg_{i}"))

    for i in range(5):
        event = await asyncio.wait_for(stream.__anext__(), timeout=2.0)
        assert event.data.raw_message == f"msg_{i}"

    await stream.aclose()
