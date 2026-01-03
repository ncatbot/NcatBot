"""命令系统异常处理端到端测试

测试：
- 优先级 1：用户可见错误
  - 命令系统异常
  - 参数验证错误
  - 类型转换错误
"""

import pytest
import pytest_asyncio
import logging
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite


FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
ERROR_PLUGIN_DIR = PLUGINS_DIR / "error_test_plugin"


@pytest_asyncio.fixture
async def error_suite():
    """创建异常测试套件"""
    suite = E2ETestSuite()
    await suite.setup()
    suite.index_plugin(str(ERROR_PLUGIN_DIR))
    await suite.register_plugin("error_test_plugin")

    yield suite

    await suite.teardown()


class TestCommandExecutionErrors:
    """命令执行异常测试

    确保命令执行过程中的异常被正确记录到日志。
    """

    @pytest.mark.asyncio
    async def test_command_crash_logged(self, error_suite, caplog):
        """测试命令崩溃时异常被记录到日志

        当命令执行时抛出异常，应该：
        1. 异常被记录到日志
        2. 日志中包含异常信息和堆栈
        """
        with caplog.at_level(logging.ERROR):
            await error_suite.inject_private_message("/crash")

        # 验证错误被记录
        assert any(
            "命令执行时发生了预期的错误" in record.message
            for record in caplog.records
            if record.levelno >= logging.ERROR
        ), f"日志中应包含异常信息，实际日志: {[r.message for r in caplog.records]}"

    @pytest.mark.asyncio
    async def test_division_by_zero_logged(self, error_suite, caplog):
        """测试除零异常被记录到日志"""
        with caplog.at_level(logging.ERROR):
            await error_suite.inject_private_message("/divide 10 0")

        # 验证错误被记录
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_records) > 0, "除零异常应该被记录到日志"

    @pytest.mark.asyncio
    async def test_value_error_logged(self, error_suite, caplog):
        """测试 ValueError 被记录到日志"""
        with caplog.at_level(logging.ERROR):
            await error_suite.inject_private_message("/valueerror abc")

        # 验证错误被记录
        assert any(
            "期望数字字符串" in record.message or "ValueError" in record.message
            for record in caplog.records
            if record.levelno >= logging.ERROR
        ), "日志中应包含 ValueError 信息"


class TestArgumentBindingErrors:
    """参数绑定异常测试

    这些测试验证命令系统在遇到参数问题时的行为。
    当前实现中，参数不足时命令可能：
    1. 不匹配命令
    2. 绑定失败并记录日志
    3. 执行时抛出异常
    """

    @pytest.mark.asyncio
    async def test_missing_required_argument_no_crash(self, error_suite, caplog):
        """测试缺少必需参数时系统不会崩溃

        验证系统能优雅地处理缺少参数的情况。
        """
        with caplog.at_level(logging.DEBUG):
            # 调用 /normal 但不提供必需的 text 参数
            await error_suite.inject_private_message("/normal")

        # 系统不应该崩溃 - 这个测试能执行到这里就说明系统正常处理了

    @pytest.mark.asyncio
    async def test_too_few_arguments_no_crash(self, error_suite, caplog):
        """测试参数不足时系统不会崩溃"""
        with caplog.at_level(logging.DEBUG):
            # /multi 需要 3 个参数，只提供 1 个
            await error_suite.inject_private_message("/multi only_one")

        # 系统不应该崩溃


class TestTypeConversionErrors:
    """类型转换异常测试

    验证类型转换失败时系统的行为。
    """

    @pytest.mark.asyncio
    async def test_invalid_int_conversion_no_crash(self, error_suite, caplog):
        """测试无效整数转换时系统不会崩溃

        传入无法转换为整数的字符串，验证系统能优雅处理。
        """
        with caplog.at_level(logging.DEBUG):
            # /number 需要 int 类型参数
            await error_suite.inject_private_message("/number not_a_number")

        # 系统不应该崩溃
        # 即使没有特定日志，测试能运行到这里就说明系统正常处理了

    @pytest.mark.asyncio
    async def test_valid_int_conversion_works(self, error_suite):
        """测试有效整数转换正常工作"""
        await error_suite.inject_private_message("/number 42")
        error_suite.assert_reply_sent("数字: 42")


class TestNormalCommandExecution:
    """正常命令执行测试（对照组）

    确保正常情况下命令能正确执行。
    """

    @pytest.mark.asyncio
    async def test_normal_command_works(self, error_suite):
        """测试正常命令执行"""
        await error_suite.inject_private_message("/normal hello")
        error_suite.assert_reply_sent("正常: hello")

    @pytest.mark.asyncio
    async def test_multi_params_works(self, error_suite):
        """测试多参数命令执行"""
        await error_suite.inject_private_message("/multi a b c")
        error_suite.assert_reply_sent("参数: a, b, c")

    @pytest.mark.asyncio
    async def test_divide_works(self, error_suite):
        """测试正常除法运算"""
        await error_suite.inject_private_message("/divide 10 2")
        error_suite.assert_reply_sent("结果: 5.0")
