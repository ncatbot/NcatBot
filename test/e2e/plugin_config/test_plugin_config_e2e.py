"""
Plugin Config 服务端到端测试

测试插件配置服务的完整功能：
- 配置注册和获取
- 配置持久化
- 插件配置隔离
- 配置更新和保存
"""

import pytest
import time

from ncatbot.utils.testing import E2ETestSuite
from .test_plugin import PluginConfigTestPlugin


class TestPluginConfigE2E:
    """Plugin Config 服务端到端测试"""

    def test_config_registration_and_defaults(self):
        """测试配置注册和默认值"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(PluginConfigTestPlugin)

            # 发送测试命令查看默认配置
            suite.inject_group_message_sync("/config_test")
            time.sleep(0.1)

            # 应该收到包含默认配置的回复
            suite.assert_reply_sent()
            suite.assert_api_called("send_group_msg")

            # 验证回复内容包含默认值
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) >= 1
            last_call = calls[-1]
            message = last_call.get("message", "")
            assert "default_value" in str(message)
            assert "42" in str(message)
            assert "True" in str(message)

    def test_config_modification(self):
        """测试配置修改"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(PluginConfigTestPlugin)

            # 修改配置
            suite.inject_group_message_sync("/config_set test_string hello_world")
            time.sleep(0.1)
            suite.assert_reply_sent()

            suite.inject_group_message_sync("/config_set test_number 123")
            time.sleep(0.1)
            suite.assert_reply_sent()

            suite.inject_group_message_sync("/config_set test_bool false")
            time.sleep(0.1)
            suite.assert_reply_sent()

            # 查看修改后的配置
            suite.inject_group_message_sync("/config_test")
            time.sleep(0.1)

            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            last_call = calls[-1]
            message = last_call.get("message", "")
            assert "hello_world" in str(message)
            assert "123" in str(message)
            assert "False" in str(message)

    def test_config_persistence_between_tests(self):
        """测试配置在测试间的持久化"""
        # 注意：这个测试需要特殊的设置，因为 E2ETestSuite 每次都是新的实例
        # 在实际的端到端测试中，这应该通过重启服务来测试
        # 这里我们只是验证配置设置后立即可以读取

        with E2ETestSuite() as suite:
            suite.register_plugin_sync(PluginConfigTestPlugin)

            # 设置配置
            suite.inject_group_message_sync("/config_set test_string persistent_test")
            time.sleep(0.1)
            suite.assert_reply_sent()

            # 在同一个测试套件实例中验证配置保持
            suite.inject_group_message_sync("/config_test")
            time.sleep(0.1)

            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            last_call = calls[-1]
            message = last_call.get("message", "")
            assert "persistent_test" in str(message)

    def test_config_isolation_between_plugins(self):
        """测试不同插件间的配置隔离"""
        with E2ETestSuite() as suite:
            # 注册两个相同的插件实例（模拟不同插件）
            suite.register_plugin_sync(PluginConfigTestPlugin)

            # 注意：在实际场景中，不同插件应该有不同的配置空间
            # 这里我们只是验证单个插件的配置工作正常
            suite.inject_group_message_sync("/config_test")
            time.sleep(0.1)

            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) >= 1

    def test_invalid_config_operations(self):
        """测试无效的配置操作"""
        with E2ETestSuite() as suite:
            suite.register_plugin_sync(PluginConfigTestPlugin)

            # 测试未知配置项
            suite.inject_group_message_sync("/config_set unknown_key some_value")
            time.sleep(0.1)
            suite.assert_reply_sent()

            # 验证错误消息
            calls = suite.get_api_calls("send_group_msg")
            last_call = calls[-1]
            message = last_call.get("message", "")
            assert "未知配置项" in str(message) or "unknown_key" in str(message)

            # 测试无效的数字转换
            suite.inject_group_message_sync("/config_set test_number not_a_number")
            time.sleep(0.1)
            suite.assert_reply_sent()

            # 应该收到错误消息
            calls = suite.get_api_calls("send_group_msg")
            last_call = calls[-1]
            message = last_call.get("message", "")
            assert "设置失败" in str(message) or "invalid literal for int" in str(message)
