"""
事件管线集成测试

规范:
  I-01: Dispatcher → HandlerDispatcher → handler 全链路
  I-02: 多类型事件混发，handler 只收到匹配的
  I-03: Hook 过滤 + handler 执行全链路
"""

import asyncio


from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.core.registry.dispatcher import HandlerDispatcher
from ncatbot.core.registry.builtin_hooks import MessageTypeFilter
from ncatbot.core.registry.hook import add_hooks
from ncatbot.event.qq.message import GroupMessageEvent
from ncatbot.testing import factory


# ---- I-01: 全链路 ----


async def test_full_pipeline():
    """I-01: 事件 → Dispatcher → HandlerDispatcher → handler 收到 EventEntity"""
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api, platform_apis={"qq": api})
    hd.start(ed)

    received = []

    async def handler(event):
        received.append(event)

    hd.register_handler("message.group", handler)

    await ed.callback(factory.group_message("hello", group_id="111"))
    await asyncio.sleep(0.05)

    assert len(received) == 1
    assert isinstance(received[0], GroupMessageEvent)
    assert received[0].raw_message == "hello"
    assert received[0].group_id == "111"

    await hd.stop()
    await ed.close()


# ---- I-02: 多类型事件混发 ----


async def test_mixed_events_filtered():
    """I-02: 注册 'message.group' handler 只收群消息，不收私聊和通知"""
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api, platform_apis={"qq": api})
    hd.start(ed)

    group_msgs = []
    all_msgs = []

    async def group_handler(event):
        group_msgs.append(event)

    async def all_handler(event):
        all_msgs.append(event)

    hd.register_handler("message.group", group_handler)
    hd.register_handler("message", all_handler)

    # 发送 3 种不同类型的事件
    await ed.callback(factory.group_message("group1", group_id="1"))
    await ed.callback(factory.private_message("private1"))
    await ed.callback(factory.group_increase(user_id="1"))
    await asyncio.sleep(0.1)

    # group_handler 只收到群消息
    assert len(group_msgs) == 1
    assert group_msgs[0].raw_message == "group1"

    # all_handler 收到所有 message 类型（群+私聊）
    assert len(all_msgs) == 2

    await hd.stop()
    await ed.close()


# ---- I-03: Hook 过滤全链路 ----


async def test_hook_filter_in_pipeline():
    """I-03: MessageTypeFilter(group) 在全链路中过滤私聊"""
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api, platform_apis={"qq": api})
    hd.start(ed)

    received = []

    @add_hooks(MessageTypeFilter("group"))
    async def filtered_handler(event):
        received.append(event)

    # 注册到 "message"（不是 "message.group"）
    hd.register_handler("message", filtered_handler)

    # 发送一条群消息和一条私聊
    await ed.callback(factory.group_message("from_group", group_id="1"))
    await ed.callback(factory.private_message("from_private"))
    await asyncio.sleep(0.05)

    # 只有群消息通过了 Hook 过滤
    assert len(received) == 1
    assert received[0].raw_message == "from_group"

    await hd.stop()
    await ed.close()


# ---- I-01 补充: handler 可调用 API ----


async def test_handler_api_call():
    """I-01 补充: handler 中调用 event.reply() → MockAPI 记录调用"""
    api = MockBotAPI()
    ed = AsyncEventDispatcher()
    hd = HandlerDispatcher(api=api, platform_apis={"qq": api})
    hd.start(ed)

    async def echo_handler(event):
        await event.reply("echo: " + event.raw_message)

    hd.register_handler("message.group", echo_handler)

    await ed.callback(factory.group_message("ping", group_id="1"))
    await asyncio.sleep(0.05)

    assert api.called("send_group_msg")
    call = api.last_call("send_group_msg")
    assert call.args[0] == "1"  # group_id
    assert "echo: ping" in str(call.args[1])  # message

    await hd.stop()
    await ed.close()
