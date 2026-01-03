"""
插件卸载端到端测试

测试插件的卸载流程和清理：
- 生命周期钩子调用
- 事件处理器清理
- 命令注销
- 配置项注册清理
"""

import pytest
import asyncio

from .conftest import get_plugin_class
from ncatbot.utils.testing import E2ETestSuite


class TestBasicPluginUnloading:
    """基础插件卸载测试"""

    @pytest.mark.asyncio
    async def test_basic_plugin_unloading_complete(
        self, test_suite: E2ETestSuite, basic_plugin_name
    ):
        """测试插件基础卸载功能（综合测试）

        测试内容：
        - 插件能够成功卸载
        - on_close 钩子被调用
        - 卸载后无法获取插件
        """
        # 1. 加载插件
        await test_suite.register_plugin(basic_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)

        # 验证加载成功
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" in plugins

        # 2. 卸载插件
        await test_suite.unregister_plugin("basic_test_plugin")

        # 3. 验证卸载成功
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" not in plugins

        # 4. 验证生命周期钩子被调用
        assert BasicTestPlugin.unload_count == 1

        # 5. 验证无法获取插件
        plugin = test_suite.client.plugin_loader.get_plugin("basic_test_plugin")
        assert plugin is None


class TestCommandCleanupOnUnload:
    """命令清理测试 - 端到端验证"""

    @pytest.mark.asyncio
    async def test_command_cleanup_complete(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试命令插件卸载后的清理（综合测试）

        测试内容：
        - 加载时命令能正确响应
        - 加载时别名能正确响应
        - 卸载后命令不再响应
        - 卸载后别名不再响应
        - 插件从注册表移除
        """
        # 1. 加载插件
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 2. 测试命令响应
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent("cmd_test executed")
        assert "cmd_test" in CommandTestPlugin.command_calls

        # 清空历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 3. 测试别名响应
        await test_suite.inject_group_message("ct")
        test_suite.assert_reply_sent("cmd_test executed")

        # 清空历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 4. 卸载插件
        await test_suite.unregister_plugin("command_test_plugin")

        # 5. 测试命令不再响应
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_no_reply()

        # 6. 测试别名不再响应
        await test_suite.inject_group_message("ct")
        test_suite.assert_no_reply()

        # 7. 验证插件从注册表移除
        plugin = test_suite.client.plugin_loader.get_plugin("command_test_plugin")
        assert plugin is None


class TestConfigCleanupOnUnload:
    """配置清理测试"""

    @pytest.mark.asyncio
    async def test_config_cleanup_complete(
        self, test_suite: E2ETestSuite, config_plugin_name
    ):
        """测试配置插件卸载后的清理（综合测试）

        测试内容：
        - 配置项注册被清理
        - 配置值被保留（持久化）
        """
        # 1. 加载插件
        await test_suite.register_plugin(config_plugin_name)
        config_service = test_suite.services.plugin_config

        # 2. 验证配置已注册
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 3

        # 3. 修改配置
        plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        plugin.set_config("api_key", "modified_key")

        # 4. 卸载插件
        await test_suite.unregister_plugin("config_test_plugin")

        # 5. 验证配置项注册被清理
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 0

        # 6. 验证配置值仍然存在（持久化）
        value = config_service.get("config_test_plugin", "api_key")
        assert value == "modified_key"


class TestHandlerCleanupOnUnload:
    """事件处理器清理测试"""

    @pytest.mark.asyncio
    async def test_handler_cleanup_complete(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试事件处理器卸载后的清理（综合测试）

        测试内容：
        - 处理器被正确注册
        - 卸载后处理器被注销
        - 卸载后处理器不被触发
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 2. 验证处理器已注册
        assert len(plugin._handlers_id) == 2

        # 3. 测试处理器能接收消息
        await test_suite.inject_group_message("Before unload")
        events_before = len(HandlerTestPlugin.message_events)
        assert events_before >= 1

        # 4. 卸载插件
        await test_suite.unregister_plugin("handler_test_plugin")

        # 5. 验证加载器中没有该插件
        loaded = test_suite.client.plugin_loader.get_plugin("handler_test_plugin")
        assert loaded is None

        # 6. 测试处理器不再被触发
        await test_suite.inject_group_message("After unload")
        assert len(HandlerTestPlugin.message_events) == events_before


class TestFullFeaturePluginUnloading:
    """完整功能插件卸载测试 - 端到端验证"""

    @pytest.mark.asyncio
    async def test_full_feature_unloading_complete(
        self, test_suite: E2ETestSuite, full_feature_plugin_name
    ):
        """测试完整功能插件卸载（综合测试）

        测试内容：
        - 所有资源被正确清理
        - 命令不再响应
        - 事件处理器不再触发
        - 生命周期钩子被调用
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)
        config_service = test_suite.services.plugin_config

        # 2. 验证所有资源已初始化
        assert len(plugin._handlers_id) == 2
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 2

        # 3. 端到端验证：命令能正确响应（这也会触发事件处理器）
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()

        # 4. 等待并记录处理器事件数（命令消息也会触发处理器）
        await asyncio.sleep(0.01)
        events_before = len(FullFeaturePlugin.handler_events)
        assert events_before >= 1  # 至少有命令消息的事件

        # 清空历史但不重置计数器（保留 handler_events 用于后续对比）
        test_suite.clear_call_history()

        # 5. 卸载插件
        await test_suite.unregister_plugin("full_feature_plugin")

        # 6. 验证 on_close 被调用
        assert "on_close" in FullFeaturePlugin.lifecycle_events

        # 7. 验证配置注册被清理
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 0

        # 8. 验证插件已从加载器移除
        plugin = test_suite.client.plugin_loader.get_plugin("full_feature_plugin")
        assert plugin is None

        # 9. 端到端验证：命令不再响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_no_reply()

        # 10. 测试事件处理器不再触发
        await test_suite.inject_group_message("after unload message")
        await asyncio.sleep(0.01)
        # 事件计数不应增加（卸载后的消息不会触发处理器）
        assert len(FullFeaturePlugin.handler_events) == events_before


class TestMultiplePluginUnloading:
    """多插件卸载测试"""

    @pytest.mark.asyncio
    async def test_multiple_plugin_unloading_complete(
        self,
        test_suite: E2ETestSuite,
        basic_plugin_name,
        command_plugin_name,
        config_plugin_name,
    ):
        """测试多插件卸载功能（综合测试）

        测试内容：
        - 卸载一个插件不影响其他插件
        - 可以卸载所有插件
        """
        # 1. 加载多个插件
        await test_suite.register_plugin(basic_plugin_name)
        await test_suite.register_plugin(command_plugin_name)
        await test_suite.register_plugin(config_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)
        config_service = test_suite.services.plugin_config

        # 2. 卸载命令插件
        await test_suite.unregister_plugin("command_test_plugin")

        # 3. 验证配置插件仍然存在
        config_plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        assert config_plugin is not None

        # 4. 验证配置插件的配置仍然存在
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 3

        # 5. 卸载所有剩余插件
        await test_suite.unregister_plugin("basic_test_plugin")
        await test_suite.unregister_plugin("config_test_plugin")

        # 6. 验证生命周期钩子被调用
        assert BasicTestPlugin.unload_count == 1

        # 7. 验证所有插件都已卸载
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" not in plugins
        assert "command_test_plugin" not in plugins
        assert "config_test_plugin" not in plugins
