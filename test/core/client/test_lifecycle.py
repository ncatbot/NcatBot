"""
LifecycleManager 测试
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from ncatbot.core.client.lifecycle import LifecycleManager, StartArgs, LEGAL_ARGS
from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.registry import EventRegistry
from ncatbot.utils.error import NcatBotError

# 预导入 plugin_system 模块以便 patch 可以正常工作
import ncatbot.plugin_system


class TestStartArgsType:
    """测试 StartArgs 类型定义"""

    def test_legal_args_contains_expected_keys(self):
        """LEGAL_ARGS 包含预期的参数"""
        expected_args = [
            "bt_uin",
            "root",
            "ws_uri",
            "webui_uri",
            "ws_token",
            "webui_token",
            "ws_listen_ip",
            "remote_mode",
            "enable_webui",
            "enable_webui_interaction",
            "debug"
        ]
        
        for arg in expected_args:
            assert arg in LEGAL_ARGS


class TestLifecycleManagerInit:
    """测试 LifecycleManager 初始化"""

    def test_init_components(self, mock_services, event_bus, event_registry):
        """初始化各组件"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        assert manager.services is mock_services
        assert manager.api is None  # API 在启动后才初始化
        assert manager.event_bus is event_bus
        assert manager.registry is event_registry
        assert manager._running is False
        assert manager.crash_flag is False
        assert manager.plugin_loader is None

    def test_init_backend_attributes(self, mock_services, event_bus, event_registry):
        """初始化后台运行相关属性"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        assert manager.lock is None
        assert manager.release_callback is None


class TestLifecycleManagerStartValidation:
    """测试启动参数验证"""

    def test_start_validates_legal_args(self, mock_services, event_bus, event_registry):
        """启动时验证合法参数"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True  # 使用 mock 模式
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader:
                    mock_loader_instance = MagicMock()
                    mock_loader.return_value = mock_loader_instance
                    
                    # 合法参数应该正常工作
                    manager.start(bt_uin="123456", debug=True)
                    
                    # 验证 config 被更新
                    mock_config.update_value.assert_any_call("bt_uin", "123456")
                    mock_config.update_value.assert_any_call("debug", True)

    def test_start_rejects_illegal_args(self, mock_services, event_bus, event_registry):
        """拒绝非法参数"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        with pytest.raises(NcatBotError, match="非法参数"):
            manager.start(illegal_param="value")

    def test_start_ignores_none_values(self, mock_services, event_bus, event_registry):
        """忽略 None 值参数"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader:
                    mock_loader_instance = MagicMock()
                    mock_loader.return_value = mock_loader_instance
                    
                    manager.start(bt_uin="123", root=None)
                    
                    # None 值不应被更新
                    calls = mock_config.update_value.call_args_list
                    keys_updated = [call[0][0] for call in calls]
                    assert "root" not in keys_updated


class TestLifecycleManagerMockMode:
    """测试 Mock 模式"""

    def test_mock_start(self, mock_services, event_bus, event_registry):
        """Mock 模式启动不连接真实服务"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader:
                    mock_loader_instance = MagicMock()
                    mock_loader.return_value = mock_loader_instance
                    
                    with patch("ncatbot.core.client.lifecycle.launch_napcat_service") as mock_launch:
                        manager.start(bt_uin="123456")
                        
                        # Mock 模式不应调用真实服务
                        mock_launch.assert_not_called()


class TestLifecycleManagerExit:
    """测试退出流程"""

    def test_bot_exit_unloads_plugins(self, mock_services, event_bus, event_registry):
        """退出时卸载所有插件"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager._running = True
        
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.unload_all = AsyncMock()
        manager.plugin_loader = mock_plugin_loader
        
        with patch("ncatbot.core.client.lifecycle.status") as mock_status:
            manager.bot_exit()
            
            mock_status.exit = True
            mock_plugin_loader.unload_all.assert_called_once()

    def test_bot_exit_when_not_running(self, mock_services, event_bus, event_registry):
        """未运行时退出给出警告"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager._running = False
        
        # 不应抛出异常
        manager.bot_exit()

    def test_bot_exit_sets_exit_flag(self, mock_services, event_bus, event_registry):
        """退出设置 exit 标志"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager._running = True
        manager.plugin_loader = None
        
        with patch("ncatbot.core.client.lifecycle.status") as mock_status:
            manager.bot_exit()
            
            assert mock_status.exit is True


