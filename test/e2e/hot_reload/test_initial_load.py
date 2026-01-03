"""
插件初始加载测试

测试插件加载时所有组件的正确注册。
"""

import pytest
import asyncio
from pathlib import Path
from ncatbot.utils.testing import E2ETestSuite
from .conftest import (
    check_command_registered,
    check_alias_registered,
    check_config_registered,
    check_handler_registered,
    RELOAD_PLUGIN_DIR,
)


PLUGIN_NAME = "reload_test_plugin"
PLUGIN_ROOT = Path(__file__).parent / "fixtures" / "plugins"

class TestInitialLoad:
    """插件初始加载测试"""

    @pytest.mark.asyncio
    async def test_plugin_loads_successfully(self, test_suite: E2ETestSuite):
        """测试插件能成功加载"""
        loader = test_suite.client.plugin_loader
        assert loader is not None

        # 通过正常流程加载插件
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        plugin = loader.get_plugin(PLUGIN_NAME)
        assert plugin is not None, f"插件 {PLUGIN_NAME} 应该已加载"
        assert plugin.name == PLUGIN_NAME

    @pytest.mark.asyncio
    async def test_commands_registered_on_load(self, test_suite: E2ETestSuite):
        """测试加载时命令正确注册"""
        loader = test_suite.client.plugin_loader
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        assert check_command_registered("reload_test_cmd"), \
            "命令 'reload_test_cmd' 应该已注册"
        assert check_command_registered("hot_reload_config"), \
            "命令 'hot_reload_config' 应该已注册"

    @pytest.mark.asyncio
    async def test_aliases_registered_on_load(self, test_suite: E2ETestSuite):
        """测试加载时别名正确注册"""
        loader = test_suite.client.plugin_loader
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        assert check_alias_registered("hrt"), \
            "别名 'hrt' 应该已注册"
        assert check_alias_registered("hrc"), \
            "别名 'hrc' 应该已注册"

    @pytest.mark.asyncio
    async def test_config_registered_on_load(self, test_suite: E2ETestSuite):
        """测试加载时配置正确注册"""
        loader = test_suite.client.plugin_loader
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        assert check_config_registered(test_suite, PLUGIN_NAME), \
            "插件配置应该已注册"

        config_service = test_suite.services.plugin_config
        registered = config_service.get_registered_configs(PLUGIN_NAME)
        assert "reload_count" in registered
        assert "test_string" in registered

    @pytest.mark.asyncio
    async def test_handler_registered_on_load(self, test_suite: E2ETestSuite):
        """测试加载时事件处理器正确注册"""
        loader = test_suite.client.plugin_loader
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        handler_count = check_handler_registered(test_suite, PLUGIN_NAME)
        assert handler_count > 0, "应该有至少一个事件处理器已注册"

    @pytest.mark.asyncio
    async def test_command_works_after_load(self, test_suite: E2ETestSuite):
        """测试加载后命令能正常工作"""
        loader = test_suite.client.plugin_loader
        await loader.load_external_plugins(PLUGIN_ROOT)
        await asyncio.sleep(0.01)

        await test_suite.inject_group_message("/reload_test_cmd")
        await asyncio.sleep(0.01)

        test_suite.assert_reply_sent()
        calls = test_suite.get_api_calls("send_group_msg")
        assert len(calls) >= 1
        message = str(calls[-1].get("message", ""))
        assert "original_response" in message
