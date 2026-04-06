"""
Session 便利方法规范测试

规范:
  M-50: wait_session_event — 自动 session 绑定（同用户同群）
  M-51: wait_session_event — extra_predicate AND 组合
  M-52: wait_session_event — cancel_words → SessionCancelled
  M-53: wait_session_event — timeout → TimeoutError
  M-54: wait_session_reply — 正常回复 → SessionResult(ok=True)
  M-55: wait_session_reply — 超时 → SessionResult(timed_out=True)
  M-56: wait_session_reply — 取消 → SessionResult(cancelled=True)
  M-57: session_prompt — 发送提示 + 等待 + 自动回复
  M-58: session_choose — 正确选择 → .key
  M-59: session_choose — 无效输入 + 重试 + 耗尽
"""

import asyncio

import pytest
import pytest_asyncio

from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.plugin.mixin.event_mixin import EventMixin
from ncatbot.plugin.mixin.session_types import SessionCancelled
from ncatbot.testing.factories import qq as factory


class FakePlugin(EventMixin):
    """最小 EventMixin 实例"""

    def __init__(self, dispatcher):
        self._dispatcher = dispatcher


class FakeEvent:
    """模拟高层事件对象，提供 user_id / group_id / reply()"""

    def __init__(self, user_id="99999", group_id="100200"):
        self.user_id = user_id
        self.group_id = group_id
        self.message_type = "group"
        self.replies = []

    async def reply(self, text):
        self.replies.append(text)


@pytest_asyncio.fixture
async def env():
    """创建 dispatcher + plugin + fake event"""
    dispatcher = AsyncEventDispatcher()
    plugin = FakePlugin(dispatcher)
    event = FakeEvent()
    yield plugin, dispatcher, event
    await dispatcher.close()


async def _inject_after(dispatcher, data, delay=0.01):
    """延迟注入事件"""
    await asyncio.sleep(delay)
    await dispatcher.callback(data)


# ---- M-50: wait_session_event — 自动 session 绑定 ----


async def test_wait_session_event_binds_session(env):
    """M-50: wait_session_event 自动绑定同用户同群"""
    plugin, dispatcher, event = env

    # 注入同用户同群的消息
    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("reply", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.wait_session_event(event, timeout=2.0)
    assert result.data.raw_message == "reply"


async def test_wait_session_event_ignores_other_user(env):
    """M-50 补充: 不同用户的消息被忽略"""
    plugin, dispatcher, event = env

    # 先注入不同用户的消息，再注入正确用户的
    async def inject_sequence():
        await asyncio.sleep(0.01)
        await dispatcher.callback(
            factory.group_message("wrong", user_id="11111", group_id="100200")
        )
        await asyncio.sleep(0.01)
        await dispatcher.callback(
            factory.group_message("right", user_id="99999", group_id="100200")
        )

    asyncio.create_task(inject_sequence())

    result = await plugin.wait_session_event(event, timeout=2.0)
    assert result.data.raw_message == "right"


# ---- M-51: wait_session_event — extra_predicate ----


async def test_wait_session_event_extra_predicate(env):
    """M-51: extra_predicate 与 session 谓词 AND 组合"""
    plugin, dispatcher, event = env

    async def inject_sequence():
        await asyncio.sleep(0.01)
        # 同 session 但不满足额外条件
        await dispatcher.callback(
            factory.group_message("nope", user_id="99999", group_id="100200")
        )
        await asyncio.sleep(0.01)
        # 同 session 且满足额外条件
        await dispatcher.callback(
            factory.group_message("yes", user_id="99999", group_id="100200")
        )

    asyncio.create_task(inject_sequence())

    result = await plugin.wait_session_event(
        event,
        timeout=2.0,
        extra_predicate=lambda e: getattr(e.data, "raw_message", "") == "yes",
    )
    assert result.data.raw_message == "yes"


# ---- M-52: wait_session_event — cancel_words ----


async def test_wait_session_event_cancel_words(env):
    """M-52: cancel_words 触发 SessionCancelled"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("取消", user_id="99999", group_id="100200"),
        )
    )

    with pytest.raises(SessionCancelled) as exc_info:
        await plugin.wait_session_event(
            event,
            timeout=2.0,
            cancel_words=["取消", "退出"],
        )

    assert exc_info.value.word == "取消"
    assert exc_info.value.event.data.raw_message == "取消"


async def test_wait_session_event_cancel_words_no_match(env):
    """M-52 补充: 非取消词正常返回"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("继续", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.wait_session_event(
        event,
        timeout=2.0,
        cancel_words=["取消"],
    )
    assert result.data.raw_message == "继续"


# ---- M-53: wait_session_event — timeout ----


async def test_wait_session_event_timeout(env):
    """M-53: timeout → TimeoutError"""
    plugin, _, event = env
    with pytest.raises(asyncio.TimeoutError):
        await plugin.wait_session_event(event, timeout=0.05)


# ---- M-54: wait_session_reply — 正常回复 ----


