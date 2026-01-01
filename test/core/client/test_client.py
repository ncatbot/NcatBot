"""
BotClient 集成测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from ncatbot.utils.error import NcatBotError


@pytest.fixture(autouse=True)
def reset_bot_client_singleton():
    """每个测试前重置 BotClient 单例状态"""
    from ncatbot.core.client.client import BotClient
    BotClient._initialized = False
    yield
    BotClient._initialized = False


class TestBotClientSingleton:
    """测试 BotClient 单例"""

    def test_client_singleton_first_instance(self):
        """第一次实例化成功"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        assert client is not None
        assert BotClient._initialized is True

    def test_client_singleton_second_instance_raises(self):
        """第二次实例化抛出异常"""
        from ncatbot.core.client.client import BotClient
        
        client1 = BotClient()
        
        with pytest.raises(NcatBotError, match="BotClient 实例只能创建一次"):
            client2 = BotClient()


class TestBotClientComponents:
    """测试 BotClient 组件初始化"""

    def test_client_components_initialized(self):
        """所有组件正确初始化"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        assert client.event_bus is not None
        assert client.services is not None
        # api 和 dispatcher 在 _setup_api 调用后才初始化
        assert client.api is None  # 延迟绑定
        assert client.dispatcher is None  # 延迟初始化

    def test_client_event_bus_type(self):
        """EventBus 类型正确"""
        from ncatbot.core.client.client import BotClient
        from ncatbot.core.client.event_bus import EventBus
        
        client = BotClient()
        
        assert isinstance(client.event_bus, EventBus)

    def test_client_services_type(self):
        """ServiceManager 类型正确"""
        from ncatbot.core.client.client import BotClient
        from ncatbot.core.service import ServiceManager
        
        client = BotClient()
        
        assert isinstance(client.services, ServiceManager)


class TestBotClientInheritance:
    """测试 BotClient 继承"""

    def test_client_inherits_registry(self):
        """继承 EventRegistry 的所有方法"""
        from ncatbot.core.client.client import BotClient
        from ncatbot.core.client.registry import EventRegistry
        
        client = BotClient()
        
        assert isinstance(client, EventRegistry)
        assert hasattr(client, "on_group_message")
        assert hasattr(client, "on_private_message")
        assert hasattr(client, "on_notice")
        assert hasattr(client, "on_startup")
        assert hasattr(client, "subscribe")
        assert hasattr(client, "register_handler")

    def test_client_decorators_work(self):
        """装饰器方法正常工作"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        @client.on_group_message()
        async def handler(event):
            pass
        
        assert "message_event" in client.event_bus._exact


class TestBotClientPluginManagement:
    """测试 BotClient 插件管理"""

    def test_get_registered_plugins_empty(self):
        """无插件时返回空列表"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        client.plugin_loader = None
        
        result = client.get_registered_plugins()
        
        assert result == []

    def test_get_registered_plugins_with_loader(self):
        """有插件加载器时返回插件列表"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        mock_plugin1 = MagicMock()
        mock_plugin2 = MagicMock()
        mock_loader = MagicMock()
        mock_loader.plugins = {"plugin1": mock_plugin1, "plugin2": mock_plugin2}
        client.plugin_loader = mock_loader
        
        result = client.get_registered_plugins()
        
        assert len(result) == 2
        assert mock_plugin1 in result
        assert mock_plugin2 in result

    def test_get_plugin_by_type_found(self):
        """按类型获取插件 - 找到"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        class TestPluginType:
            pass
        
        mock_plugin = TestPluginType()
        mock_loader = MagicMock()
        mock_loader.plugins = {"test": mock_plugin}
        client.plugin_loader = mock_loader
        
        result = client.get_plugin(TestPluginType)
        
        assert result is mock_plugin

    def test_get_plugin_by_type_not_found(self):
        """按类型获取插件 - 未找到抛出异常"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        class TestPluginType:
            pass
        
        class OtherPluginType:
            pass
        
        mock_plugin = OtherPluginType()
        mock_loader = MagicMock()
        mock_loader.plugins = {"other": mock_plugin}
        client.plugin_loader = mock_loader
        
        with pytest.raises(ValueError, match="未找到"):
            client.get_plugin(TestPluginType)


class TestBotClientBuiltinHandlers:
    """测试内置处理器"""

    def test_builtin_startup_handler_registered(self):
        """内置启动处理器注册"""
        from ncatbot.core.client.client import BotClient
        
        client = BotClient()
        
        assert "meta_event" in client.event_bus._exact
