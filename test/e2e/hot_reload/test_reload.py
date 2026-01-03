"""
插件重载测试

测试通过 plugin_loader 卸载后重新加载插件的完整流程。
"""

import pytest
import asyncio

from ncatbot.core import NcatBotEvent
from ncatbot.utils.testing import E2ETestSuite
from .conftest import (
    check_command_registered,
    check_alias_registered,
    check_handler_registered,
)


PLUGIN_NAME = "reload_test_plugin"


class TestReload:
    """插件重载测试"""

    @pytest.mark.asyncio
    async def test_reload_restores_commands(self, test_suite: E2ETestSuite):
        """测试重载后命令正确恢复"""
        loader = test_suite.client.plugin_loader

        # 加载插件
        await loader.load_plugin(PLUGIN_NAME)
        assert check_command_registered("reload_test_cmd")

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)
        assert not check_command_registered("reload_test_cmd")

        # 重新加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 验证命令已恢复
        assert check_command_registered("reload_test_cmd"), \
            "命令 'reload_test_cmd' 应该已恢复"
        assert check_alias_registered("hrt"), \
            "别名 'hrt' 应该已恢复"

    @pytest.mark.asyncio
    async def test_reload_restores_handlers(self, test_suite: E2ETestSuite):
        """测试重载后事件处理器正确恢复"""
        loader = test_suite.client.plugin_loader

        # 加载插件
        await loader.load_plugin(PLUGIN_NAME)
        assert check_handler_registered(test_suite, PLUGIN_NAME) > 0

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)

        # 重新加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 验证处理器已恢复
        assert check_handler_registered(test_suite, PLUGIN_NAME) > 0, \
            "事件处理器应该已恢复"

    @pytest.mark.asyncio
    async def test_reload_preserves_config_values(self, test_suite: E2ETestSuite):
        """测试重载后配置值被保留"""
        loader = test_suite.client.plugin_loader
        config_service = test_suite.services.plugin_config

        # 加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 设置配置值（使用异步版本确保串行保存）
        await config_service.set_atomic_async(PLUGIN_NAME, "test_string", "modified_value")
        await config_service.set_atomic_async(PLUGIN_NAME, "reload_count", 10)

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)

        # 重新加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 验证插件可以访问保留的配置
        plugin = loader.get_plugin(PLUGIN_NAME)
        assert plugin is not None
        assert plugin.config.get("reload_count") == 10

    @pytest.mark.asyncio
    async def test_reload_allows_config_re_registration(self, test_suite: E2ETestSuite):
        """测试重载后可以重新注册配置项"""
        loader = test_suite.client.plugin_loader
        config_service = test_suite.services.plugin_config

        # 第一次加载
        await loader.load_plugin(PLUGIN_NAME)
        registered = config_service.get_registered_configs(PLUGIN_NAME)
        assert "reload_count" in registered

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)

        # 验证配置项注册已清理
        registered = config_service.get_registered_configs(PLUGIN_NAME)
        assert len(registered) == 0

        # 第二次加载（应该可以重新注册配置项）
        await loader.load_plugin(PLUGIN_NAME)

        # 验证配置项重新注册成功
        registered = config_service.get_registered_configs(PLUGIN_NAME)
        assert "reload_count" in registered, "配置项应该可以重新注册"

    @pytest.mark.asyncio
    async def test_command_works_after_reload(self, test_suite: E2ETestSuite):
        """测试重载后命令正常工作"""
        loader = test_suite.client.plugin_loader

        # 加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)

        # 重新加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 验证命令工作
        await test_suite.inject_group_message("/reload_test_cmd")
        test_suite.assert_reply_sent()
        calls = test_suite.get_api_calls("send_group_msg")
        assert "original_response" in str(calls[-1].get("message", ""))

    @pytest.mark.asyncio
    async def test_event_handler_works_after_reload(self, test_suite: E2ETestSuite):
        """测试重载后事件处理器正常工作"""
        loader = test_suite.client.plugin_loader

        # 加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 获取插件类
        plugin = loader.get_plugin(PLUGIN_NAME)
        plugin_class = type(plugin)

        # 发布测试事件
        test_event = NcatBotEvent(
            "ncatbot.hot_reload_test_event",
            data={"test": "value1"}
        )
        await test_suite.event_bus.publish(test_event)
        assert plugin_class.HANDLER_CALL_COUNT > 0

        # 重置计数器
        plugin_class.reset_counters()

        # 卸载插件
        await loader.unload_plugin(PLUGIN_NAME)

        # 重新加载插件
        await loader.load_plugin(PLUGIN_NAME)

        # 获取新的插件类
        plugin = loader.get_plugin(PLUGIN_NAME)
        plugin_class = type(plugin)

        # 再次发布测试事件
        test_event = NcatBotEvent(
            "ncatbot.hot_reload_test_event",
            data={"test": "value2"}
        )
        await test_suite.event_bus.publish(test_event)

        # 验证处理器被调用
        assert plugin_class.HANDLER_CALL_COUNT > 0, \
            "重载后事件处理器应该工作"

    @pytest.mark.asyncio
    async def test_full_hot_reload_cycle(self, test_suite: E2ETestSuite):
        """测试完整的热重载周期"""
        loader = test_suite.client.plugin_loader

        # 加载
        await loader.load_plugin(PLUGIN_NAME)
        assert check_command_registered("reload_test_cmd")

        # 使用命令
        await test_suite.inject_group_message("/reload_test_cmd")
        test_suite.assert_reply_sent()
        test_suite.clear_call_history()

        # 卸载
        await loader.unload_plugin(PLUGIN_NAME)
        assert not check_command_registered("reload_test_cmd")

        # 重新加载
        await loader.load_plugin(PLUGIN_NAME)
        assert check_command_registered("reload_test_cmd")

        # 再次使用命令
        await test_suite.inject_group_message("/reload_test_cmd")
        test_suite.assert_reply_sent()
