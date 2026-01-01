"""
测试套件集成测试

验证 TestSuite 和相关测试工具是否正常工作。
"""

import pytest
import asyncio
from ncatbot.utils.testing import TestSuite, EventFactory, TestHelper
from ncatbot.utils import run_coroutine


class TestTestSuite:
    """TestSuite 测试"""
    
    def test_suite_setup_teardown(self):
        """测试 TestSuite 的 setup 和 teardown"""
        suite = TestSuite()
        client = suite.setup()
        
        assert client is not None
        assert client._mock_mode is True
        assert suite.mock_router is not None
        
        suite.teardown()
    
    def test_suite_context_manager(self):
        """测试 TestSuite 作为上下文管理器"""
        with TestSuite() as suite:
            assert suite.client is not None
            assert suite.client._mock_mode is True
    
    def test_api_call_recording(self):
        """测试 API 调用记录"""
        with TestSuite() as suite:
            # 直接调用 MockMessageRouter 的 send 方法
            run_coroutine(
                suite.mock_router.send, "send_group_msg", {"group_id": "123", "message": "test"}
            )
            
            # 验证调用被记录
            suite.assert_api_called("send_group_msg")
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) == 1
            assert calls[0]["group_id"] == "123"
    
    def test_api_response_setting(self):
        """测试设置 API 响应"""
        with TestSuite() as suite:
            custom_response = {"retcode": 0, "data": {"message_id": "custom_id"}}
            suite.set_api_response("send_group_msg", custom_response)
            
            result = run_coroutine(
                suite.mock_router.send, "send_group_msg", {"group_id": "123", "message": "test"}
            )
            
            assert result["data"]["message_id"] == "custom_id"


class TestEventFactory:
    """EventFactory 测试"""
    
    def test_create_group_message(self):
        """测试创建群消息事件"""
        event = EventFactory.create_group_message(
            message="hello world",
            group_id="123456",
            user_id="654321",
        )
        
        # GroupMessageEvent 使用 pydantic 模型
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
        
        # NoticeEvent 的 notice_type 可能是枚举或字符串
        assert str(event.notice_type) == "group_increase" or event.notice_type.value == "group_increase"


class TestTestHelper:
    """TestHelper 测试"""
    
    def test_helper_initialization(self):
        """测试 TestHelper 初始化"""
        with TestSuite() as suite:
            helper = TestHelper(suite.client)
            assert helper.client is suite.client
            assert helper.mock_router is suite.mock_router
    
    def test_helper_send_group_message(self):
        """测试 TestHelper 发送群消息"""
        with TestSuite() as suite:
            helper = TestHelper(suite.client)
            # 使用同步版本
            helper.send_group_message_sync("/test command")
            # 事件应该被处理（虽然没有插件处理，但不应该报错）
    
    def test_helper_assert_no_reply(self):
        """测试 TestHelper 断言无回复"""
        with TestSuite() as suite:
            helper = TestHelper(suite.client)
            helper.assert_no_reply()  # 没有回复，不应该报错


class TestMockMessageRouter:
    """MockMessageRouter 测试"""
    
    def test_call_history(self):
        """测试调用历史记录"""
        with TestSuite() as suite:
            router = suite.mock_router
            
            run_coroutine(
                router.send, "send_group_msg", {"group_id": "123", "message": "test"}
            )
            
            history = router.get_call_history()
            assert len(history) == 1
            assert history[0][0] == "send_group_msg"
    
    def test_assert_called(self):
        """测试断言方法"""
        with TestSuite() as suite:
            router = suite.mock_router
            
            run_coroutine(router.send, "get_login_info", {})
            
            router.assert_called("get_login_info")
            router.assert_not_called("send_group_msg")
    
    def test_clear_history(self):
        """测试清空历史"""
        with TestSuite() as suite:
            router = suite.mock_router
            
            run_coroutine(router.send, "test_action", {})
            
            assert len(router.get_call_history()) == 1
            router.clear_call_history()
            assert len(router.get_call_history()) == 0
