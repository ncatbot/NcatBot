"""
E2ETestSuite 断言有效性测试

测试 E2ETestSuite 的断言方法是否能正确检测回复。
使用 clear_call_history() 在测试之间清理，减少 setup/teardown 开销。
"""

import os
import pytest

from ncatbot.utils.testing import E2ETestSuite


# 测试插件目录的路径
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class TestSimpleReplyPlugin:
    """使用 simple_reply_plugin 的断言测试（合并到单个 suite）"""

    @pytest.mark.asyncio
    async def test_assertions_with_simple_reply_plugin(self):
        """测试所有使用 simple_reply_plugin 的断言场景"""
        async with E2ETestSuite() as suite:
            plugin_dir = os.path.join(PLUGINS_DIR, "simple_reply_plugin")
            suite.index_plugin(plugin_dir)
            await suite.register_plugin("simple_reply_plugin")

            # 场景1: assert_reply_sent 能检测到回复
            await suite.inject_group_message("/ping")
            suite.assert_reply_sent()
            suite.assert_api_called("send_group_msg")
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) >= 1, f"Expected at least 1 call, got {len(calls)}"
            suite.clear_call_history()

            # 场景2: assert_reply_sent 能检测回复内容
            await suite.inject_group_message("/ping")
            suite.assert_reply_sent(contains="pong")
            suite.clear_call_history()

            # 场景3: assert_no_reply 在有回复时应该失败
            await suite.inject_group_message("/ping")
            with pytest.raises(AssertionError):
                suite.assert_no_reply()
            suite.clear_call_history()

            # 场景4: get_latest_reply 获取最后一条回复
            await suite.inject_group_message("/ping")
            last_reply = suite.get_latest_reply()
            assert last_reply is not None
            suite.clear_call_history()

            # 场景5: echo 命令带参数
            await suite.inject_group_message("/echo hello world")
            suite.assert_reply_sent(contains="Echo:")
            suite.clear_call_history()

            # 场景6: greet 命令带名字参数
            await suite.inject_group_message("/greet Alice")
            suite.assert_reply_sent(contains="Hello")


class TestNoReplyPlugin:
    """使用 no_reply_plugin 的断言测试（合并到单个 suite）"""

    @pytest.mark.asyncio
    async def test_assertions_with_no_reply_plugin(self):
        """测试所有使用 no_reply_plugin 的断言场景"""
        async with E2ETestSuite() as suite:
            plugin_dir = os.path.join(PLUGINS_DIR, "no_reply_plugin")
            suite.index_plugin(plugin_dir)
            await suite.register_plugin("no_reply_plugin")

            # 场景1: assert_no_reply 在无回复时通过
            await suite.inject_group_message("/silent")
            suite.assert_no_reply()
            suite.clear_call_history()

            # 场景2: assert_reply_sent 在无回复时应该失败
            await suite.inject_group_message("/silent")
            with pytest.raises(AssertionError):
                suite.assert_reply_sent()


class TestFilteredReplyPlugin:
    """使用 filtered_reply_plugin 的过滤器测试（合并到单个 suite）"""

    @pytest.mark.asyncio
    async def test_filter_behaviors(self):
        """测试过滤器命令的回复检测"""
        async with E2ETestSuite() as suite:
            plugin_dir = os.path.join(PLUGINS_DIR, "filtered_reply_plugin")
            suite.index_plugin(plugin_dir)
            await suite.register_plugin("filtered_reply_plugin")

            # 场景1: 群聊过滤器允许群消息
            await suite.inject_group_message("/group_ping")
            suite.assert_api_called("send_group_msg")
            suite.clear_call_history()

            # 场景2: 群聊过滤器阻止私聊消息
            await suite.inject_private_message("/group_ping")
            suite.assert_api_not_called("send_group_msg")
            suite.clear_call_history()

            # 场景3: 私聊过滤器允许私聊消息
            await suite.inject_private_message("/private_ping")
            suite.assert_api_called("send_private_msg")


class TestSuiteIsolation:
    """测试 suite 实例之间的隔离"""

    @pytest.mark.asyncio
    async def test_new_suite_has_clean_history(self):
        """验证新 suite 实例没有历史记录"""
        # 第一个 suite 发送回复
        async with E2ETestSuite() as suite:
            plugin_dir = os.path.join(PLUGINS_DIR, "simple_reply_plugin")
            suite.index_plugin(plugin_dir)
            await suite.register_plugin("simple_reply_plugin")
            await suite.inject_group_message("/ping")
            suite.assert_reply_sent()

        # 第二个 suite 应该是干净的
        async with E2ETestSuite() as suite:
            assert len(suite.get_api_calls()) == 0
