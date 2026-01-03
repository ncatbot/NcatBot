"""FilterRegistry 单元测试

测试过滤器注册表的所有功能：
- 过滤器实例注册
- 为函数添加过滤器
- 插件撤销
"""

import pytest

from ncatbot.core.service.builtin.unified_registry.filter_system.registry import (
    FilterRegistry,
)
from ncatbot.core.service.builtin.unified_registry.filter_system.base import BaseFilter


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def registry():
    """创建新的过滤器注册表"""
    return FilterRegistry()


class MockFilter(BaseFilter):
    """测试用过滤器"""

    def __init__(self, should_pass=True):
        super().__init__()
        self.should_pass = should_pass

    def check(self, event) -> bool:
        return self.should_pass


# =============================================================================
# 初始化测试
# =============================================================================


class TestFilterRegistryInit:
    """测试过滤器注册表初始化"""

    def test_default_init(self, registry):
        """测试默认初始化"""
        assert registry._filters == {}
        assert registry._function_filters == {}


# =============================================================================
# 过滤器注册测试
# =============================================================================


class TestFilterRegistration:
    """测试过滤器注册"""

    def test_register_filter(self, registry):
        """测试注册过滤器实例"""
        filter_instance = MockFilter()

        registry.register_filter("test_filter", filter_instance)

        entry = registry.get_filter("test_filter")
        assert entry is not None
        assert entry.name == "test_filter"
        assert entry.filter_instance is filter_instance

    def test_register_filter_with_metadata(self, registry):
        """测试注册带元数据的过滤器"""
        filter_instance = MockFilter()
        metadata = {"author": "test", "version": "1.0"}

        registry.register_filter("meta_filter", filter_instance, metadata)

        entry = registry.get_filter("meta_filter")
        assert entry.metadata == metadata

    def test_register_filter_overwrite(self, registry):
        """测试覆盖已存在的过滤器"""
        filter1 = MockFilter(should_pass=True)
        filter2 = MockFilter(should_pass=False)

        registry.register_filter("dup_filter", filter1)
        registry.register_filter("dup_filter", filter2)

        entry = registry.get_filter("dup_filter")
        assert entry.filter_instance is filter2

    def test_get_nonexistent_filter(self, registry):
        """测试获取不存在的过滤器"""
        assert registry.get_filter("nonexistent") is None
        assert registry.get_filter_instance("nonexistent") is None


# =============================================================================
# 函数过滤器测试
# =============================================================================


class TestFunctionFilters:
    """测试函数过滤器功能"""

    def test_add_filter_to_function(self, registry):
        """测试为函数添加过滤器"""
        FilterRegistry.set_current_plugin_name("test_plugin")

        filter1 = MockFilter()

        def handler(event):
            pass

        result = registry.add_filter_to_function(handler, filter1)

        assert result is handler
        assert hasattr(handler, "__filters__")
        assert filter1 in handler.__filters__

        # 清理
        FilterRegistry.set_current_plugin_name("")

    def test_add_multiple_filters(self, registry):
        """测试添加多个过滤器"""
        FilterRegistry.set_current_plugin_name("test_plugin")

        filter1 = MockFilter()
        filter2 = MockFilter()
        filter3 = MockFilter()

        def handler(event):
            pass

        registry.add_filter_to_function(handler, filter1, filter2, filter3)

        assert len(handler.__filters__) == 3

        # 清理
        FilterRegistry.set_current_plugin_name("")

    def test_add_filter_by_name(self, registry):
        """测试按名称添加过滤器"""
        FilterRegistry.set_current_plugin_name("test_plugin")

        filter_instance = MockFilter()
        registry.register_filter("named_filter", filter_instance)

        def handler(event):
            pass

        registry.add_filter_to_function(handler, "named_filter")

        assert filter_instance in handler.__filters__

        # 清理
        FilterRegistry.set_current_plugin_name("")

    def test_filters_decorator(self, registry):
        """测试 filters 装饰器"""
        FilterRegistry.set_current_plugin_name("test_plugin")

        filter1 = MockFilter()

        @registry.filters(filter1)
        def handler(event):
            pass

        assert hasattr(handler, "__filters__")
        assert filter1 in handler.__filters__

        # 清理
        FilterRegistry.set_current_plugin_name("")


# =============================================================================
# 插件撤销测试
# =============================================================================


class TestPluginRevocation:
    """测试插件撤销"""

    def test_revoke_plugin(self, registry):
        """测试撤销插件的过滤器函数"""
        FilterRegistry.set_current_plugin_name("plugin_a")

        def handler_a(event):
            pass

        registry.add_filter_to_function(handler_a, MockFilter())

        FilterRegistry.set_current_plugin_name("plugin_b")

        def handler_b(event):
            pass

        registry.add_filter_to_function(handler_b, MockFilter())

        assert len(registry._function_filters) == 2

        registry.revoke_plugin("plugin_a")

        assert len(registry._function_filters) == 1
        assert "plugin_b::handler_b" in registry._function_filters

        # 清理
        FilterRegistry.set_current_plugin_name("")


# =============================================================================
# 清理测试
# =============================================================================


class TestClear:
    """测试清理功能"""

    def test_clear_all(self, registry):
        """测试清理所有"""
        FilterRegistry.set_current_plugin_name("test")

        registry.register_filter("filter1", MockFilter())

        def handler(event):
            pass

        registry.add_filter_to_function(handler, MockFilter())

        registry.clear()

        assert len(registry._filters) == 0
        assert len(registry._function_filters) == 0

        # 清理
        FilterRegistry.set_current_plugin_name("")
