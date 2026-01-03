"""
EventRegistry 消息/通知/请求/元事件处理器测试
"""

import pytest
from unittest.mock import MagicMock

from ncatbot.core import NcatBotEvent


class TestEventRegistryMessageHandlers:
    """测试消息处理器注册"""

    @pytest.mark.asyncio
    async def test_add_group_message_handler(
        self, event_registry, mock_group_message_event
    ):
        """群消息处理器注册及过滤"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_group_message_handler(handler)

        ncatbot_event = NcatBotEvent("message_event", mock_group_message_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_group_message_handler_filters_private(
        self, event_registry, mock_private_message_event
    ):
        """群消息处理器过滤私聊消息"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_group_message_handler(handler)

        ncatbot_event = NcatBotEvent("message_event", mock_private_message_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_add_private_message_handler(
        self, event_registry, mock_private_message_event
    ):
        """私聊消息处理器注册及过滤"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_private_message_handler(handler)

        ncatbot_event = NcatBotEvent("message_event", mock_private_message_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_private_message_handler_filters_group(
        self, event_registry, mock_group_message_event
    ):
        """私聊消息处理器过滤群消息"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_private_message_handler(handler)

        ncatbot_event = NcatBotEvent("message_event", mock_group_message_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_add_group_message_with_segment_filter(self, event_registry):
        """带 MessageSegment 过滤的群消息"""
        from ncatbot.core import MessageSegment

        received = []

        async def handler(event):
            received.append(event)

        mock_event = MagicMock()
        mock_event.message_type = "group"
        mock_event.message = MagicMock()
        mock_event.message.filter = MagicMock(return_value=[MagicMock()])

        event_registry.add_group_message_handler(handler, filter=MessageSegment)

        ncatbot_event = NcatBotEvent("message_event", mock_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1


class TestEventRegistryNoticeHandler:
    """测试通知处理器注册"""

    @pytest.mark.asyncio
    async def test_add_notice_handler(self, event_registry, mock_notice_event):
        """通知处理器注册"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_notice_handler(handler)

        ncatbot_event = NcatBotEvent("notice_event", mock_notice_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1


class TestEventRegistryRequestHandlers:
    """测试请求处理器注册"""

    @pytest.mark.asyncio
    async def test_add_group_request_handler(
        self, event_registry, mock_group_request_event
    ):
        """群请求处理器"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_group_request_handler(handler)

        ncatbot_event = NcatBotEvent("request_event", mock_group_request_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_friend_request_handler(
        self, event_registry, mock_friend_request_event
    ):
        """好友请求处理器"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_friend_request_handler(handler)

        ncatbot_event = NcatBotEvent("request_event", mock_friend_request_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_group_request_handler_filters_friend(
        self, event_registry, mock_friend_request_event
    ):
        """群请求处理器过滤好友请求"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_group_request_handler(handler)

        ncatbot_event = NcatBotEvent("request_event", mock_friend_request_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 0

    def test_add_request_handler_deprecated_group(self, event_registry):
        """弃用的 add_request_handler 群过滤"""

        async def handler(event):
            pass

        event_registry.add_request_handler(handler, filter="group")
        assert "request_event" in event_registry.event_bus._exact

    def test_add_request_handler_deprecated_friend(self, event_registry):
        """弃用的 add_request_handler 好友过滤"""

        async def handler(event):
            pass

        event_registry.add_request_handler(handler, filter="friend")
        assert "request_event" in event_registry.event_bus._exact


class TestEventRegistryMetaHandlers:
    """测试元事件处理器注册"""

    @pytest.mark.asyncio
    async def test_add_startup_handler(self, event_registry, mock_startup_event):
        """启动处理器（lifecycle connect）"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_startup_handler(handler)

        ncatbot_event = NcatBotEvent("meta_event", mock_startup_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_heartbeat_handler(self, event_registry, mock_heartbeat_event):
        """心跳处理器"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_heartbeat_handler(handler)

        ncatbot_event = NcatBotEvent("meta_event", mock_heartbeat_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_add_startup_handler_filters_heartbeat(
        self, event_registry, mock_heartbeat_event
    ):
        """启动处理器过滤心跳事件"""
        received = []

        async def handler(event):
            received.append(event)

        event_registry.add_startup_handler(handler)

        ncatbot_event = NcatBotEvent("meta_event", mock_heartbeat_event)
        await event_registry.event_bus.publish(ncatbot_event)

        assert len(received) == 0
