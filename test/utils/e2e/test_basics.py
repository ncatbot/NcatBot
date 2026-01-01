"""
E2E 测试套件基础功能测试

测试 E2ETestSuite、EventFactory、MockMessageRouter 的基本功能。
"""

import pytest
import asyncio

from ncatbot.utils.testing import E2ETestSuite, EventFactory, TestHelper
from ncatbot.utils import run_coroutine

from .test_plugins import LifecyclePlugin


class TestE2ETestSuiteBasics:
    """E2ETestSuite 基础功能测试"""
    
    def test_suite_setup_teardown(self):
        """测试 E2ETestSuite 的 setup 和 teardown"""
        suite = E2ETestSuite()
        client = suite.setup()
        
        assert client is not None
        assert client._mock_mode is True
        assert suite.mock_router is not None
        
        suite.teardown()
    
    def test_suite_sync_context_manager(self):
        """测试同步上下文管理器"""
        with E2ETestSuite() as suite:
            assert suite.client is not None
            assert suite.client._mock_mode is True
    
    @pytest.mark.asyncio
    async def test_suite_async_context_manager(self):
        """测试异步上下文管理器"""
        async with E2ETestSuite() as suite:
            assert suite.client is not None
            assert suite.client._mock_mode is True


class TestEventFactoryBasics:
    """EventFactory 基础功能测试"""
    
    def test_create_group_message(self):
        """测试创建群消息事件"""
        event = EventFactory.create_group_message(
            message="hello world",
            group_id="123456",
            user_id="654321",
        )
        
        assert str(event.group_id) == "123456"
        assert str(event.user_id) == "654321"
        assert event.raw_message == "hello world"
    
    def test_create_private_message(self):
        """测试创建私聊消息事件"""
        event = EventFactory.create_private_message(
            message="hello",
            user_id="654321",
        )
        
        assert str(event.user_id) == "654321"
        assert event.raw_message == "hello"
    
    def test_create_notice_event(self):
        """测试创建通知事件"""
        event = EventFactory.create_notice_event(
            notice_type="group_increase",
            user_id="654321",
            group_id="123456",
        )
        
        notice_type_str = str(event.notice_type)
        assert "group_increase" in notice_type_str or event.notice_type.value == "group_increase"
    
    def test_create_request_event(self):
        """测试创建请求事件"""
        event = EventFactory.create_friend_request_event(
            user_id="123456",
            comment="Please add me",
        )
        
        assert event is not None


class TestMockMessageRouterBasics:
    """MockMessageRouter 基础功能测试"""
    
    def test_api_call_recording(self):
        """测试 API 调用记录"""
        with E2ETestSuite() as suite:
            run_coroutine(
                suite.mock_router.send,
                "send_group_msg",
                {"group_id": "123", "message": "test"}
            )
            
            suite.assert_api_called("send_group_msg")
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) == 1
            assert calls[0]["group_id"] == "123"
    
    def test_api_response_mocking(self):
        """测试 API 响应模拟"""
        with E2ETestSuite() as suite:
            custom_response = {
                "retcode": 0,
                "data": {"nickname": "TestBot", "user_id": "12345"}
            }
            suite.set_api_response("get_login_info", custom_response)
            
            result = run_coroutine(
                suite.mock_router.send,
                "get_login_info",
                {}
            )
            
            assert result["data"]["nickname"] == "TestBot"
    
    def test_multiple_api_calls(self):
        """测试多次 API 调用"""
        with E2ETestSuite() as suite:
            run_coroutine(suite.mock_router.send, "send_group_msg", {"group_id": "1"})
            run_coroutine(suite.mock_router.send, "send_private_msg", {"user_id": "2"})
            run_coroutine(suite.mock_router.send, "send_group_msg", {"group_id": "3"})
            
            group_calls = suite.get_api_calls("send_group_msg")
            private_calls = suite.get_api_calls("send_private_msg")
            
            assert len(group_calls) == 2
            assert len(private_calls) == 1
    
    def test_clear_call_history(self):
        """测试清空调用历史"""
        with E2ETestSuite() as suite:
            run_coroutine(suite.mock_router.send, "test_action", {})
            assert len(suite.mock_router.get_call_history()) == 1
            
            suite.clear_call_history()
            assert len(suite.mock_router.get_call_history()) == 0


class TestPluginLifecycle:
    """插件生命周期测试"""
    
    def test_plugin_load_unload(self):
        """测试插件加载和卸载"""
        LifecyclePlugin.lifecycle_events = []
        
        with E2ETestSuite() as suite:
            plugin = suite.register_plugin_sync(LifecyclePlugin)
            
            assert "loaded" in LifecyclePlugin.lifecycle_events
            
            suite.unregister_plugin_sync("lifecycle_plugin")
            
            import time
            time.sleep(0.1)
            
            assert "closed" in LifecyclePlugin.lifecycle_events


class TestTestHelper:
    """TestHelper 基础功能测试"""
    
    def test_helper_initialization(self):
        """测试 TestHelper 初始化"""
        with E2ETestSuite() as suite:
            helper = TestHelper(suite.client)
            assert helper.client is suite.client
            assert helper.mock_router is suite.mock_router
