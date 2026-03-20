"""
AsyncEventDispatcher 规范测试

规范:
  D-01: callback 接收 BaseEventData 后推导事件类型
  D-02: events() 返回 EventStream，支持 async for
  D-03: events(type) 精确过滤
  D-04: events(type) 前缀匹配
  D-05: 多消费者同时收到同一事件
  D-06: wait_event(predicate) 只返回满足条件的事件
  D-07: wait_event(timeout) 超时抛 TimeoutError
  D-08: close() 后所有 stream 终止
  D-09: 队列满时丢弃最旧事件不阻塞生产者
"""

import asyncio

import pytest

from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.testing import factory


# ---- D-01: 类型推导 ----


async def test_callback_resolves_group_message_type(event_dispatcher):
    """D-01: GroupMessageEventData → Event.type == 'message.group'"""
    stream = event_dispatcher.events("message.group")
    data = factory.group_message("hi", group_id="1", user_id="2")
    await event_dispatcher.callback(data)

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.type == "message.group"
    await stream.aclose()


async def test_callback_resolves_private_message_type(event_dispatcher):
    """D-01: PrivateMessageEventData → Event.type == 'message.private'"""
    stream = event_dispatcher.events("message.private")
    data = factory.private_message("hi", user_id="3")
    await event_dispatcher.callback(data)

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.type == "message.private"
    await stream.aclose()


async def test_callback_resolves_notice_type(event_dispatcher):
    """D-01: GroupIncreaseNoticeEventData → Event.type 含 'notice'"""
    stream = event_dispatcher.events("notice")
    data = factory.group_increase(user_id="4", group_id="5")
    await event_dispatcher.callback(data)

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.type.startswith("notice")
    await stream.aclose()


# ---- D-02: events() 返回 EventStream ----


async def test_events_returns_stream(event_dispatcher):
    """D-02: events() 返回可异步迭代的 EventStream"""
    stream = event_dispatcher.events()
    data = factory.group_message("test")
    await event_dispatcher.callback(data)

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.data is data
    await stream.aclose()


# ---- D-03: 精确过滤 ----


async def test_events_exact_filter(event_dispatcher):
    """D-03: events('message.group') 不接收 'message.private'"""
    stream = event_dispatcher.events("message.group")

    # 发私聊消息
    await event_dispatcher.callback(factory.private_message("ignored"))
    # 发群消息
    await event_dispatcher.callback(factory.group_message("wanted", group_id="1"))

    event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
    assert event.type == "message.group"
    assert event.data.raw_message == "wanted"
    await stream.aclose()


# ---- D-04: 前缀匹配 ----


async def test_events_prefix_match(event_dispatcher):
    """D-04: events('message') 同时接收 'message.group' 和 'message.private'"""
    stream = event_dispatcher.events("message")
    received = []

    await event_dispatcher.callback(factory.group_message("a", group_id="1"))
    await event_dispatcher.callback(factory.private_message("b", user_id="2"))

    for _ in range(2):
        event = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        received.append(event.type)

    assert "message.group" in received
    assert "message.private" in received
    await stream.aclose()


# ---- D-05: 多消费者 ----


async def test_multiple_consumers(event_dispatcher):
    """D-05: 多个 stream 同时收到同一事件"""
    stream1 = event_dispatcher.events()
    stream2 = event_dispatcher.events()

    data = factory.group_message("broadcast")
    await event_dispatcher.callback(data)

    e1 = await asyncio.wait_for(stream1.__anext__(), timeout=1.0)
    e2 = await asyncio.wait_for(stream2.__anext__(), timeout=1.0)

    assert e1.data is e2.data
    assert e1.data is data
    await stream1.aclose()
    await stream2.aclose()


# ---- D-06: wait_event(predicate) ----


async def test_wait_event_with_predicate(event_dispatcher):
    """D-06: wait_event 只返回满足条件的事件"""

    async def inject_later():
        await asyncio.sleep(0.01)
        await event_dispatcher.callback(factory.group_message("no", group_id="1"))
        await event_dispatcher.callback(factory.group_message("yes", group_id="999"))

    asyncio.create_task(inject_later())

    event = await event_dispatcher.wait_event(
        predicate=lambda e: getattr(e.data, "group_id", None) == "999",
        timeout=2.0,
    )
    assert event.data.group_id == "999"


# ---- D-07: wait_event 超时 ----


async def test_wait_event_timeout(event_dispatcher):
    """D-07: 超时未等到事件 → TimeoutError"""
    with pytest.raises(asyncio.TimeoutError):
        await event_dispatcher.wait_event(timeout=0.05)


# ---- D-08: close() 后 stream 终止 ----


async def test_close_terminates_streams():
    """D-08: close() 后所有 stream 抛 StopAsyncIteration"""
    dispatcher = AsyncEventDispatcher()
    stream = dispatcher.events()

    await dispatcher.close()

    with pytest.raises(StopAsyncIteration):
        await stream.__anext__()


async def test_close_terminates_waiters():
    """D-08 补充: close() 后 wait_event 抛 RuntimeError"""
    dispatcher = AsyncEventDispatcher()

    async def wait_then_close():
        await asyncio.sleep(0.01)
        await dispatcher.close()

    asyncio.create_task(wait_then_close())

    with pytest.raises(RuntimeError, match="已关闭"):
        await dispatcher.wait_event(timeout=2.0)


# ---- D-09: 队列满时丢弃 ----


async def test_full_queue_drops_oldest():
    """D-09: 队列满时丢弃最旧事件，不阻塞生产者"""
    dispatcher = AsyncEventDispatcher(stream_queue_size=3)
    stream = dispatcher.events()

    # 注入 5 条，队列容量 3
    for i in range(5):
        await dispatcher.callback(factory.group_message(f"msg{i}"))

    # 不应阻塞到这里
    events = []
    for _ in range(3):
        e = await asyncio.wait_for(stream.__anext__(), timeout=1.0)
        events.append(e.data.raw_message)

    # 最旧的被丢弃，最新的保留
    assert "msg4" in events
    await stream.aclose()
    await dispatcher.close()
