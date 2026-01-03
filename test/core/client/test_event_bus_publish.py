"""
EventBus 发布和执行测试
"""

import asyncio

import pytest

from ncatbot.core.client.event_bus import HandlerTimeoutError
from ncatbot.core import NcatBotEvent


class TestEventBusPublish:
    """测试 EventBus 事件发布"""

    @pytest.mark.asyncio
    async def test_publish_exact_match(self, event_bus):
        """发布事件触发精确匹配处理器"""
        results = []

        async def handler(event):
            results.append(event.type)
            return "handled"

        event_bus.subscribe("test.event", handler)
        event = NcatBotEvent("test.event", {"data": "test"})

        await event_bus.publish(event)

        assert results == ["test.event"]
        assert event.results == ["handled"]

    @pytest.mark.asyncio
    async def test_publish_prefix_match(self, event_bus):
        """前缀匹配触发"""
        results = []

        async def prefix_handler(event):
            results.append("prefix")
            return "prefix_handled"

        async def exact_handler(event):
            results.append("exact")
            return "exact_handled"

        event_bus.subscribe("ncatbot.notice", prefix_handler)
        event_bus.subscribe("ncatbot.notice.group_increase", exact_handler)

        event = NcatBotEvent("ncatbot.notice.group_increase", {})
        await event_bus.publish(event)

        assert "exact" in results
        assert "prefix" in results

    @pytest.mark.asyncio
    async def test_publish_regex_match(self, event_bus):
        """正则匹配触发"""
        results = []

        async def handler(event):
            results.append(event.type)

        event_bus.subscribe("re:ncatbot\\.notice\\..*", handler)

        event = NcatBotEvent("ncatbot.notice.group_increase", {})
        await event_bus.publish(event)

        assert results == ["ncatbot.notice.group_increase"]

    @pytest.mark.asyncio
    async def test_publish_no_match(self, event_bus):
        """无匹配处理器时正常返回"""
        event = NcatBotEvent("unmatched.event", {})
        results = await event_bus.publish(event)
        assert results == []

    @pytest.mark.asyncio
    async def test_publish_multiple_handlers(self, event_bus):
        """多个处理器都被调用"""
        call_order = []

        async def handler1(event):
            call_order.append(1)
            return 1

        async def handler2(event):
            call_order.append(2)
            return 2

        event_bus.subscribe("test.event", handler1)
        event_bus.subscribe("test.event", handler2)

        event = NcatBotEvent("test.event", {})
        results = await event_bus.publish(event)

        assert len(call_order) == 2
        assert set(results) == {1, 2}


class TestEventBusPriority:
    """测试处理器优先级"""

    @pytest.mark.asyncio
    async def test_handler_priority_order(self, event_bus):
        """高优先级处理器先执行"""
        call_order = []

        async def low_priority(event):
            call_order.append("low")

        async def high_priority(event):
            call_order.append("high")

        async def medium_priority(event):
            call_order.append("medium")

        event_bus.subscribe("test.event", low_priority, priority=1)
        event_bus.subscribe("test.event", high_priority, priority=100)
        event_bus.subscribe("test.event", medium_priority, priority=50)

        event = NcatBotEvent("test.event", {})
        await event_bus.publish(event)

        assert call_order == ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_stop_propagation_in_handler(self, event_bus):
        """处理器中调用 stop_propagation()"""
        call_order = []

        async def first_handler(event):
            call_order.append("first")
            event.stop_propagation()

        async def second_handler(event):
            call_order.append("second")

        event_bus.subscribe("test.event", first_handler, priority=100)
        event_bus.subscribe("test.event", second_handler, priority=1)

        event = NcatBotEvent("test.event", {})
        await event_bus.publish(event)

        assert call_order == ["first"]


class TestEventBusTimeout:
    """测试处理器超时"""

    @pytest.mark.asyncio
    async def test_handler_timeout(self, event_bus_short_timeout):
        """处理器超时触发 HandlerTimeoutError"""

        async def slow_handler(event):
            await asyncio.sleep(0.12)
            return "done"

        event_bus_short_timeout.subscribe("test.event", slow_handler)

        event = NcatBotEvent("test.event", {})
        await event_bus_short_timeout.publish(event)

        assert len(event.exceptions) == 1
        assert isinstance(event.exceptions[0], HandlerTimeoutError)

    @pytest.mark.asyncio
    async def test_handler_custom_timeout(self, event_bus):
        """自定义超时时间"""

        async def slow_handler(event):
            await asyncio.sleep(0.02)
            return "done"

        event_bus.subscribe("test.event", slow_handler, timeout=0.01)

        event = NcatBotEvent("test.event", {})
        await event_bus.publish(event)

        assert len(event.exceptions) == 1
        assert isinstance(event.exceptions[0], HandlerTimeoutError)

    def test_handler_timeout_error_str(self):
        """测试 HandlerTimeoutError 字符串表示"""
        error = HandlerTimeoutError(
            meta_data={"name": "TestPlugin"}, handler="test_handler", time=5.0
        )

        error_str = str(error)

        assert "TestPlugin" in error_str
        assert "test_handler" in error_str
        assert "5" in error_str


class TestEventBusExceptionHandling:
    """测试异常处理"""

    @pytest.mark.asyncio
    async def test_handler_exception_captured(self, event_bus):
        """处理器异常被捕获到 event.exceptions"""

        async def failing_handler(event):
            raise ValueError("Handler error")

        async def normal_handler(event):
            return "ok"

        event_bus.subscribe("test.event", failing_handler, priority=100)
        event_bus.subscribe("test.event", normal_handler, priority=1)

        event = NcatBotEvent("test.event", {})
        results = await event_bus.publish(event)

        assert len(event.exceptions) == 1
        assert isinstance(event.exceptions[0], ValueError)
        assert "ok" in results


class TestEventBusHandlerTypes:
    """测试不同类型的处理器"""

    @pytest.mark.asyncio
    async def test_async_handler_execution(self, event_bus):
        """异步处理器正确执行"""
        result = []

        async def async_handler(event):
            await asyncio.sleep(0.01)
            result.append("async")
            return "async_result"

        event_bus.subscribe("test.event", async_handler)

        event = NcatBotEvent("test.event", {})
        results = await event_bus.publish(event)

        assert result == ["async"]
        assert "async_result" in results

    @pytest.mark.asyncio
    async def test_sync_handler_execution(self, event_bus):
        """同步处理器正确执行（to_thread）"""
        result = []

        def sync_handler(event):
            result.append("sync")
            return "sync_result"

        event_bus.subscribe("test.event", sync_handler)

        event = NcatBotEvent("test.event", {})
        results = await event_bus.publish(event)

        assert result == ["sync"]
        assert "sync_result" in results