async def test_wait_session_reply_success(env):
    """M-54: 正常回复 → SessionResult(ok=True, text=...)"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("  张三  ", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.wait_session_reply(event, timeout=2.0)
    assert result.ok is True
    assert result.text == "张三"
    assert result.event is not None
    assert result.cancelled is False
    assert result.timed_out is False


# ---- M-55: wait_session_reply — 超时 ----


async def test_wait_session_reply_timeout(env):
    """M-55: 超时 → SessionResult(timed_out=True)"""
    plugin, _, event = env

    result = await plugin.wait_session_reply(event, timeout=0.05)
    assert result.ok is False
    assert result.timed_out is True
    assert result.text is None
    assert result.event is None


# ---- M-56: wait_session_reply — 取消 ----


async def test_wait_session_reply_cancelled(env):
    """M-56: 取消词 → SessionResult(cancelled=True)"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("退出", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.wait_session_reply(
        event,
        timeout=2.0,
        cancel_words=["取消", "退出"],
    )
    assert result.ok is False
    assert result.cancelled is True
    assert result.cancel_word == "退出"
    assert result.event is not None


# ---- M-57: session_prompt — 发送提示 + 等待 + 自动回复 ----


async def test_session_prompt_success(env):
    """M-57: 发送提示 → 等回复 → 返回结果"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("李四", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.session_prompt("请输入名字", event, timeout=2.0)
    assert event.replies == ["请输入名字"]
    assert result.ok is True
    assert result.text == "李四"


async def test_session_prompt_timeout_auto_reply(env):
    """M-57 补充: 超时时自动回复"""
    plugin, _, event = env

    result = await plugin.session_prompt(
        "请输入",
        event,
        timeout=0.05,
        timeout_reply="⏰ 超时了",
    )
    assert result.ok is False
    assert result.timed_out is True
    assert "请输入" in event.replies
    assert "⏰ 超时了" in event.replies


async def test_session_prompt_cancel_auto_reply(env):
    """M-57 补充: 取消时自动回复"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("取消", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.session_prompt(
        "请输入",
        event,
        timeout=2.0,
        cancel_words=["取消"],
        cancel_reply="❌ 已取消",
    )
    assert result.ok is False
    assert result.cancelled is True
    assert "❌ 已取消" in event.replies


# ---- M-58: session_choose — 正确选择 ----


async def test_session_choose_valid_choice(env):
    """M-58: 有效选择 → .key 返回映射值"""
    plugin, dispatcher, event = env

    asyncio.create_task(
        _inject_after(
            dispatcher,
            factory.group_message("确认", user_id="99999", group_id="100200"),
        )
    )

    result = await plugin.session_choose(
        "确认注册？",
        event,
        choices={"确认": "confirm", "取消": "cancel"},
        timeout=2.0,
    )
    assert result.ok is True
    assert result.key == "confirm"
    assert result.text == "确认"
    assert "确认注册？" in event.replies


# ---- M-59: session_choose — 无效输入 + 重试 + 耗尽 ----


async def test_session_choose_invalid_then_valid(env):
    """M-59: 无效输入 → 重试 → 有效输入"""
    plugin, dispatcher, event = env

    async def inject_sequence():
        await asyncio.sleep(0.01)
        await dispatcher.callback(
            factory.group_message("啥？", user_id="99999", group_id="100200")
        )
        await asyncio.sleep(0.05)
        await dispatcher.callback(
            factory.group_message("确认", user_id="99999", group_id="100200")
        )

    asyncio.create_task(inject_sequence())

    result = await plugin.session_choose(
        "确认？",
        event,
        choices={"确认": "confirm", "取消": "cancel"},
        timeout=2.0,
        max_retries=1,
        invalid_reply="请选择：确认/取消",
    )
    assert result.ok is True
    assert result.key == "confirm"
    assert "请选择：确认/取消" in event.replies


async def test_session_choose_retries_exhausted(env):
    """M-59 补充: 重试耗尽 → SessionResult(ok=False)"""
    plugin, dispatcher, event = env

    async def inject_sequence():
        await asyncio.sleep(0.01)
        await dispatcher.callback(
            factory.group_message("啥", user_id="99999", group_id="100200")
        )
        await asyncio.sleep(0.05)
        await dispatcher.callback(
            factory.group_message("啊", user_id="99999", group_id="100200")
        )

    asyncio.create_task(inject_sequence())

    result = await plugin.session_choose(
        "确认？",
        event,
        choices={"确认": "confirm"},
        timeout=2.0,
        max_retries=1,
        invalid_reply="无效",
    )
    assert result.ok is False
    assert result.text == "啊"  # 最后一次输入


async def test_session_choose_timeout(env):
    """M-59 补充: 选择超时"""
    plugin, _, event = env

    result = await plugin.session_choose(
        "确认？",
        event,
        choices={"确认": "confirm"},
        timeout=0.05,
        timeout_reply="超时了",
    )
    assert result.ok is False
    assert result.timed_out is True
    assert "超时了" in event.replies
