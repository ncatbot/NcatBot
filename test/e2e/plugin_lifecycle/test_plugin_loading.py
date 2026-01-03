"""
插件加载端到端测试

测试插件的加载流程和初始化：
- 基本加载流程
- 生命周期钩子调用
- 与各服务的协作初始化
"""

import pytest

from .conftest import get_plugin_class
from ncatbot.utils.testing import E2ETestSuite


class TestBasicPluginLoading:
    """基础插件加载测试"""

    @pytest.mark.asyncio
    async def test_basic_plugin_loading_complete(
        self, test_suite: E2ETestSuite, basic_plugin_name
    ):
        """测试插件基础加载功能（综合测试）

        测试内容：
        - 插件成功加载
        - _init_ 钩子被调用
        - on_load 钩子被调用
        - 插件被注册到加载器
        - 可通过名称获取插件
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(basic_plugin_name)

        # 2. 测试插件基本信息
        assert plugin is not None
        assert plugin.name == "basic_test_plugin"
        assert plugin.version == "1.0.0"

        # 3. 测试生命周期钩子
        BasicTestPlugin = get_plugin_class(basic_plugin_name)
        assert BasicTestPlugin.init_called is True
        assert BasicTestPlugin.load_count == 1

        # 4. 测试插件注册
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" in plugins

        # 5. 测试插件获取
        retrieved_plugin = test_suite.client.plugin_loader.get_plugin(
            "basic_test_plugin"
        )
        assert retrieved_plugin is not None
        assert retrieved_plugin.name == "basic_test_plugin"


class TestPluginLoadingWithCommands:
    """带命令的插件加载测试"""

    @pytest.mark.asyncio
    async def test_command_plugin_loading_complete(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试命令插件加载功能（综合测试）

        测试内容：
        - 命令在加载时被注册
        - 命令别名被注册
        - 加载后命令可执行
        """
        # 1. 加载插件
        await test_suite.register_plugin(command_plugin_name)

        # 2. 检查命令注册
        registry = test_suite.services.unified_registry
        registry.initialize_if_needed()

        commands = registry.command_registry.get_all_commands()
        command_names = [path[0] for path in commands.keys()]
        assert "cmd_test" in command_names

        # 3. 检查别名注册
        aliases = registry.command_registry.get_all_aliases()
        alias_names = [path[0] for path in aliases.keys()]
        assert "ct" in alias_names

        # 4. 测试命令执行
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent("cmd_test executed")


class TestPluginLoadingWithConfig:
    """带配置的插件加载测试"""

    @pytest.mark.asyncio
    async def test_config_plugin_loading_complete(
        self, test_suite: E2ETestSuite, config_plugin_name
    ):
        """测试配置插件加载功能（综合测试）

        测试内容：
        - 配置默认值被应用
        - 配置可通过插件实例访问
        """
        # 1. 加载插件
        plugin = await test_suite.register_plugin(config_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)

        # 2. 检查 PluginConfigService 中的配置
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("config_test_plugin")

        assert "api_key" in configs
        assert "max_retries" in configs
        assert "enabled" in configs

        # 3. 验证加载时记录的配置值
        assert ConfigTestPlugin.config_values_on_load["api_key"] == "default_api_key"
        assert ConfigTestPlugin.config_values_on_load["max_retries"] == 3
        assert ConfigTestPlugin.config_values_on_load["enabled"] in [
            True,
            "True",
            "true",
        ]

        # 4. 测试配置通过插件实例访问
        assert plugin.config["api_key"] == "default_api_key"
        assert plugin.config["max_retries"] == 3


class TestPluginLoadingWithHandlers:
    """带事件处理器的插件加载测试"""

    @pytest.mark.asyncio
    async def test_handler_plugin_loading_complete(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试事件处理器插件加载功能（综合测试）

        测试内容：
        - 处理器被注册
        - 消息处理器能接收事件
        """
        # 1. 加载插件
        await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = test_suite.client.get_plugin_class_by_name(
            "handler_test_plugin"
        )

        # 2. 检查处理器注册
        assert len(HandlerTestPlugin.handler_ids) == 2
        assert len(test_suite.client.get_plugin(HandlerTestPlugin)._handlers_id) == 2

        # 3. 测试消息处理器接收事件
        await test_suite.inject_group_message("Hello from test")

        assert len(HandlerTestPlugin.message_events) >= 1
        assert "Hello from test" in str(HandlerTestPlugin.message_events)


class TestFullFeaturePluginLoading:
    """完整功能插件加载测试"""

    @pytest.mark.asyncio
    async def test_full_feature_plugin_loading_complete(
        self, test_suite: E2ETestSuite, full_feature_plugin_name
    ):
        """测试完整功能插件加载（综合测试）

        测试内容：
        - 配置服务正常工作
        - 事件处理器被注册
        - 命令被注册
        - 命令可执行
        - 生命周期钩子被调用
        """
        # 1. 加载插件
        await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = test_suite.client.get_plugin_class_by_name(
            "full_feature_plugin"
        )

        # 2. 测试配置服务
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert "feature_enabled" in configs

        # 3. 测试事件处理器
        assert len(test_suite.client.get_plugin(FullFeaturePlugin)._handlers_id) == 2

        # 4. 测试命令注册
        registry = test_suite.services.unified_registry
        registry.initialize_if_needed()
        commands = registry.command_registry.get_all_commands()
        command_names = [path[0] for path in commands.keys()]
        assert "ff_status" in command_names

        # 5. 测试命令执行
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()
        assert "ff_status" in FullFeaturePlugin.command_executions

        # 6. 测试生命周期钩子
        assert "_init_" in FullFeaturePlugin.lifecycle_events
        assert "on_load" in FullFeaturePlugin.lifecycle_events


class TestMultiplePluginLoading:
    """多插件加载测试"""

    @pytest.mark.asyncio
    async def test_multiple_plugins_loading_complete(
        self, test_suite: E2ETestSuite, handler_plugin_name, config_plugin_name
    ):
        """测试多插件加载功能（综合测试）

        测试内容：
        - 多个插件可以同时加载
        - 插件之间不互相干扰
        - 各插件功能独立正常
        """
        # 1. 加载多个插件
        await test_suite.register_plugin(handler_plugin_name)
        await test_suite.register_plugin(config_plugin_name)

        # 2. 检查插件都被注册
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "handler_test_plugin" in plugins
        assert "config_test_plugin" in plugins

        # 3. 获取插件类
        HandlerTestPlugin = test_suite.client.get_plugin_class_by_name(
            "handler_test_plugin"
        )
        ConfigTestPlugin = test_suite.client.get_plugin_class_by_name(
            "config_test_plugin"
        )
        assert HandlerTestPlugin is not None
        assert ConfigTestPlugin is not None

        # 4. 测试各插件功能独立
        # Handler 插件应该记录了消息事件处理器
        assert len(HandlerTestPlugin.handler_ids) == 2

        # Config 插件应该记录了配置
        assert len(ConfigTestPlugin.config_values_on_load) == 3

        # 5. 测试插件配置独立
        config_service = test_suite.services.plugin_config
        handler_configs = config_service.get_registered_configs("handler_test_plugin")
        config_configs = config_service.get_registered_configs("config_test_plugin")

        # Handler 插件没有注册配置
        assert len(handler_configs) == 0
        # Config 插件有配置
        assert len(config_configs) == 3
