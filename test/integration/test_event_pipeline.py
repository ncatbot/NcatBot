"""
事件处理流水线集成测试

测试从原始 WebSocket 消息到事件处理器的完整流程：
WebSocket 数据 → EventDispatcher → EventBus → Handler

注意：事件类型格式为 ncatbot.{EventType.value}，即：
- ncatbot.message_event (消息事件)
- ncatbot.message_sent_event (消息发送事件)
- ncatbot.notice_event (通知事件)
- ncatbot.request_event (请求事件)
- ncatbot.meta_event (元事件)
"""

import pytest
import asyncio
from typing import List

from ncatbot.core.client.dispatcher import EventDispatcher
from ncatbot.core.client.ncatbot_event import NcatBotEvent
from ncatbot.core.event.enums import EventType


# 事件类型常量
MESSAGE_EVENT = f"ncatbot.{EventType.MESSAGE.value}"  # ncatbot.message_event
MESSAGE_SENT_EVENT = (
    f"ncatbot.{EventType.MESSAGE_SENT.value}"  # ncatbot.message_sent_event
)
NOTICE_EVENT = f"ncatbot.{EventType.NOTICE.value}"  # ncatbot.notice_event
REQUEST_EVENT = f"ncatbot.{EventType.REQUEST.value}"  # ncatbot.request_event
META_EVENT = f"ncatbot.{EventType.META.value}"  # ncatbot.meta_event


# =============================================================================
# 事件处理流水线基础测试
# =============================================================================


class TestEventPipelineBasic:
    """事件处理流水线基础测试"""

    @pytest.mark.asyncio
    async def test_message_event_full_pipeline(
        self, event_bus, mock_api, sample_message_event
    ):
        """测试消息事件完整流水线"""
        received_events: List[NcatBotEvent] = []

        def handler(event: NcatBotEvent):
            received_events.append(event)

        # 订阅消息事件
        event_bus.subscribe(MESSAGE_EVENT, handler)

        # 创建分发器并分发事件
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        # 验证处理器被调用
        assert len(received_events) == 1
        event = received_events[0]
        assert event.type == MESSAGE_EVENT
        assert event.data.group_id == "701784439"
        assert event.data.raw_message == "Hello"

    @pytest.mark.asyncio
    async def test_private_message_pipeline(
        self, event_bus, mock_api, sample_private_message_event
    ):
        """测试私聊消息流水线"""
        received = []

        event_bus.subscribe(MESSAGE_EVENT, lambda e: received.append(e))

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_private_message_event)

        assert len(received) == 1
        assert received[0].data.user_id == "3051561876"
        assert received[0].data.message_type == "private"

    @pytest.mark.asyncio
    async def test_notice_event_pipeline(
        self, event_bus, mock_api, sample_notice_event
    ):
        """测试通知事件流水线"""
        received = []

        event_bus.subscribe(NOTICE_EVENT, lambda e: received.append(e))

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_notice_event)

        assert len(received) == 1
        assert received[0].data.notice_type == "group_increase"

    @pytest.mark.asyncio
    async def test_request_event_pipeline(
        self, event_bus, mock_api, sample_request_event
    ):
        """测试请求事件流水线"""
        received = []

        event_bus.subscribe(REQUEST_EVENT, lambda e: received.append(e))

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_request_event)

        assert len(received) == 1
        assert received[0].data.request_type == "friend"

    @pytest.mark.asyncio
    async def test_meta_event_pipeline(self, event_bus, mock_api, sample_meta_event):
        """测试元事件流水线"""
        received = []

        event_bus.subscribe(META_EVENT, lambda e: received.append(e))

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_meta_event)

        assert len(received) == 1


# =============================================================================
# 多处理器测试
# =============================================================================


class TestMultipleHandlers:
    """多处理器场景测试"""

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called(
        self, event_bus, mock_api, sample_message_event
    ):
        """测试多个处理器都被调用"""
        call_order = []

        def handler1(e):
            call_order.append("handler1")

        def handler2(e):
            call_order.append("handler2")

        def handler3(e):
            call_order.append("handler3")

        event_bus.subscribe(MESSAGE_EVENT, handler1)
        event_bus.subscribe(MESSAGE_EVENT, handler2)
        event_bus.subscribe(MESSAGE_EVENT, handler3)

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        assert len(call_order) == 3
        assert "handler1" in call_order
        assert "handler2" in call_order
        assert "handler3" in call_order

    @pytest.mark.asyncio
    async def test_handler_priority_order(
        self, event_bus, mock_api, sample_message_event
    ):
        """测试处理器按优先级执行"""
        call_order = []

        def low_priority(e):
            call_order.append("low")

        def high_priority(e):
            call_order.append("high")

        def medium_priority(e):
            call_order.append("medium")

        # 不同优先级注册
        event_bus.subscribe(MESSAGE_EVENT, low_priority, priority=1)
        event_bus.subscribe(MESSAGE_EVENT, high_priority, priority=100)
        event_bus.subscribe(MESSAGE_EVENT, medium_priority, priority=50)

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        # 高优先级先执行
        assert call_order[0] == "high"
        assert call_order[1] == "medium"
        assert call_order[2] == "low"

    @pytest.mark.asyncio
    async def test_async_handlers(self, event_bus, mock_api, sample_message_event):
        """测试异步处理器"""
        results = []

        async def async_handler(e):
            await asyncio.sleep(0.01)
            results.append("async_done")

        event_bus.subscribe(MESSAGE_EVENT, async_handler)

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        assert results == ["async_done"]


# =============================================================================
# 异常处理测试
# =============================================================================


class TestHandlerExceptions:
    """处理器异常场景测试"""

    @pytest.mark.asyncio
    async def test_exception_does_not_stop_other_handlers(
        self, event_bus, mock_api, sample_message_event
    ):
        """测试一个处理器异常不影响其他处理器"""
        results = []

        def good_handler1(e):
            results.append("good1")

        def bad_handler(e):
            raise ValueError("Handler error")

        def good_handler2(e):
            results.append("good2")

        # 高优先级的好处理器
        event_bus.subscribe(MESSAGE_EVENT, good_handler1, priority=100)
        # 中等优先级的坏处理器
        event_bus.subscribe(MESSAGE_EVENT, bad_handler, priority=50)
        # 低优先级的好处理器
        event_bus.subscribe(MESSAGE_EVENT, good_handler2, priority=1)

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        # 两个好处理器都应该执行
        assert "good1" in results
        assert "good2" in results

    @pytest.mark.asyncio
    async def test_async_exception_handling(
        self, event_bus, mock_api, sample_message_event
    ):
        """测试异步处理器异常"""
        results = []

        async def async_bad(e):
            raise RuntimeError("Async error")

        async def async_good(e):
            results.append("async_good")

        event_bus.subscribe(MESSAGE_EVENT, async_bad, priority=100)
        event_bus.subscribe(MESSAGE_EVENT, async_good, priority=1)

        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)

        assert "async_good" in results


# =============================================================================
# 事件订阅/取消订阅测试
# =============================================================================