class TestLifecycleManagerRunModes:
    """测试运行模式"""

    def test_run_frontend_alias(self, mock_services, event_bus, event_registry):
        """run_frontend 别名正确"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        assert manager.run_frontend == manager.run_blocking
        assert manager.run == manager.run_frontend

    def test_run_backend_alias(self, mock_services, event_bus, event_registry):
        """run_backend 别名正确"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        assert manager.run_backend == manager.run_non_blocking

    def test_run_frontend_calls_start(self, mock_services, event_bus, event_registry):
        """run_frontend 调用 start"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.start = MagicMock(side_effect=KeyboardInterrupt)
        manager.bot_exit = MagicMock()
        
        manager.run_frontend(bt_uin="123456")
        
        manager.start.assert_called_once_with(bt_uin="123456")
        manager.bot_exit.assert_called_once()


class TestLifecycleManagerBackendMode:
    """测试后台模式"""

    def test_run_backend_returns_api(self, mock_services, event_bus, event_registry):
        """run_backend 返回 API 实例"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        mock_api = MagicMock()
        
        # Mock start 方法：模拟正常启动，通过 startup handler 释放锁
        def mock_start(**kwargs):
            # 正常启动后，触发 startup handler 来释放锁
            import time
            time.sleep(0.01)  # 给主线程时间设置锁
            manager.api = mock_api  # 模拟设置 api
            if manager.release_callback:
                manager.release_callback(None)
            # 保持运行，防止线程退出
            import threading
            threading.Event().wait(timeout=0.1)
        
        manager.start = mock_start
        
        result = manager.run_backend(bt_uin="123456")
        
        assert result is mock_api

    def test_run_backend_crash(self, mock_services, event_bus, event_registry):
        """run_backend 启动崩溃抛出异常"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        
        def mock_start(**kwargs):
            manager.crash_flag = True
            if manager.release_callback:
                manager.release_callback(None)
        
        manager.start = mock_start
        
        with pytest.raises(NcatBotError, match="启动失败"):
            manager.run_backend(bt_uin="123456")


class TestLifecycleManagerPluginLoader:
    """测试插件加载器管理"""

    def test_plugin_loader_initialized_on_start(self, mock_services, event_bus, event_registry):
        """启动时初始化插件加载器"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader_class:
                    mock_loader_instance = MagicMock()
                    mock_loader_class.return_value = mock_loader_instance
                    
                    manager.start(bt_uin="123456")
                    
                    mock_loader_class.assert_called_once()
                    assert manager.plugin_loader is mock_loader_instance


class TestLifecycleManagerStartFlow:
    """测试完整启动流程"""

    def test_start_flow_mock_mode(self, mock_services, event_bus, event_registry):
        """Mock 模式完整启动流程"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine") as mock_run_coroutine:
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader_class:
                    mock_loader_instance = MagicMock()
                    mock_loader_class.return_value = mock_loader_instance
                    
                    manager.start(bt_uin="123456")
                    
                    # 验证流程
                    mock_config.validate_config.assert_called_once()
                    mock_run_coroutine.assert_called_once()
                    assert manager._running is True

    def test_start_sets_running_flag(self, mock_services, event_bus, event_registry):
        """启动设置 running 标志"""
        manager = LifecycleManager(mock_services, event_bus, event_registry)
        manager.mock_mode = True
        
        assert manager._running is False
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as mock_loader_class:
                    mock_loader_class.return_value = MagicMock()
                    
                    manager.start(bt_uin="123456")
        
        assert manager._running is True
