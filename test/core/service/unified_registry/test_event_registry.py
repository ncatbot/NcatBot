"""EventRegistry 单元测试

测试事件注册表的所有功能：
- notice/request 处理器注册
- 插件撤销
- 清理
"""

import pytest

from ncatbot.core.service.builtin.unified_registry.filter_system.event_registry import (
    EventRegistry,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def registry():
    """创建新的事件注册表"""
    return EventRegistry()


# =============================================================================
# 初始化测试
# =============================================================================


class TestEventRegistryInit:
    """测试事件注册表初始化"""

    def test_default_init(self, registry):
        """测试默认初始化"""
        assert registry._notice_handlers == {}
        assert registry._request_handlers == {}

    def test_handlers_properties_empty(self, registry):
        """测试空处理器列表"""
        assert registry.notice_handlers == []
        assert registry.request_handlers == []


# =============================================================================
# 处理器注册测试
# =============================================================================


class TestHandlerRegistration:
    """测试处理器注册"""

    def test_register_notice_handler(self, registry):
        """测试注册 notice 处理器"""

        def handler(event):
            pass

        result = registry.notice_handler(handler)

        assert result is handler
        assert handler in registry.notice_handlers

    def test_register_request_handler(self, registry):
        """测试注册 request 处理器"""

        def handler(event):
            pass

        result = registry.request_handler(handler)

        assert result is handler
        assert handler in registry.request_handlers

    def test_register_multiple_handlers(self, registry):
        """测试注册多个处理器"""
        handlers = [lambda e: None for _ in range(5)]

        for h in handlers:
            registry.notice_handler(h)

        assert len(registry.notice_handlers) == 5

    def test_handler_with_plugin_name(self, registry):
        """测试带插件名的处理器注册"""
        EventRegistry.set_current_plugin_name("test_plugin")

        def handler(event):
            pass

        registry.notice_handler(handler)

        assert registry._notice_handlers[handler] == "test_plugin"

        # 清理
        EventRegistry.set_current_plugin_name("")


# =============================================================================
# 插件撤销测试
# =============================================================================


class TestPluginRevocation:
    """测试插件撤销"""

    def test_revoke_plugin_notice_handlers(self, registry):
        """测试撤销插件的 notice 处理器"""
        EventRegistry.set_current_plugin_name("plugin_a")

        def handler_a1(e):
            pass

        def handler_a2(e):
            pass

        registry.notice_handler(handler_a1)
        registry.notice_handler(handler_a2)

        EventRegistry.set_current_plugin_name("plugin_b")

        def handler_b(e):
            pass

        registry.notice_handler(handler_b)

        assert len(registry.notice_handlers) == 3

        registry.revoke_plugin("plugin_a")

        assert len(registry.notice_handlers) == 1
        assert handler_b in registry.notice_handlers
        assert handler_a1 not in registry.notice_handlers
        assert handler_a2 not in registry.notice_handlers

        # 清理
        EventRegistry.set_current_plugin_name("")

    def test_revoke_plugin_request_handlers(self, registry):
        """测试撤销插件的 request 处理器"""
        EventRegistry.set_current_plugin_name("plugin_x")

        def handler_x(e):
            pass

        registry.request_handler(handler_x)

        EventRegistry.set_current_plugin_name("plugin_y")

        def handler_y(e):
            pass

        registry.request_handler(handler_y)

        registry.revoke_plugin("plugin_x")

        assert len(registry.request_handlers) == 1
        assert handler_y in registry.request_handlers

        # 清理
        EventRegistry.set_current_plugin_name("")

    def test_revoke_nonexistent_plugin(self, registry):
        """测试撤销不存在的插件"""

        def handler(e):
            pass

        registry.notice_handler(handler)

        # 应该不会报错
        registry.revoke_plugin("nonexistent")

        assert len(registry.notice_handlers) == 1


# =============================================================================
# 清理测试
# =============================================================================


class TestClear:
    """测试清理功能"""

    def test_clear_all_handlers(self, registry):
        """测试清理所有处理器"""
        for i in range(3):
            registry.notice_handler(lambda e: None)
            registry.request_handler(lambda e: None)

        assert len(registry.notice_handlers) == 3
        assert len(registry.request_handlers) == 3

        registry.clear()

        assert len(registry.notice_handlers) == 0
        assert len(registry.request_handlers) == 0


# =============================================================================
# 集成测试
# =============================================================================


class TestEventRegistryIntegration:
    """事件注册表集成测试"""

    def test_full_lifecycle(self, registry):
        """测试完整生命周期"""
        # 注册 plugin_a 的处理器
        EventRegistry.set_current_plugin_name("plugin_a")

        @registry.notice_handler
        def notice_a(event):
            return "notice_a"

        @registry.request_handler
        def request_a(event):
            return "request_a"

        # 注册 plugin_b 的处理器
        EventRegistry.set_current_plugin_name("plugin_b")

        @registry.notice_handler
        def notice_b(event):
            return "notice_b"

        # 验证注册
        assert len(registry.notice_handlers) == 2
        assert len(registry.request_handlers) == 1

        # 卸载 plugin_a
        registry.revoke_plugin("plugin_a")

        assert len(registry.notice_handlers) == 1
        assert len(registry.request_handlers) == 0
        assert notice_b in registry.notice_handlers

        # 清理
        registry.clear()
        EventRegistry.set_current_plugin_name("")

        assert len(registry.notice_handlers) == 0
