"""
服务协作端到端测试

测试插件生命周期与各服务的协作：
- register_handler 与 EventBus 的协作
- unified_registry 与命令系统的协作
- PluginConfigService 与配置系统的协作
- 多服务同时协作的场景
"""

import pytest
import asyncio

from ncatbot.core.client import NcatBotEvent
from ncatbot.utils.testing import E2ETestSuite
from .conftest import get_plugin_class


class TestRegisterHandlerCoordination:
    """register_handler 与 EventBus 协作测试"""

    @pytest.mark.asyncio
    async def test_register_handler_coordination_complete(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试 register_handler 与 EventBus 协作（综合测试）

        测试内容：
        - 处理器优先级被尊重
        - 卸载时处理器被取消订阅
        - 自定义事件被接收
        - 取消注册后处理器不被调用
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 2. 验证处理器注册成功
        assert len(plugin._handlers_id) == 2

        # 3. 测试自定义事件被接收
        custom_event = NcatBotEvent("handler_test.custom_event", {"key": "value"})
        await test_suite.event_bus.publish(custom_event)
        assert len(HandlerTestPlugin.custom_events) >= 1

        # 4. 测试取消注册后处理器不被调用
        await test_suite.inject_group_message("Before unregister")
        count_before = len(HandlerTestPlugin.message_events)

        plugin.unregister_all_handler()
        await test_suite.inject_group_message("After unregister")
        assert len(HandlerTestPlugin.message_events) == count_before

        # 5. 重新加载插件以测试卸载清理
        await test_suite.unregister_plugin("handler_test_plugin")
        await test_suite.register_plugin(handler_plugin_name)
        plugin = test_suite.client.plugin_loader.get_plugin("handler_test_plugin")
        new_handler_ids = list(plugin._handlers_id)

        # 6. 卸载插件并验证事件总线中的订阅已被移除
        await test_suite.unregister_plugin("handler_test_plugin")
        event_bus = test_suite.event_bus
        for handler_id in new_handler_ids:
            result = event_bus.unsubscribe(handler_id)
            assert result is False


class TestUnifiedRegistryCoordination:
    """unified_registry 与命令系统协作测试"""

    @pytest.mark.asyncio
    async def test_unified_registry_coordination_complete(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试 unified_registry 与命令系统协作（综合测试）

        测试内容：
        - 命令通过 unified_registry 分发
        - 带参数的命令正常工作
        - 命令前缀处理正确
        - 插件变更时 registry 重新初始化
        """
        # 1. 加载插件
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)
        registry = test_suite.services.unified_registry

        # 2. 测试命令通过 unified_registry 分发
        await test_suite.inject_group_message("cmd_test")
        assert "cmd_test" in CommandTestPlugin.command_calls
        test_suite.assert_reply_sent()

        # 清空历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 3. 测试带参数的命令
        await test_suite.inject_group_message("cmd_echo hello_world")
        assert any(
            "cmd_echo:hello_world" in call for call in CommandTestPlugin.command_calls
        )
        test_suite.assert_reply_sent("Echo: hello_world")

        # 清空历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 4. 测试命令前缀处理
        # 测试无前缀
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent()

        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 测试有前缀
        await test_suite.inject_group_message("/cmd_test")
        test_suite.assert_reply_sent()

        # 5. 测试 registry 重新初始化
        registry.initialize_if_needed()
        assert registry._initialized is True

        await test_suite.unregister_plugin("command_test_plugin")
        assert registry._initialized is True


class TestPluginConfigServiceCoordination:
    """PluginConfigService 与配置系统协作测试"""

    @pytest.mark.asyncio
    async def test_plugin_config_service_coordination_complete(
        self, test_suite: E2ETestSuite, config_plugin_name, handler_plugin_name
    ):
        """测试 PluginConfigService 与配置系统协作（综合测试）

        测试内容：
        - 插件间配置隔离
        - 配置跨操作持久化
        - 首次加载使用默认值
        - 通过插件修改配置
        """
        # 1. 加载多个插件测试配置隔离
        await test_suite.register_plugin(config_plugin_name)
        await test_suite.register_plugin(handler_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)
        config_service = test_suite.services.plugin_config

        # 2. 验证配置隔离
        config_configs = config_service.get_registered_configs("config_test_plugin")
        handler_configs = config_service.get_registered_configs("handler_test_plugin")
        assert len(config_configs) == 3
        assert len(handler_configs) == 0

        # 3. 验证首次加载时使用默认值
        assert ConfigTestPlugin.config_values_on_load["api_key"] == "default_api_key"
        assert ConfigTestPlugin.config_values_on_load["max_retries"] == 3
        assert ConfigTestPlugin.config_values_on_load["enabled"] is True

        # 4. 测试通过插件修改配置
        await test_suite.inject_group_message("cfg_set api_key new_key")
        assert len(ConfigTestPlugin.config_change_history) >= 1
        # 验证配置从默认值变为新值
        assert (
            "api_key",
            "default_api_key",
            "new_key",
        ) in ConfigTestPlugin.config_change_history

        # 5. 测试配置持久化 - 卸载后值仍存在
        config_service.set("config_test_plugin", "max_retries", 10)
        value = config_service.get("config_test_plugin", "max_retries")
        assert value == 10

        await test_suite.unregister_plugin("config_test_plugin")
        value = config_service.get("config_test_plugin", "max_retries")
        assert value == 10


class TestMultiServiceCoordination:
    """多服务协作测试"""

    @pytest.mark.asyncio
    async def test_multi_service_coordination_complete(
        self, test_suite: E2ETestSuite, full_feature_plugin_name
    ):
        """测试多服务协作（综合测试）

        测试内容：
        - 所有服务协同工作
        - 卸载时所有服务清理
        - 配置与命令交互
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)
        config_service = test_suite.services.plugin_config

        # 2. 验证配置服务工作
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 2

        # 3. 验证命令系统工作
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()
        assert "ff_status" in FullFeaturePlugin.command_executions

        # 4. 验证事件处理器工作
        assert len(FullFeaturePlugin.handler_events) >= 1

        # 5. 测试配置与命令交互
        test_suite.clear_call_history()
        await test_suite.inject_group_message("ff_config set feature_value new_value")
        test_suite.assert_reply_sent()
        assert any(
            "set:feature_value=new_value" in op
            for op in FullFeaturePlugin.config_operations
        )

        # 获取配置
        test_suite.clear_call_history()
        await test_suite.inject_group_message("ff_config get feature_value")
        test_suite.assert_reply_sent()

        # 6. 测试卸载时所有服务清理
        initial_handler_count = len(plugin._handlers_id)
        assert initial_handler_count == 2

        test_suite.clear_call_history()
        FullFeaturePlugin.reset_counters()

        await test_suite.unregister_plugin("full_feature_plugin")

        # 验证配置注册被清理
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 0

        # 验证插件从加载器移除
        removed_plugin = test_suite.client.plugin_loader.get_plugin(
            "full_feature_plugin"
        )
        assert removed_plugin is None

        # 验证生命周期钩子被调用
        assert "on_close" in FullFeaturePlugin.lifecycle_events

        # 端到端验证：命令不再响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_no_reply()


class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_edge_cases_complete(
        self, test_suite: E2ETestSuite, command_plugin_name, handler_plugin_name
    ):
        """测试边界情况（综合测试）

        测试内容：
        - 重复加载同一插件
        - 卸载不存在的插件
        - 快速加载卸载循环
        - 插件操作期间的事件处理
        """
        # 1. 测试重复加载同一插件
        await test_suite.register_plugin(command_plugin_name)
        try:
            await test_suite.register_plugin(command_plugin_name)
        except Exception:
            pass

        plugin = test_suite.client.plugin_loader.get_plugin("command_test_plugin")
        assert plugin is not None

        await test_suite.unregister_plugin("command_test_plugin")

        # 2. 测试卸载不存在的插件（应该不会报错）
        await test_suite.unregister_plugin("nonexistent_plugin")

        # 3. 测试快速加载卸载循环
        for _ in range(3):
            await test_suite.register_plugin(command_plugin_name)
            await test_suite.register_plugin(handler_plugin_name)
            await test_suite.unregister_plugin("command_test_plugin")
            await test_suite.unregister_plugin("handler_test_plugin")

        # 验证最终没有测试插件
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "command_test_plugin" not in plugins
        assert "handler_test_plugin" not in plugins

        # 4. 测试插件操作期间的事件处理
        await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        await test_suite.inject_group_message("Test message 1")
        await test_suite.unregister_plugin("handler_test_plugin")
        await test_suite.inject_group_message("Test message 2")

        await asyncio.sleep(0.1)

        # 第二条消息不应该被处理
        messages_with_2 = [
            e for e in HandlerTestPlugin.message_events if "Test message 2" in str(e)
        ]
        assert len(messages_with_2) == 0
