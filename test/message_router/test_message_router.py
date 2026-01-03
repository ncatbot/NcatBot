"""
MessageRouter 单元测试

测试消息路由服务的核心功能：
- 初始化和状态管理
- 发送消息和等待响应
- 消息回调处理
- 资源清理
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.core.service.builtin.message_router import MessageRouter


class TestMessageRouterInit:
    """初始化测试"""

    def test_init_with_defaults(self):
        """测试默认初始化"""
        router = MessageRouter()

        assert router._uri is None
        assert router._event_callback is None
        assert router._ws is None
        assert router._pending_futures == {}

    def test_init_with_uri(self):
        """测试带 URI 初始化"""
        uri = "ws://localhost:8080"
        router = MessageRouter(uri=uri)

        assert router._uri == uri

    def test_init_with_callback(self):
        """测试带回调初始化"""

        async def callback(data):
            pass

        router = MessageRouter(event_callback=callback)

        assert router._event_callback is callback

    def test_service_name_and_description(self):
        """测试服务名称和描述"""
        router = MessageRouter()

        assert router.name == "message_router"
        assert router.description == "消息路由服务"


class TestMessageRouterProperties:
    """属性测试"""

    def test_connected_when_no_ws(self):
        """测试无 WebSocket 时 connected 为 False"""
        router = MessageRouter()

        assert router.connected is False

    def test_connected_when_ws_not_connected(self):
        """测试 WebSocket 未连接时 connected 为 False"""
        router = MessageRouter()
        router._ws = MagicMock()
        router._ws.connected = False

        assert router.connected is False

    def test_connected_when_ws_connected(self):
        """测试 WebSocket 已连接时 connected 为 True"""
        router = MessageRouter()
        router._ws = MagicMock()
        router._ws.connected = True

        assert router.connected is True

    def test_websocket_property(self):
        """测试 websocket 属性"""
        router = MessageRouter()
        mock_ws = MagicMock()
        router._ws = mock_ws

        assert router.websocket is mock_ws


class TestSetEventCallback:
    """set_event_callback 方法测试"""

    def test_set_event_callback(self):
        """测试设置事件回调"""
        router = MessageRouter()

        async def new_callback(data):
            pass

        router.set_event_callback(new_callback)

        assert router._event_callback is new_callback


class TestMessageRouterSend:
    """send 方法测试"""

    @pytest.fixture
    def router_with_mock_ws(self):
        """创建带 Mock WebSocket 的路由器"""
        router = MessageRouter()
        router._ws = MagicMock()
        router._ws.send = AsyncMock()
        return router

    @pytest.mark.asyncio
    async def test_send_without_ws_raises_error(self):
        """测试无 WebSocket 时发送会抛出错误"""
        router = MessageRouter()

        with pytest.raises(ConnectionError, match="服务未连接"):
            await router.send("get_login_info")

    @pytest.mark.asyncio
    async def test_send_creates_pending_future(self, router_with_mock_ws):
        """测试发送时会创建等待中的 Future"""
        router = router_with_mock_ws

        # 创建一个任务但不等待它完成
        task = asyncio.create_task(router.send("get_login_info", timeout=0.1))
        await asyncio.sleep(0.01)  # 让任务启动

        # 应该有一个挂起的 Future
        assert len(router._pending_futures) == 1

        # 取消任务以清理
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, TimeoutError):
            pass

    @pytest.mark.asyncio
    async def test_send_timeout(self, router_with_mock_ws):
        """测试发送超时"""
        router = router_with_mock_ws

        with pytest.raises(TimeoutError, match="API请求超时"):
            await router.send("slow_action", timeout=0.05)

    @pytest.mark.asyncio
    async def test_send_cleans_up_future_on_timeout(self, router_with_mock_ws):
        """测试超时后清理 Future"""
        router = router_with_mock_ws

        try:
            await router.send("slow_action", timeout=0.05)
        except TimeoutError:
            pass

        # Future 应该被清理
        assert len(router._pending_futures) == 0


class TestOnMessage:
    """_on_message 方法测试"""

    @pytest.mark.asyncio
    async def test_on_message_resolves_pending_future(self):
        """测试收到响应时解析等待中的 Future"""
        router = MessageRouter()
        router._ws = MagicMock()
        router._ws.send = AsyncMock()

        # 模拟发送请求
        send_task = asyncio.create_task(router.send("test_action", timeout=1.0))
        await asyncio.sleep(0.01)

        # 获取 echo 值
        assert len(router._pending_futures) == 1
        echo = list(router._pending_futures.keys())[0]

        # 模拟收到响应
        response = {"echo": echo, "status": "ok", "data": {"result": "success"}}
        await router._on_message(response)

        # 等待发送任务完成
        result = await send_task

        assert result == response

    @pytest.mark.asyncio
    async def test_on_message_calls_event_callback_for_events(self):
        """测试收到事件时调用回调"""
        callback = AsyncMock()
        router = MessageRouter(event_callback=callback)

        event_data = {
            "post_type": "message",
            "message_type": "group",
            "message": "Hello",
        }

        await router._on_message(event_data)
        await asyncio.sleep(0.01)  # 等待 create_task 执行

        callback.assert_awaited_once_with(event_data)

    @pytest.mark.asyncio
    async def test_on_message_ignores_unknown_echo(self):
        """测试忽略未知 echo 的响应"""
        callback = AsyncMock()
        router = MessageRouter(event_callback=callback)

        # 发送带未知 echo 的消息
        unknown_response = {"echo": "unknown-echo-id", "status": "ok"}
        await router._on_message(unknown_response)
        await asyncio.sleep(0.01)

        # 由于有 echo 但找不到 Future，会作为事件处理
        callback.assert_awaited_once_with(unknown_response)


class TestOnLoad:
    """on_load 方法测试"""

    @pytest.mark.asyncio
    @patch("ncatbot.core.service.builtin.message_router.NapCatWebSocket")
    async def test_on_load_creates_websocket(self, mock_ws_class):
        """测试加载时创建 WebSocket"""
        mock_ws = MagicMock()
        mock_ws.connect = AsyncMock()
        mock_ws_class.return_value = mock_ws

        router = MessageRouter(uri="ws://localhost:8080")
        await router.on_load()

        mock_ws_class.assert_called_once()
        mock_ws.connect.assert_awaited_once()
        assert router._ws is mock_ws


class TestOnClose:
    """on_close 方法测试"""

    @pytest.mark.asyncio
    async def test_on_close_cancels_pending_futures(self):
        """测试关闭时取消等待中的 Future"""
        router = MessageRouter()

        # 创建一些挂起的 Future
        loop = asyncio.get_running_loop()
        future1 = loop.create_future()
        future2 = loop.create_future()
        router._pending_futures = {"echo1": future1, "echo2": future2}

        await router.on_close()

        assert future1.cancelled()
        assert future2.cancelled()
        assert len(router._pending_futures) == 0

    @pytest.mark.asyncio
    async def test_on_close_disconnects_websocket(self):
        """测试关闭时断开 WebSocket"""
        router = MessageRouter()
        mock_ws = MagicMock()
        mock_ws.disconnect = AsyncMock()
        router._ws = mock_ws

        await router.on_close()

        mock_ws.disconnect.assert_awaited_once()
        assert router._ws is None

    @pytest.mark.asyncio
    async def test_on_close_safe_without_ws(self):
        """测试无 WebSocket 时关闭安全"""
        router = MessageRouter()
        router._ws = None

        await router.on_close()  # 不应抛出异常


class TestStartListening:
    """start_listening 方法测试"""

    def test_start_listening_delegates_to_ws(self):
        """测试 start_listening 委托给 WebSocket"""
        router = MessageRouter()
        mock_ws = MagicMock()
        mock_ws.start_listening = MagicMock(return_value="listening_task")
        router._ws = mock_ws

        result = router.start_listening()

        mock_ws.start_listening.assert_called_once()
        assert result == "listening_task"

    def test_start_listening_without_ws(self):
        """测试无 WebSocket 时返回 None"""
        router = MessageRouter()
        router._ws = None

        result = router.start_listening()

        assert result is None
