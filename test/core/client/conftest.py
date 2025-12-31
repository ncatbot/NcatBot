"""
Client 模块测试共享 fixtures
"""
import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.ncatbot_event import NcatBotEvent
from ncatbot.core.client.dispatcher import EventDispatcher
from ncatbot.core.client.registry import EventRegistry


# ==================== EventBus Fixtures ====================

@pytest.fixture
def event_bus():
    """创建一个新的 EventBus 实例"""
    return EventBus(default_timeout=5.0)


@pytest.fixture
def event_bus_short_timeout():
    """创建一个短超时的 EventBus 实例（用于超时测试）"""
    return EventBus(default_timeout=0.1)


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_api():
    """Mock 的 BotAPI 实例"""
    api = MagicMock()
    api.send = AsyncMock()
    api.send_group_msg = AsyncMock()
    api.send_private_msg = AsyncMock()
    return api


@pytest.fixture
def mock_adapter():
    """Mock 的 Adapter 实例"""
    adapter = MagicMock()
    adapter.send = AsyncMock()
    adapter.connect = AsyncMock()
    adapter.set_event_callback = MagicMock()
    return adapter


@pytest.fixture
def mock_services():
    """Mock 的 ServiceManager 实例"""
    from ncatbot.core.service import ServiceManager
    services = MagicMock(spec=ServiceManager)
    services.load_all = AsyncMock()
    services.close_all = AsyncMock()
    services.get = MagicMock(return_value=MagicMock())
    return services


# ==================== EventRegistry Fixtures ====================

@pytest.fixture
def event_registry(event_bus):
    """创建 EventRegistry 实例"""
    return EventRegistry(event_bus)


# ==================== EventDispatcher Fixtures ====================

@pytest.fixture
def event_dispatcher(event_bus, mock_api):
    """创建 EventDispatcher 实例"""
    return EventDispatcher(event_bus, mock_api)


# ==================== Sample Event Data Fixtures ====================

@pytest.fixture
def sample_message_event_data() -> Dict[str, Any]:
    """示例群消息事件原始数据"""
    return {
        "post_type": "message",
        "message_type": "group",
        "sub_type": "normal",
        "message_id": 12345,
        "group_id": 123456789,
        "user_id": 987654321,
        "anonymous": None,
        "message": [{"type": "text", "data": {"text": "Hello, world!"}}],
        "raw_message": "Hello, world!",
        "font": 0,
        "sender": {
            "user_id": 987654321,
            "nickname": "TestUser",
            "card": "",
            "sex": "unknown",
            "age": 0,
            "area": "",
            "level": "1",
            "role": "member",
            "title": ""
        },
        "time": 1640000000,
        "self_id": 111111111
    }


@pytest.fixture
def sample_private_message_event_data() -> Dict[str, Any]:
    """示例私聊消息事件原始数据"""
    return {
        "post_type": "message",
        "message_type": "private",
        "sub_type": "friend",
        "message_id": 12346,
        "user_id": 987654321,
        "message": [{"type": "text", "data": {"text": "Hello!"}}],
        "raw_message": "Hello!",
        "font": 0,
        "sender": {
            "user_id": 987654321,
            "nickname": "TestUser",
            "sex": "unknown",
            "age": 0
        },
        "time": 1640000001,
        "self_id": 111111111
    }


@pytest.fixture
def sample_notice_event_data() -> Dict[str, Any]:
    """示例通知事件原始数据"""
    return {
        "post_type": "notice",
        "notice_type": "group_increase",
        "sub_type": "approve",
        "group_id": 123456789,
        "operator_id": 111111111,
        "user_id": 222222222,
        "time": 1640000002,
        "self_id": 111111111
    }


@pytest.fixture
def sample_request_event_data() -> Dict[str, Any]:
    """示例群请求事件原始数据"""
    return {
        "post_type": "request",
        "request_type": "group",
        "sub_type": "add",
        "group_id": 123456789,
        "user_id": 333333333,
        "comment": "请求加群",
        "flag": "flag_123456",
        "time": 1640000003,
        "self_id": 111111111
    }


