"""
集成测试共享 fixtures
"""

import asyncio
import pytest
from typing import Any, Callable, Dict, List, Optional, Awaitable
from pathlib import Path
import tempfile
import shutil

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.service import ServiceManager, BaseService


# =============================================================================
# Mock WebSocket
# =============================================================================


class MockWebSocket:
    """模拟 WebSocket 连接"""

    def __init__(self):
        self.connected = False
        self.sent_messages: List[dict] = []
        self.message_callback: Optional[Callable[[dict], Awaitable[None]]] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.connected = False

    async def send(self, data: dict) -> None:
        self.sent_messages.append(data)

    def set_message_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self.message_callback = callback

    async def simulate_receive(self, data: dict) -> None:
        """模拟接收消息"""
        if self.message_callback:
            await self.message_callback(data)

    async def listen(self) -> None:
        """模拟监听（立即返回，测试中手动触发消息）"""
        pass


class MockMessageRouter(BaseService):
    """模拟消息路由服务"""

    name = "message_router"
    description = "Mock message router for testing"

    def __init__(self, **config):
        super().__init__(**config)
        self.websocket = MockWebSocket()
        self._event_callback: Optional[Callable[[dict], Awaitable[None]]] = None
        self._responses: Dict[str, dict] = {}

    async def on_load(self) -> None:
        await self.websocket.connect()

    async def on_close(self) -> None:
        await self.websocket.disconnect()

    def set_event_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self._event_callback = callback
        self.websocket.set_message_callback(self._on_message)

    async def _on_message(self, data: dict) -> None:
        """处理收到的消息"""
        if "echo" in data:
            # API 响应
            pass
        elif self._event_callback:
            # 事件
            await self._event_callback(data)

    async def send(
        self, action: str, params: Optional[dict] = None, timeout: float = 30.0
    ) -> dict:
        """模拟发送 API 请求"""
        self.websocket.sent_messages.append({"action": action, "params": params})
        # 返回预设响应或默认成功
        return self._responses.get(action, {"status": "ok", "retcode": 0, "data": {}})

    def set_response(self, action: str, response: dict) -> None:
        """设置特定 action 的响应"""
        self._responses[action] = response

    async def simulate_event(self, event_data: dict) -> None:
        """模拟收到事件"""
        await self.websocket.simulate_receive(event_data)


# =============================================================================
# Mock API
# =============================================================================


class MockBotAPI:
    """模拟 BotAPI"""

    def __init__(self):
        self._calls: List[tuple] = []

    def get_calls(self) -> List[tuple]:
        return self._calls

    def get_last_call(self) -> Optional[tuple]:
        return self._calls[-1] if self._calls else None

    def clear_calls(self) -> None:
        self._calls.clear()

    async def post_group_msg(self, group_id, text, **kwargs):
        self._calls.append(("post_group_msg", group_id, text, kwargs))
        return {"message_id": "12345"}

    async def post_private_msg(self, user_id, text, **kwargs):
        self._calls.append(("post_private_msg", user_id, text, kwargs))
        return {"message_id": "12346"}

    async def set_group_kick(self, group_id, user_id, **kwargs):
        self._calls.append(("set_group_kick", group_id, user_id, kwargs))
        return {}

    async def set_group_ban(self, group_id, user_id, duration, **kwargs):
        self._calls.append(("set_group_ban", group_id, user_id, duration, kwargs))
        return {}

    def __getattr__(self, name):
        """处理其他 API 调用"""

        async def mock_method(*args, **kwargs):
            self._calls.append((name, args, kwargs))
            return {}

        return mock_method


# =============================================================================
# Test Plugin
# =============================================================================


class TestPlugin:
    """用于测试的简单插件"""

    name = "test_plugin"
    version = "1.0.0"
    author = "Test"
    description = "Test plugin"
    dependencies = {}

    def __init__(self):
        self.load_count = 0
        self.close_count = 0
        self.events_received: List[Any] = []
        self._handlers_id = set()

    def _init_(self):
        pass

    async def on_load(self):
        self.load_count += 1

    async def on_close(self):
        self.close_count += 1

    def handle_event(self, event):
        self.events_received.append(event)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def event_bus():
    """创建事件总线"""
    return EventBus(default_timeout=10.0)


@pytest.fixture
def mock_api():
    """创建 Mock API"""
    return MockBotAPI()


@pytest.fixture
def service_manager():
    """创建服务管理器"""
    return ServiceManager()


@pytest.fixture
def mock_router():
    """创建 Mock 消息路由"""
    return MockMessageRouter()


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def sample_message_event():
    """示例消息事件数据"""
    return {
        "time": 1767072511,
        "self_id": "1550507358",
        "post_type": "message",
        "message_type": "group",
        "sub_type": "normal",
        "message_id": "2009890763",
        "user_id": "3051561876",
        "group_id": "701784439",
        "message": [{"type": "text", "data": {"text": "Hello"}}],
        "raw_message": "Hello",
        "font": 14,
        "sender": {"user_id": "3051561876", "nickname": "测试用户", "role": "member"},
    }


@pytest.fixture
def sample_private_message_event():
    """示例私聊消息事件"""
    return {
        "time": 1767072441,
        "self_id": "1550507358",
        "post_type": "message",
        "message_type": "private",
        "sub_type": "friend",
        "message_id": "400060831",
        "user_id": "3051561876",
        "message": [{"type": "text", "data": {"text": "Hi"}}],
        "raw_message": "Hi",
        "font": 14,
        "sender": {"user_id": "3051561876", "nickname": "测试用户"},
    }


@pytest.fixture
def sample_notice_event():
    """示例通知事件数据"""
    return {
        "time": 1767072600,
        "self_id": "1550507358",
        "post_type": "notice",
        "notice_type": "group_increase",
        "sub_type": "approve",
        "group_id": "701784439",
        "operator_id": "123456",
        "user_id": "789012",
    }


@pytest.fixture
def sample_request_event():
    """示例请求事件数据"""
    return {
        "time": 1767072700,
        "self_id": "1550507358",
        "post_type": "request",
        "request_type": "friend",
        "user_id": "3051561876",
        "comment": "请加我好友",
        "flag": "request_flag_123",
    }


@pytest.fixture
def sample_meta_event():
    """示例元事件数据"""
    return {
        "time": 1767072800,
        "self_id": "1550507358",
        "post_type": "meta_event",
        "meta_event_type": "lifecycle",
        "sub_type": "connect",
    }
