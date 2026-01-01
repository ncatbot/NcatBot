"""
TestHelper 断言有效性测试

测试 TestHelper 和 E2ETestSuite 的断言方法是否能正确检测回复。
"""

import pytest
import time

from ncatbot.utils.testing import E2ETestSuite, TestHelper, EventFactory
from ncatbot.utils import run_coroutine

from .test_plugins import (
    SimpleReplyPlugin,
    FilteredReplyPlugin,
    NoReplyPlugin,
)


class TestAssertReplyValidity:
    """测试 assert_reply_sent 断言的有效性"""
    
    def test_assert_reply_sent_detects_reply(self):
        """验证 assert_reply_sent 能检测到回复"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            # 发送命令
            suite.inject_group_message_sync("/ping")
            time.sleep(0.1)  # 等待异步处理
            
            # 断言应该能检测到回复
            suite.assert_reply_sent()
            
            # 验证具体调用了 send_group_msg
            suite.assert_api_called("send_group_msg")
            
            # 验证调用参数
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) >= 1, f"Expected at least 1 call, got {len(calls)}"
    
    def test_assert_reply_sent_with_content(self):
        """验证 assert_reply_sent 能检测回复内容"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            suite.inject_group_message_sync("/ping")
            time.sleep(0.1)
            
            # 断言包含特定内容
            suite.assert_reply_sent(contains="pong")
    
    def test_assert_no_reply_when_no_response(self):
        """验证 assert_no_reply 在无回复时通过"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(NoReplyPlugin)
            
            suite.inject_group_message_sync("/silent")
            time.sleep(0.1)
            
            # 应该没有回复
            suite.assert_no_reply()
    
    def test_assert_no_reply_fails_when_reply_exists(self):
        """验证 assert_no_reply 在有回复时失败"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            suite.inject_group_message_sync("/ping")
            time.sleep(0.1)
            
            # 有回复时应该失败
            with pytest.raises(AssertionError):
                suite.assert_no_reply()
    
    def test_assert_reply_sent_fails_when_no_reply(self):
        """验证 assert_reply_sent 在无回复时失败"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(NoReplyPlugin)
            
            suite.inject_group_message_sync("/silent")
            time.sleep(0.1)
            
            # 无回复时应该失败
            with pytest.raises(AssertionError):
                suite.assert_reply_sent()


class TestTestHelperAssertions:
    """测试 TestHelper 的断言方法"""
    
    def test_helper_assert_reply_sent(self):
        """测试 TestHelper.assert_reply_sent"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            helper = TestHelper(suite.client)
            
            helper.send_group_message_sync("/ping")
            time.sleep(0.1)
            
            # 使用 helper 的断言方法
            helper.assert_reply_sent()
    
    def test_helper_assert_no_reply(self):
        """测试 TestHelper.assert_no_reply"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(NoReplyPlugin)
            helper = TestHelper(suite.client)
            
            helper.send_group_message_sync("/silent")
            time.sleep(0.1)
            
            helper.assert_no_reply()
    
    def test_helper_get_last_reply(self):
        """测试 TestHelper.get_last_reply"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            helper = TestHelper(suite.client)
            
            helper.send_group_message_sync("/ping")
            time.sleep(0.1)
            
            # 获取最后一条回复
            last_reply = helper.get_last_reply()
            assert last_reply is not None


class TestFilteredCommandReply:
    """测试过滤器命令的回复检测"""
    
    def test_group_filter_allows_group_message(self):
        """测试群聊过滤器允许群消息"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(FilteredReplyPlugin)
            
            suite.inject_group_message_sync("/group_ping")
            time.sleep(0.1)
            
            # 群消息应该有回复
            suite.assert_api_called("send_group_msg")
    
    def test_group_filter_blocks_private_message(self):
        """测试群聊过滤器阻止私聊消息"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(FilteredReplyPlugin)
            
            suite.inject_private_message_sync("/group_ping")
            time.sleep(0.1)
            
            # 私聊消息不应该触发群聊命令的回复
            suite.assert_api_not_called("send_group_msg")
    
    def test_private_filter_allows_private_message(self):
        """测试私聊过滤器允许私聊消息"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(FilteredReplyPlugin)
            
            suite.inject_private_message_sync("/private_ping")
            time.sleep(0.1)
            
            # 私聊消息应该有回复
            suite.assert_api_called("send_private_msg")


class TestCommandWithArgs:
    """测试带参数命令的回复"""
    
    def test_echo_command_with_args(self):
        """测试 echo 命令带参数"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            suite.inject_group_message_sync("/echo hello world")
            time.sleep(0.1)
            
            # 应该有回复
            suite.assert_reply_sent(contains="Echo:")
    
    def test_greet_command_with_name(self):
        """测试 greet 命令带名字参数"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            suite.inject_group_message_sync("/greet Alice")
            time.sleep(0.1)
            
            # 应该有回复包含名字
            suite.assert_reply_sent(contains="Hello")


class TestClearHistoryBetweenTests:
    """测试测试之间的隔离"""
    
    def test_first_test_sends_reply(self):
        """第一个测试发送回复"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(SimpleReplyPlugin)
            
            suite.inject_group_message_sync("/ping")
            time.sleep(0.1)
            
            suite.assert_reply_sent()
    
    def test_second_test_has_clean_history(self):
        """第二个测试有干净的历史"""
        with E2ETestSuite() as suite:
            # 新的 suite 应该没有历史记录
            assert len(suite.mock_router.get_call_history()) == 0