@pytest.fixture
def sample_friend_request_event_data() -> Dict[str, Any]:
    """示例好友请求事件原始数据"""
    return {
        "post_type": "request",
        "request_type": "friend",
        "user_id": 444444444,
        "comment": "请求添加好友",
        "flag": "flag_789012",
        "time": 1640000004,
        "self_id": 111111111
    }


@pytest.fixture
def sample_meta_event_data() -> Dict[str, Any]:
    """示例元事件原始数据（生命周期连接）"""
    return {
        "post_type": "meta_event",
        "meta_event_type": "lifecycle",
        "sub_type": "connect",
        "time": 1640000005,
        "self_id": 111111111
    }


@pytest.fixture
def sample_heartbeat_event_data() -> Dict[str, Any]:
    """示例心跳事件原始数据"""
    return {
        "post_type": "meta_event",
        "meta_event_type": "heartbeat",
        "status": {
            "online": True,
            "good": True
        },
        "interval": 5000,
        "time": 1640000006,
        "self_id": 111111111
    }


# ==================== NcatBotEvent Fixtures ====================

@pytest.fixture
def ncatbot_event():
    """创建一个简单的 NcatBotEvent 实例"""
    return NcatBotEvent("test.event", {"key": "value"})


@pytest.fixture
def ncatbot_message_event():
    """创建一个消息类型的 NcatBotEvent"""
    return NcatBotEvent("ncatbot.message", {
        "message_type": "group",
        "group_id": 123456789,
        "user_id": 987654321,
        "message": "Hello!"
    })


# ==================== Mock Event Objects ====================

@pytest.fixture
def mock_group_message_event():
    """Mock 的群消息事件对象"""
    event = MagicMock()
    event.message_type = "group"
    event.group_id = 123456789
    event.user_id = 987654321
    event.message = MagicMock()
    event.message.filter = MagicMock(return_value=[])
    return event


@pytest.fixture
def mock_private_message_event():
    """Mock 的私聊消息事件对象"""
    event = MagicMock()
    event.message_type = "private"
    event.user_id = 987654321
    event.message = MagicMock()
    event.message.filter = MagicMock(return_value=[])
    return event


@pytest.fixture
def mock_notice_event():
    """Mock 的通知事件对象"""
    event = MagicMock()
    event.notice_type = "group_increase"
    event.group_id = 123456789
    event.user_id = 222222222
    return event


@pytest.fixture
def mock_group_request_event():
    """Mock 的群请求事件对象"""
    event = MagicMock()
    event.request_type = "group"
    event.group_id = 123456789
    event.user_id = 333333333
    return event


@pytest.fixture
def mock_friend_request_event():
    """Mock 的好友请求事件对象"""
    event = MagicMock()
    event.request_type = "friend"
    event.user_id = 444444444
    return event


@pytest.fixture
def mock_startup_event():
    """Mock 的启动事件对象"""
    event = MagicMock()
    event.meta_event_type = "lifecycle"
    event.sub_type = "connect"
    event.self_id = 111111111
    return event


@pytest.fixture
def mock_heartbeat_event():
    """Mock 的心跳事件对象"""
    event = MagicMock()
    event.meta_event_type = "heartbeat"
    event.status = {"online": True, "good": True}
    return event


# ==================== Helper Functions ====================

def create_ncatbot_event(event_type: str, data: Any) -> NcatBotEvent:
    """辅助函数：创建 NcatBotEvent"""
    return NcatBotEvent(event_type, data)


def run_async(coro):
    """辅助函数：运行异步协程"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_handler(name: str = "mock_handler"):
    """创建带有 __name__ 属性的 Mock 处理器"""
    handler = MagicMock()
    handler.__name__ = name
    return handler


def create_async_mock_handler(name: str = "async_mock_handler"):
    """创建带有 __name__ 属性的异步 Mock 处理器"""
    handler = AsyncMock()
    handler.__name__ = name
    return handler
