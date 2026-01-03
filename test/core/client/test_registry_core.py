"""
EventRegistry 核心功能测试
"""

import pytest
from unittest.mock import MagicMock

from ncatbot.core.client.registry import EventRegistry
from ncatbot.core import NcatBotEvent
from ncatbot.core import EventType


class TestEventRegistryInit:
    """测试 EventRegistry 初始化"""

    def test_init_with_event_bus(self, event_bus):
        """使用 EventBus 初始化"""
        registry = EventRegistry(event_bus)
        assert registry.event_bus is event_bus


class TestEventRegistrySubscribe:
    """测试 EventRegistry 核心订阅方法"""

    def test_subscribe_with_event_type_enum(self, event_registry):
        """使用 EventType 枚举订阅"""

        async def handler(event):
            pass

        event_registry.subscribe(EventType.MESSAGE, handler)
        assert "message_event" in event_registry.event_bus._exact

    def test_subscribe_with_string(self, event_registry):
        """使用字符串订阅"""

        async def handler(event):
            pass

        event_registry.subscribe("custom.event", handler)
        assert "custom.event" in event_registry.event_bus._exact

    def test_subscribe_with_priority(self, event_registry):
        """带优先级订阅"""

        async def handler(event):
            pass

        event_registry.subscribe("test.event", handler, priority=100)
        handlers = event_registry.event_bus._exact["test.event"]
        assert handlers[0][1] == 100

    def test_subscribe_with_timeout(self, event_registry):
        """带超时订阅"""

        async def handler(event):
            pass

        event_registry.subscribe("test.event", handler, timeout=30.0)
        handlers = event_registry.event_bus._exact["test.event"]
        assert handlers[0][4] == 30.0


class TestEventRegistryRegisterHandler:
    """测试 register_handler 方法"""

    @pytest.mark.asyncio
    async def test_register_handler_extracts_data(self, event_registry):
        """register_handler 从 NcatBotEvent 提取 data"""
        received_data = []

        async def handler(event):
            received_data.append(event)

        event_registry.register_handler(EventType.MESSAGE, handler)

        mock_event_data = MagicMock()
        mock_event_data.user_id = 12345
        ncatbot_event = NcatBotEvent("message_event", mock_event_data)

        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received_data) == 1
        assert received_data[0].user_id == 12345

    @pytest.mark.asyncio
    async def test_register_handler_with_filter(self, event_registry):
        """带过滤函数的注册"""
        received_data = []

        async def handler(event):
            received_data.append(event)

        def filter_func(event):
            return event.user_id > 1000

        event_registry.register_handler(
            EventType.MESSAGE, handler, filter_func=filter_func
        )

        # 发布被过滤的事件
        mock_event1 = MagicMock()
        mock_event1.user_id = 500
        ncatbot_event1 = NcatBotEvent("message_event", mock_event1)
        await event_registry.event_bus.publish(ncatbot_event1)

        # 发布通过过滤的事件
        mock_event2 = MagicMock()
        mock_event2.user_id = 2000
        ncatbot_event2 = NcatBotEvent("message_event", mock_event2)
        await event_registry.event_bus.publish(ncatbot_event2)

        assert len(received_data) == 1
        assert received_data[0].user_id == 2000

    @pytest.mark.asyncio
    async def test_register_handler_sync_handler(self, event_registry):
        """同步处理器正确执行"""
        received_data = []

        def sync_handler(event):
            received_data.append(event)

        event_registry.register_handler(EventType.MESSAGE, sync_handler)

        mock_event_data = MagicMock()
        ncatbot_event = NcatBotEvent("message_event", mock_event_data)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received_data) == 1


class TestEventRegistryAddHandler:
    """测试 add_handler 兼容方法"""

    def test_add_handler_compatibility(self, event_registry):
        """add_handler 兼容旧接口"""

        async def handler(event):
            pass

        event_registry.add_handler("test.event", handler)
        assert "test.event" in event_registry.event_bus._exact
