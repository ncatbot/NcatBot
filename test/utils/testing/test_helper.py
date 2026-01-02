"""TestHelper 测试

测试 TestHelper 和 TestClient 的各种方法。
"""

import pytest
import sys
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite


# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGIN_DIR = FIXTURES_DIR / "hello_plugin"


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name for name in list(sys.modules.keys())
        if "ncatbot_plugin" in name or "hello_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


@pytest.fixture
def suite():
    """创建测试套件"""
    _cleanup_modules()
    
    s = E2ETestSuite()
    s.setup()
    s.index_plugin(str(PLUGIN_DIR))
    s.register_plugin_sync("hello_plugin")
    
    yield s
    
    s.teardown()
    _cleanup_modules()


class TestSendMessage:
    """消息发送测试"""

    def test_send_private_message(self, suite):
        """测试发送私聊消息"""
        suite.inject_private_message_sync("/hello")
        suite.assert_reply_sent("你好")

    def test_send_private_message_with_user_id(self, suite):
        """测试发送指定用户的私聊消息"""
        suite.clear_call_history()
        suite.inject_private_message_sync("/hello", user_id="123456")
        suite.assert_reply_sent("你好")

    def test_send_group_message(self, suite):
        """测试发送群聊消息"""
        suite.clear_call_history()
        suite.inject_group_message_sync("/hello", group_id="888888")
        suite.assert_reply_sent("你好")


class TestAssertions:
    """断言方法测试"""

    def test_assert_reply_sent(self, suite):
        """测试回复断言"""
        suite.inject_private_message_sync("/hello")
        suite.assert_reply_sent("你好")

    def test_assert_no_reply(self, suite):
        """测试无回复断言"""
        suite.clear_call_history()
        # 发送不是命令的消息
        suite.inject_private_message_sync("这不是命令")
        suite.assert_no_reply()

    def test_assert_api_called(self, suite):
        """测试 API 调用断言"""
        suite.inject_private_message_sync("/hello")
        suite.assert_api_called("send_private_msg")


class TestApiResponse:
    """API 响应设置测试"""

    def test_set_api_response(self, suite):
        """测试设置 API 响应"""
        suite.set_api_response(
            "get_user_info",
            {"retcode": 0, "data": {"user_id": "123456", "nickname": "测试用户"}},
        )
        # 响应设置不会抛出异常即为成功


class TestCallHistory:
    """调用历史测试"""

    def test_get_api_calls(self, suite):
        """测试获取 API 调用记录"""
        suite.inject_private_message_sync("/hello")
        
        calls = suite.get_api_calls("send_private_msg")
        assert len(calls) > 0

    def test_clear_call_history(self, suite):
        """测试清空调用历史"""
        suite.inject_private_message_sync("/hello")
        suite.clear_call_history()
        
        calls = suite.get_api_calls("send_private_msg")
        assert len(calls) == 0

