"""CommandRunner 单元测试

测试命令运行器的所有功能：
- 初始化
- 命令预处理
- 解析器访问
- 资源清理
"""

import pytest
from unittest.mock import Mock, AsyncMock

from ncatbot.core.service.builtin.unified_registry.command_runner import CommandRunner
from ncatbot.core.service.builtin.unified_registry.executor import FunctionExecutor
from ncatbot.core.service.builtin.unified_registry.trigger.preprocessor import (
    MessagePreprocessor,
)
from ncatbot.core.service.builtin.unified_registry.trigger.resolver import (
    CommandResolver,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def mock_executor():
    """创建模拟执行器"""
    executor = Mock(spec=FunctionExecutor)
    executor.execute = AsyncMock(return_value=True)
    return executor


@pytest.fixture
def runner(mock_executor):
    """创建命令运行器"""
    return CommandRunner(
        prefixes=["/", "!"],
        executor=mock_executor,
        event_bus=None,
    )


@pytest.fixture
def mock_message_event():
    """创建模拟消息事件"""
    from ncatbot.core.event.message_segments.primitives import PlainText

    event = Mock()
    event.message = Mock()

    # 创建 PlainText 消息段
    plain_text = PlainText(text="/test arg1 arg2")
    event.message.message = [plain_text]

    return event


# =============================================================================
# 初始化测试
# =============================================================================


class TestCommandRunnerInit:
    """测试命令运行器初始化"""

    def test_default_init(self, mock_executor):
        """测试默认初始化"""
        runner = CommandRunner(
            prefixes=["/"],
            executor=mock_executor,
        )

        assert runner._executor is mock_executor
        assert runner._event_bus is None
        assert runner._binder is not None
        assert runner._preprocessor is not None
        assert runner._resolver is not None

    def test_init_with_event_bus(self, mock_executor):
        """测试带事件总线初始化"""
        mock_bus = Mock()

        runner = CommandRunner(
            prefixes=["/"],
            executor=mock_executor,
            event_bus=mock_bus,
        )

        assert runner._event_bus is mock_bus

    def test_init_with_multiple_prefixes(self, mock_executor):
        """测试多前缀初始化"""
        runner = CommandRunner(
            prefixes=["/", "!", "#"],
            executor=mock_executor,
        )

        assert runner._preprocessor.prefixes == ["/", "!", "#"]


# =============================================================================
# 属性访问测试
# =============================================================================


class TestProperties:
    """测试属性访问"""

    def test_preprocessor_property(self, runner):
        """测试预处理器属性"""
        assert isinstance(runner.preprocessor, MessagePreprocessor)

    def test_resolver_property(self, runner):
        """测试解析器属性"""
        assert isinstance(runner.resolver, CommandResolver)

    def test_set_event_bus(self, runner):
        """测试设置事件总线"""
        mock_bus = Mock()

        runner.set_event_bus(mock_bus)

        assert runner._event_bus is mock_bus


# =============================================================================
# 命令运行测试
# =============================================================================


class TestCommandExecution:
    """测试命令执行"""

    @pytest.mark.asyncio
    async def test_run_returns_false_on_precheck_fail(self, runner):
        """测试预检查失败返回 False"""
        event = Mock()
        event.message = Mock()
        event.message.message = []  # 空消息

        result = await runner.run(event)

        assert result is False

    @pytest.mark.asyncio
    async def test_run_returns_false_no_command_hit(self, runner, mock_message_event):
        """测试无命令匹配返回 False"""
        # 没有注册任何命令，所以不会匹配
        result = await runner.run(mock_message_event)

        assert result is False


# =============================================================================
# 清理测试
# =============================================================================


class TestClear:
    """测试资源清理"""

    def test_clear_clears_resolver(self, runner):
        """测试清理解析器"""
        # 先构建一些索引
        runner._resolver._index = {("test",): Mock()}

        runner.clear()

        assert runner._resolver._index == {}


# =============================================================================
# 边界情况测试
# =============================================================================


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_prefixes(self, mock_executor):
        """测试空前缀列表"""
        runner = CommandRunner(
            prefixes=[],
            executor=mock_executor,
        )

        assert runner._preprocessor.prefixes == []

    @pytest.mark.asyncio
    async def test_run_with_non_text_first_segment(self, runner):
        """测试首段非文本消息"""
        event = Mock()
        event.message = Mock()

        # 首段是图片而非文本
        image_segment = Mock()
        image_segment.__class__.__name__ = "Image"
        event.message.message = [image_segment]

        result = await runner.run(event)

        assert result is False
