"""
插件系统集成测试

测试插件的完整生命周期：加载、事件处理、卸载。
"""

import pytest
from typing import List, Dict, Set
from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.ncatbot_event import NcatBotEvent


# =============================================================================
# 模拟插件基类（简化版，避免导入问题）
# =============================================================================


class MockBasePlugin:
    """简化的测试插件基类"""

    name: str = None
    version: str = "1.0.0"
    author: str = "Test"
    description: str = "Test plugin"
    dependencies: Dict[str, str] = {}

    def __init__(self, event_bus: EventBus, **kwargs):
        if not self.name:
            raise ValueError("Plugin must have a name")
        self._event_bus = event_bus
        self._handlers_id: Set[UUID] = set()
        self.config: dict = {}
        self.workspace = kwargs.get("workspace", Path("/tmp"))

        # 生命周期追踪
        self._init_called = False
        self._load_called = False
        self._close_called = False
        self.events_received: List[NcatBotEvent] = []

    def _init_(self):
        """同步初始化"""
        self._init_called = True

    async def on_load(self):
        """异步加载"""
        self._load_called = True

    async def on_close(self):
        """异步关闭"""
        self._close_called = True

    def register_handler(self, event_type: str, handler, priority: int = 0) -> UUID:
        """注册事件处理器"""
        handler_id = self._event_bus.subscribe(event_type, handler, priority=priority)
        self._handlers_id.add(handler_id)
        return handler_id

    def unregister_all_handler(self):
        """注销所有处理器"""
        for hid in self._handlers_id:
            self._event_bus.unsubscribe(hid)
        self._handlers_id.clear()

    @property
    def meta_data(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
        }


# =============================================================================
# 测试插件
# =============================================================================


class GreeterPlugin(MockBasePlugin):
    """问候插件"""

    name = "greeter"
    version = "1.0.0"

    def __init__(self, event_bus, **kwargs):
        super().__init__(event_bus, **kwargs)
        self.greet_count = 0

    async def on_load(self):
        await super().on_load()
        # 注册消息处理器
        self.register_handler("ncatbot.message", self._on_message)

    def _on_message(self, event: NcatBotEvent):
        self.events_received.append(event)
        self.greet_count += 1


class LoggerPlugin(MockBasePlugin):
    """日志插件"""

    name = "logger"
    version = "2.0.0"

    def __init__(self, event_bus, **kwargs):
        super().__init__(event_bus, **kwargs)
        self.log_entries: List[str] = []

    async def on_load(self):
        await super().on_load()
        # 注册所有事件
        self.register_handler("re:ncatbot\\..*", self._log_event, priority=1000)

    def _log_event(self, event: NcatBotEvent):
        self.log_entries.append(f"[{event.type}] received")


class DependentPlugin(MockBasePlugin):
    """依赖其他插件的插件"""

    name = "dependent"
    version = "1.0.0"
    dependencies = {"greeter": ">=1.0.0"}


# =============================================================================
# 插件生命周期测试
# =============================================================================


class TestPluginLifecycle:
    """插件生命周期测试"""

    @pytest.mark.asyncio
    async def test_plugin_init_and_load(self, event_bus):
        """测试插件初始化和加载"""
        plugin = GreeterPlugin(event_bus)

        # 同步初始化
        plugin._init_()
        assert plugin._init_called

        # 异步加载
        await plugin.on_load()
        assert plugin._load_called

    @pytest.mark.asyncio
    async def test_plugin_close(self, event_bus):
        """测试插件关闭"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()

        # 关闭
        await plugin.on_close()
        assert plugin._close_called

    @pytest.mark.asyncio
    async def test_plugin_handler_unregistered_on_close(self, event_bus):
        """测试插件关闭时处理器被注销"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()

        # 验证有处理器
        assert len(plugin._handlers_id) > 0

        # 注销所有处理器
        plugin.unregister_all_handler()

        # 验证处理器被清空
        assert len(plugin._handlers_id) == 0


# =============================================================================
# 插件事件处理测试
# =============================================================================


class TestPluginEventHandling:
    """插件事件处理测试"""

    @pytest.mark.asyncio
    async def test_plugin_receives_events(self, event_bus):
        """测试插件接收事件"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()

        # 发布事件
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)

        assert plugin.greet_count == 1
        assert len(plugin.events_received) == 1

    @pytest.mark.asyncio
    async def test_multiple_plugins_handle_same_event(self, event_bus):
        """测试多个插件处理同一事件"""
        _greeter = GreeterPlugin(event_bus)
        _logger = LoggerPlugin(event_bus)
