"""
E2E 测试套件基础功能测试

测试 E2ETestSuite、EventFactory、MockMessageRouter 的基本功能。
"""

import os
import pytest
import asyncio

from ncatbot.utils.testing import E2ETestSuite, EventFactory


# 测试插件目录的路径
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class TestE2ETestSuiteBasics:
    """E2ETestSuite 基础功能测试"""

    @pytest.mark.asyncio
    async def test_suite_setup_teardown(self):
        """测试 E2ETestSuite 的 setup 和 teardown"""
        suite = E2ETestSuite()
        client = await suite.setup()

        assert client is not None
        assert suite.mock_server is not None

        await suite.teardown()

    @pytest.mark.asyncio
    async def test_suite_async_context_manager(self):
        """测试异步上下文管理器"""
        async with E2ETestSuite() as suite:
            assert suite.client is not None


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
        assert (
            "group_increase" in notice_type_str
            or event.notice_type.value == "group_increase"
        )

    def test_create_request_event(self):
        """测试创建请求事件"""
        event = EventFactory.create_friend_request_event(
            user_id="123456",
            comment="Please add me",
        )

        assert event is not None


class TestMockServerBasics:
    """MockServer 基础功能测试"""

    @pytest.mark.asyncio
    async def test_multiple_api_calls(self):
        """测试多次 API 调用"""
        async with E2ETestSuite() as suite:
            await suite.api.send_group_text(group_id="1", text="test1")
            await suite.api.send_private_text(user_id="2", text="test2")
            await suite.api.send_group_text(group_id="3", text="test3")

            group_calls = suite.get_api_calls("send_group_msg")
            private_calls = suite.get_api_calls("send_private_msg")

            assert group_calls[0]["group_id"] == "1"
            assert len(group_calls) == 2
            assert len(private_calls) == 1

            suite.clear_call_history()
            assert len(suite.get_api_calls("send_group_msg")) == 0


class TestPluginLifecycle:
    """插件生命周期测试"""

    @pytest.mark.asyncio
    async def test_plugin_load_unload(self):
        """测试插件加载和卸载"""
        async with E2ETestSuite() as suite:
            plugin_dir = os.path.join(PLUGINS_DIR, "lifecycle_plugin")
            suite.index_plugin(plugin_dir)
            plugin = await suite.register_plugin("lifecycle_plugin")

            # 获取加载后的插件实例的类
            PluginClass = type(plugin)

            # 验证 on_load 被调用
            assert "loaded" in PluginClass.lifecycle_events

            await suite.unregister_plugin("lifecycle_plugin")

            await asyncio.sleep(0.01)

            # 验证 on_close 被调用
            assert "closed" in PluginClass.lifecycle_events
