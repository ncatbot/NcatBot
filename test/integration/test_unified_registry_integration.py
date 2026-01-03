"""UnifiedRegistry 集成测试

测试统一注册模块的完整工作流：
- 命令注册和执行流程
- 过滤器注册和验证流程
- 事件处理器注册和分发流程
- 插件加载/卸载流程
"""

import pytest
from unittest.mock import Mock

from ncatbot.core.service.builtin.unified_registry import (
    UnifiedRegistryService,
    filter_registry,
)
from ncatbot.core.service.builtin.unified_registry.executor import FunctionExecutor
from ncatbot.core.service.builtin.unified_registry.command_runner import CommandRunner
from ncatbot.core.service.builtin.unified_registry.filter_system.event_registry import (
    EventRegistry,
)
from ncatbot.core.service.builtin.unified_registry.filter_system.base import BaseFilter
from ncatbot.core.service.builtin.unified_registry.command_system.lexer import (
    StringTokenizer,
    CommandParser,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def clean_registries():
    """清理所有注册表"""
    # 清理前
    filter_registry.clear()
    # command_registry 没有 clear 方法，跳过

    yield

    # 清理后
    filter_registry.clear()
    EventRegistry.set_current_plugin_name("")


# =============================================================================
# 词法分析集成测试
# =============================================================================


class TestLexerIntegration:
    """词法分析器集成测试"""

    def test_tokenizer_to_parser_flow(self):
        """测试分词器到解析器的完整流程"""
        command = '/test --verbose -n=value "quoted arg" positional'

        # 分词
        tokenizer = StringTokenizer(command)
        tokens = tokenizer.tokenize()

        # 解析
        parser = CommandParser()
        parsed = parser.parse(tokens)

        # 验证结果
        assert "verbose" in parsed.options
        assert parsed.named_params.get("n") == "value"
        assert len(parsed.elements) == 3  # /test, "quoted arg", positional

    def test_complex_command_parsing(self):
        """测试复杂命令解析"""
        commands = [
            "/help --format=json",
            '!ban user123 --reason="spam" -s',
            '/config set key "value with spaces"',
        ]

        for cmd in commands:
            tokenizer = StringTokenizer(cmd)
            tokens = tokenizer.tokenize()
            parser = CommandParser()
            parsed = parser.parse(tokens)

            # 基本验证
            assert parsed is not None
            assert len(parsed.elements) > 0


# =============================================================================
# 执行器集成测试
# =============================================================================


class TestExecutorIntegration:
    """执行器集成测试"""

    @pytest.mark.asyncio
    async def test_executor_with_filter_chain(self):
        """测试执行器与过滤器链"""
        executor = FunctionExecutor()

        class PassFilter(BaseFilter):
            def check(self, event) -> bool:
                return True

        class FailFilter(BaseFilter):
            def check(self, event) -> bool:
                return False

        # 测试通过的过滤器
        async def passing_handler(event):
            return "passed"

        passing_handler.__filters__ = [PassFilter()]

        mock_event = Mock()
        result = await executor.execute(passing_handler, mock_event)

        assert result == "passed"

        # 测试失败的过滤器
        async def failing_handler(event):
            return "should not reach"

        failing_handler.__filters__ = [FailFilter()]

        result = await executor.execute(failing_handler, mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_executor_sync_async_mix(self):
        """测试执行器处理同步和异步函数"""
        executor = FunctionExecutor()
        results = []

        async def async_handler(event):
            results.append("async")
            return "async_result"

        def sync_handler(event):
            results.append("sync")
            return "sync_result"

        mock_event = Mock()

        await executor.execute(async_handler, mock_event)
        await executor.execute(sync_handler, mock_event)

        assert results == ["async", "sync"]


# =============================================================================
# 命令运行器集成测试
# =============================================================================


class TestCommandRunnerIntegration:
    """命令运行器集成测试"""

    def test_runner_initialization_chain(self):
        """测试运行器初始化链"""
        executor = FunctionExecutor()
        runner = CommandRunner(
            prefixes=["/", "!"],
            executor=executor,
        )

        # 验证组件正确初始化
        assert runner.preprocessor is not None
        assert runner.resolver is not None
        assert runner._binder is not None

        # 验证配置传递
        assert runner.preprocessor.prefixes == ["/", "!"]

    @pytest.mark.asyncio
    async def test_runner_no_match_flow(self):
        """测试无匹配命令的流程"""
        from ncatbot.core.event.message_segments.primitives import PlainText

        executor = FunctionExecutor()
        runner = CommandRunner(
            prefixes=["/"],
            executor=executor,
        )

        # 创建消息事件
        event = Mock()
        event.message = Mock()
        event.message.message = [PlainText(text="/unknown_command")]

        result = await runner.run(event)

        # 没有注册命令，应该返回 False
        assert result is False


# =============================================================================
# 事件注册表集成测试
# =============================================================================


class TestEventRegistryIntegration:
    """事件注册表集成测试"""

    def test_multi_plugin_registration(self, clean_registries):
        """测试多插件注册"""
        registry = EventRegistry()

        # 插件 A 注册
        EventRegistry.set_current_plugin_name("plugin_a")

        @registry.notice_handler
        def notice_a(event):
            return "a"

        @registry.request_handler
        def request_a(event):
            return "a"

        # 插件 B 注册
        EventRegistry.set_current_plugin_name("plugin_b")

        @registry.notice_handler
        def notice_b(event):
            return "b"

        # 验证注册
        assert len(registry.notice_handlers) == 2
        assert len(registry.request_handlers) == 1

        # 卸载插件 A
        registry.revoke_plugin("plugin_a")

        assert len(registry.notice_handlers) == 1
        assert len(registry.request_handlers) == 0

        # 清理
        registry.clear()


# =============================================================================
# 服务完整流程测试
# =============================================================================


class TestServiceFullFlow:
    """服务完整流程测试"""

    @pytest.mark.asyncio
    async def test_service_lifecycle(self, clean_registries):
        """测试服务完整生命周期"""
        service = UnifiedRegistryService()

        # 1. 加载服务
        await service.on_load()

        # 2. 注册处理器
        handler_called = []

        def notice_handler(event):
            handler_called.append("notice")

        service.register_notice_handler(notice_handler)

        # 3. 初始化
        service.initialize_if_needed()

        assert service._initialized is True

        # 4. 关闭服务
        await service.on_close()

        assert service._initialized is False

    def test_service_clear_and_reinitialize(self, clean_registries):
        """测试服务清理和重新初始化"""
        from ncatbot.core.service.builtin.unified_registry.executor import (
            FunctionExecutor,
        )

        service = UnifiedRegistryService()
        service._executor = FunctionExecutor()  # 初始化 executor

        # 首次初始化
        service.initialize_if_needed()

        # 清理
        service.clear()
        assert service._initialized is False

        # 重新初始化
        service.initialize_if_needed()
        assert service._initialized is True


# =============================================================================
# 错误处理集成测试
# =============================================================================


class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    @pytest.mark.asyncio
    async def test_executor_handles_handler_exception(self):
        """测试执行器处理处理器异常"""
        executor = FunctionExecutor()

        async def failing_handler(event):
            raise RuntimeError("Handler error")

        mock_event = Mock()

        # 应该捕获异常并返回 False
        result = await executor.execute(failing_handler, mock_event)

        assert result is False

    def test_service_prefix_conflict_detection(self, clean_registries):
        """测试服务前缀冲突检测"""
        service = UnifiedRegistryService()

        # 模拟冲突的前缀
        service.prefixes = ["/", "/cmd"]

        with pytest.raises(ValueError, match="prefix conflict"):
            service._check_prefix_conflicts()


# =============================================================================
# 性能相关测试
# =============================================================================


class TestPerformance:
    """性能相关测试"""

    def test_tokenizer_performance(self):
        """测试分词器性能"""
        import time

        command = '/test --verbose -n=value "quoted arg" positional ' * 10

        start = time.time()
        for _ in range(1000):
            tokenizer = StringTokenizer(command)
            tokenizer.tokenize()
        elapsed = time.time() - start

        # 1000 次分词应该在合理时间内完成
        assert elapsed < 5.0  # 5 秒上限

    def test_executor_cache_effectiveness(self):
        """测试执行器缓存有效性"""
        executor = FunctionExecutor()

        def handler():
            pass

        mock_plugin = Mock()

        # 首次查找
        executor._func_plugin_map[handler] = mock_plugin

        # 多次查找应该使用缓存
        for _ in range(100):
            result = executor.find_plugin_for_function(handler)
            assert result is mock_plugin
