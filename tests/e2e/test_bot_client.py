"""
BotClient E2E 测试

规范:
  B-01: TestHarness 启动/停止
  B-02: 注入事件 → handler 执行 → API 记录
  B-03: 多事件流水线
  B-04: handler 调用 event.reply() 产生正确 API
  B-05: settle() 等待 handler 完成
"""

import asyncio


from ncatbot.testing.harness import TestHarness
from ncatbot.event.qq.message import GroupMessageEvent
from ncatbot.testing import factory


# ---- B-01: 启动/停止 ----


async def test_harness_lifecycle():
    """B-01: TestHarness 可正常 start() 和 stop()"""
    harness = TestHarness()
    await harness.start()

    assert harness.bot._running
    assert harness.adapter.connected

    await harness.stop()
    assert not harness.bot._running


async def test_harness_context_manager():
    """B-01 补充: async with TestHarness() 等价"""
    async with TestHarness() as h:
        assert h.bot._running
    assert not h.bot._running


# ---- B-02: 注入 → handler → API ----


async def test_inject_event_triggers_handler():
    """B-02: 注入群消息 → handler 接收 → API 被调用"""
    async with TestHarness() as h:
        received = []

        async def handler(event):
            received.append(event)
            await event.reply("pong")

        h.bot.handler_dispatcher.register_handler("message.group", handler)

        await h.inject(factory.group_message("ping", group_id="111"))
        await h.settle()

        assert len(received) == 1
        assert isinstance(received[0], GroupMessageEvent)
        assert h.api_called("send_group_msg")


# ---- B-03: 多事件 ----


async def test_multiple_events():
    """B-03: 注入多个事件，handler 都收到"""
    async with TestHarness() as h:
        count = 0

        async def counter(event):
            nonlocal count
            count += 1

        h.bot.handler_dispatcher.register_handler("message", counter)

        await h.inject_many(
            [
                factory.group_message("a"),
                factory.private_message("b"),
                factory.group_message("c"),
            ]
        )
        await h.settle(0.1)

        assert count == 3


# ---- B-04: handler 调用 reply ----


async def test_reply_produces_api_call():
    """B-04: event.reply() 产生正确的 send_group_msg 调用"""
    async with TestHarness() as h:

        async def echo(event):
            await event.reply("echo:" + event.raw_message)

        h.bot.handler_dispatcher.register_handler("message.group", echo)

        await h.inject(factory.group_message("hello", group_id="999"))
        await h.settle()

        assert h.api_called("send_group_msg")
        call = h.last_api_call("send_group_msg")
        assert call.args[0] == "999"


# ---- B-05: settle ----


async def test_settle_waits_for_handler():
    """B-05: settle() 等待异步 handler 完成"""
    async with TestHarness() as h:
        done = asyncio.Event()

        async def slow_handler(event):
            await asyncio.sleep(0.02)
            done.set()

        h.bot.handler_dispatcher.register_handler("message.group", slow_handler)

        await h.inject(factory.group_message("slow"))
        await h.settle(0.1)

        assert done.is_set()


# ---- B-02 补充: reset_api 清空记录 ----


async def test_reset_api():
    """B-02 补充: reset_api() 清空 API 调用记录"""
    async with TestHarness() as h:

        async def handler(event):
            await event.reply("r")

        h.bot.handler_dispatcher.register_handler("message.group", handler)

        await h.inject(factory.group_message("first"))
        await h.settle()
        assert h.api_call_count("send_group_msg") == 1

        h.reset_api()
        assert h.api_call_count("send_group_msg") == 0

        await h.inject(factory.group_message("second"))
        await h.settle()
        assert h.api_call_count("send_group_msg") == 1
