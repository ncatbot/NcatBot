"""FunctionExecutor 单元测试

测试函数执行器的所有功能：
- 函数执行（同步/异步）
- 过滤器验证
- 插件上下文注入
- 缓存管理
"""

import pytest
from unittest.mock import Mock

from ncatbot.core.service.builtin.unified_registry.executor import FunctionExecutor
from ncatbot.core.service.builtin.unified_registry.filter_system.validator import (
    FilterValidator,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def executor():
    """创建基本执行器"""
    return FunctionExecutor()


@pytest.fixture
def mock_event():
    """创建模拟事件"""
    event = Mock()
    event.message = Mock()
    event.user_id = 12345
    event.group_id = 67890
    return event


@pytest.fixture
def mock_plugin_loader():
    """创建模拟插件加载器"""
    loader = Mock()
    loader.plugins = {}
    return loader


# =============================================================================
# FunctionExecutor 初始化测试
# =============================================================================


class TestFunctionExecutorInit:
    """测试执行器初始化"""

    def test_default_init(self):
        """测试默认初始化"""
        executor = FunctionExecutor()

        assert executor._filter_validator is not None
        assert isinstance(executor._filter_validator, FilterValidator)
        assert executor._func_plugin_map == {}
        assert executor._plugin_loader is None

    def test_custom_filter_validator(self):
        """测试自定义过滤器验证器"""
        custom_validator = Mock(spec=FilterValidator)
        executor = FunctionExecutor(filter_validator=custom_validator)

        assert executor._filter_validator is custom_validator

    def test_set_plugin_loader(self, executor, mock_plugin_loader):
        """测试设置插件加载器"""
        executor.set_plugin_loader(mock_plugin_loader)

        assert executor._plugin_loader is mock_plugin_loader


# =============================================================================
# 插件查找测试
# =============================================================================


class TestPluginLookup:
    """测试插件查找功能"""

    def test_plugins_property_without_loader(self, executor):
        """测试无加载器时的插件列表"""
        assert executor.plugins == []

    def test_plugins_property_with_loader(self, executor, mock_plugin_loader):
        """测试有加载器时的插件列表"""
        plugin1 = Mock()
        plugin2 = Mock()
        mock_plugin_loader.plugins = {"p1": plugin1, "p2": plugin2}

        executor.set_plugin_loader(mock_plugin_loader)

        assert len(executor.plugins) == 2
        assert plugin1 in executor.plugins
        assert plugin2 in executor.plugins

    def test_find_plugin_for_function_not_found(self, executor):
        """测试查找不存在的插件函数"""

        def standalone_func():
            pass

        result = executor.find_plugin_for_function(standalone_func)

        assert result is None

    def test_find_plugin_for_function_cached(self, executor):
        """测试插件函数缓存"""

        def some_func():
            pass

        mock_plugin = Mock()
        executor._func_plugin_map[some_func] = mock_plugin

        result = executor.find_plugin_for_function(some_func)

        assert result is mock_plugin

    def test_find_plugin_for_function_in_plugin_class(
        self, executor, mock_plugin_loader
    ):
        """测试在插件类中查找函数"""

        class TestPlugin:
            def handler(self):
                pass

        plugin_instance = TestPlugin()
        mock_plugin_loader.plugins = {"test": plugin_instance}
        executor.set_plugin_loader(mock_plugin_loader)

        result = executor.find_plugin_for_function(TestPlugin.handler)

        assert result is plugin_instance
        # 验证缓存
        assert TestPlugin.handler in executor._func_plugin_map


# =============================================================================
# 函数执行测试
# =============================================================================


class TestFunctionExecution:
    """测试函数执行"""

    @pytest.mark.asyncio
    async def test_execute_async_function(self, executor, mock_event):
        """测试执行异步函数"""
        result_holder = []

        async def async_handler(event):
            result_holder.append(event)
            return "success"

        result = await executor.execute(async_handler, mock_event)

        assert result == "success"
        assert len(result_holder) == 1
        assert result_holder[0] is mock_event

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, executor, mock_event):
        """测试执行同步函数"""
        result_holder = []

        def sync_handler(event):
            result_holder.append(event)
            return "sync_success"

        result = await executor.execute(sync_handler, mock_event)

        assert result == "sync_success"
        assert len(result_holder) == 1

    @pytest.mark.asyncio
    async def test_execute_with_args(self, executor, mock_event):
        """测试带参数执行"""

        async def handler_with_args(event, arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = await executor.execute(
            handler_with_args, mock_event, "a", "b", kwarg1="c"
        )

        assert result == "a-b-c"

    @pytest.mark.asyncio
    async def test_execute_with_plugin_context(
        self, executor, mock_event, mock_plugin_loader
    ):
        """测试带插件上下文执行"""

        class TestPlugin:
            def handler(self, event):
                return f"plugin:{self.__class__.__name__}"

        plugin_instance = TestPlugin()
        mock_plugin_loader.plugins = {"test": plugin_instance}
        executor.set_plugin_loader(mock_plugin_loader)

        # 手动添加到缓存（模拟已注册的函数）
        executor._func_plugin_map[TestPlugin.handler] = plugin_instance

        result = await executor.execute(TestPlugin.handler, mock_event)

        assert result == "plugin:TestPlugin"

    @pytest.mark.asyncio
    async def test_execute_with_filter_validation_pass(self, executor, mock_event):
        """测试过滤器验证通过"""
        mock_validator = Mock(spec=FilterValidator)
        mock_validator.validate_filters.return_value = True
        executor._filter_validator = mock_validator

        async def filtered_handler(event):
            return "passed"

        filtered_handler.__filters__ = [Mock()]

        result = await executor.execute(filtered_handler, mock_event)

        assert result == "passed"
        mock_validator.validate_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_filter_validation_fail(self, executor, mock_event):
        """测试过滤器验证失败"""
        mock_validator = Mock(spec=FilterValidator)
        mock_validator.validate_filters.return_value = False
        executor._filter_validator = mock_validator

        async def filtered_handler(event):
            return "should not reach"

        filtered_handler.__filters__ = [Mock()]

        result = await executor.execute(filtered_handler, mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, executor, mock_event):
        """测试异常处理"""

        async def failing_handler(event):
            raise ValueError("Test error")

        result = await executor.execute(failing_handler, mock_event)

        assert result is False


# =============================================================================
# 缓存管理测试
# =============================================================================


class TestCacheManagement:
    """测试缓存管理"""

    def test_clear_cache(self, executor):
        """测试清理缓存"""

        def func1():
            pass

        def func2():
            pass

        executor._func_plugin_map[func1] = Mock()
        executor._func_plugin_map[func2] = Mock()

        assert len(executor._func_plugin_map) == 2

        executor.clear_cache()

        assert len(executor._func_plugin_map) == 0
