"""
EventRegistry 装饰器和集成测试
"""

import pytest
from unittest.mock import MagicMock

from ncatbot.core import NcatBotEvent


class TestEventRegistryDecorators:
    """测试装饰器接口"""

    def test_on_group_message_decorator(self, event_registry):
        """@on_group_message() 装饰器"""

        @event_registry.on_group_message()
        async def handler(event):
            pass

        assert "message_event" in event_registry.event_bus._exact

    def test_on_group_message_returns_function(self, event_registry):
        """装饰器返回原函数"""

        async def handler(event):
            return "result"

        decorated = event_registry.on_group_message()(handler)
        assert decorated is handler

    def test_on_private_message_decorator(self, event_registry):
        """@on_private_message() 装饰器"""

        @event_registry.on_private_message()
        async def handler(event):
            pass

        assert "message_event" in event_registry.event_bus._exact

    def test_on_notice_decorator(self, event_registry):
        """@on_notice() 装饰器"""

        @event_registry.on_notice()
        async def handler(event):
            pass

        assert "notice_event" in event_registry.event_bus._exact

    def test_on_notice_with_type(self, event_registry):
        """@on_notice(notice_type="group_increase")"""

        @event_registry.on_notice(notice_type="group_increase")
        async def handler(event):
            pass

        assert "notice.group_increase" in event_registry.event_bus._exact

    def test_on_request_decorator_deprecated(self, event_registry):
        """@on_request() 弃用装饰器"""

        @event_registry.on_request()
        async def handler(event):
            pass

        assert "request_event" in event_registry.event_bus._exact

    def test_on_group_request_decorator(self, event_registry):
        """@on_group_request() 装饰器"""

        @event_registry.on_group_request()
        async def handler(event):
            pass

        assert "request_event" in event_registry.event_bus._exact

    def test_on_friend_request_decorator(self, event_registry):
        """@on_friend_request() 装饰器"""

        @event_registry.on_friend_request()
        async def handler(event):
            pass

        assert "request_event" in event_registry.event_bus._exact

    def test_on_startup_decorator(self, event_registry):
        """@on_startup() 装饰器"""

        @event_registry.on_startup()
        async def handler(event):
            pass

        assert "meta_event" in event_registry.event_bus._exact

    def test_on_shutdown_decorator(self, event_registry):
        """@on_shutdown() 装饰器"""

        @event_registry.on_shutdown()
        async def handler(event):
            pass

        assert "meta_event" in event_registry.event_bus._exact

    def test_on_heartbeat_decorator(self, event_registry):
        """@on_heartbeat() 装饰器"""

        @event_registry.on_heartbeat()
        async def handler(event):
            pass

        assert "meta_event" in event_registry.event_bus._exact

    def test_on_message_sent_decorator(self, event_registry):
        """@on_message_sent() 装饰器"""

        @event_registry.on_message_sent()
        async def handler(event):
            pass

        assert "message_sent_event" in event_registry.event_bus._exact


class TestEventRegistryIntegration:
    """EventRegistry 集成测试"""

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_registry):
        """同一事件多个处理器"""
        results = []

        @event_registry.on_group_message()
        async def handler1(event):
            results.append("handler1")

        @event_registry.on_group_message()
        async def handler2(event):
            results.append("handler2")

        mock_event = MagicMock()
        mock_event.message_type = "group"
        ncatbot_event = NcatBotEvent("message_event", mock_event)

        await event_registry.event_bus.publish(ncatbot_event)

        assert len(results) == 2
        assert "handler1" in results
        assert "handler2" in results

    @pytest.mark.asyncio
    async def test_decorator_with_filter(self, event_registry):
        """装饰器带过滤器"""
        from ncatbot.core import MessageSegment

        results = []

        @event_registry.on_group_message(filter=MessageSegment)
        async def handler(event):
            results.append(event)

        mock_event = MagicMock()
        mock_event.message_type = "group"
        mock_event.message = MagicMock()
        mock_event.message.filter = MagicMock(return_value=[MagicMock()])

        ncatbot_event = NcatBotEvent("message_event", mock_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(results) == 1
