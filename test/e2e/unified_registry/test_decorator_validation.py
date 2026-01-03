"""装饰器验证 E2E 测试

测试 decorator_validator.py 的功能，包括：
- 选项名格式验证
- 选项名冲突检测
- 参数名冲突检测
- 选项组验证
"""

import pytest
import sys
from pathlib import Path

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.analyzer.decorator_validator import (
    DecoratorValidator,
)
from ncatbot.core.service.builtin.unified_registry.command_system.utils import (
    CommandRegistrationError,
    OptionSpec,
    ParameterSpec,
    OptionGroupSpec,
)

# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
DECORATOR_PLUGIN_DIR = PLUGINS_DIR / "decorator_test_plugin"


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name
        for name in list(sys.modules.keys())
        if "decorator_test_plugin" in name or "ncatbot_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


class TestDecoratorValidation:
    """装饰器验证测试"""

    @pytest.mark.asyncio
    async def test_valid_plugin_loads_successfully(self):
        """测试有效插件加载成功"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(DECORATOR_PLUGIN_DIR))
            await suite.register_plugin("decorator_test_plugin")

            # 验证命令已注册
            all_commands = command_registry.get_all_commands()
            assert any("opt_short" in path for path in all_commands.keys())
            assert any("opt_long" in path for path in all_commands.keys())
            assert any("opt_both" in path for path in all_commands.keys())
            assert any("complex" in path for path in all_commands.keys())

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_command_with_options_works(self):
        """测试带选项的命令能正常工作"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(DECORATOR_PLUGIN_DIR))
            await suite.register_plugin("decorator_test_plugin")

            # 测试短选项
            await suite.inject_group_message("/opt_short -v")
            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            assert "verbose=True" in str(calls[-1].get("message", ""))

            suite.clear_call_history()

            # 测试长选项
            await suite.inject_group_message("/opt_long --verbose")
            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            assert "verbose=True" in str(calls[-1].get("message", ""))

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_complex_command_works(self):
        """测试复杂命令组合"""
        _cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(DECORATOR_PLUGIN_DIR))
            await suite.register_plugin("decorator_test_plugin")

            # option_group 创建的是 --fast/--normal/--safe 选项，而非 --mode=xxx
            await suite.inject_group_message(
                "/complex test.txt --output=result.txt --fast -v -f"
            )
            suite.assert_reply_sent()
            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "input=test.txt" in msg
            assert "mode=fast" in msg

        _cleanup_modules()


class TestDecoratorValidatorUnit:
    """装饰器验证器单元测试"""

    def test_short_option_validation(self):
        """测试短选项格式验证"""

        def valid_func():
            pass

        valid_func.__command_options__ = [
            OptionSpec(short_name="v", long_name=None),
            OptionSpec(short_name="a", long_name=None),
        ]
        valid_func.__command_params__ = []
        valid_func.__command_option_groups__ = []

        # 不应抛出异常
        DecoratorValidator.validate_function_decorators(valid_func)

    def test_short_option_conflict_detection(self):
        """测试短选项冲突检测"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = [
            OptionSpec(short_name="v", long_name=None),
            OptionSpec(short_name="v", long_name=None),  # 重复
        ]
        conflict_func.__command_params__ = []
        conflict_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_long_option_conflict_detection(self):
        """测试长选项冲突检测"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = [
            OptionSpec(short_name=None, long_name="verbose"),
            OptionSpec(short_name=None, long_name="verbose"),  # 重复
        ]
        conflict_func.__command_params__ = []
        conflict_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_invalid_short_option_format(self):
        """测试无效短选项格式"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = [
            OptionSpec(short_name="ab", long_name=None),  # 短选项应该是单字符
        ]
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)

    def test_invalid_long_option_format(self):
        """测试无效长选项格式"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = [
            OptionSpec(short_name=None, long_name="a"),  # 长选项至少2个字符
        ]
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)

    def test_empty_option_error(self):
        """测试空选项错误"""

        def empty_func():
            pass

        empty_func.__command_options__ = [
            OptionSpec(short_name=None, long_name=None),  # 必须至少有一个
        ]
        empty_func.__command_params__ = []
        empty_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(empty_func)

    def test_param_name_conflict(self):
        """测试参数名冲突"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = []
        conflict_func.__command_params__ = [
            ParameterSpec(name="input"),
            ParameterSpec(name="input"),  # 重复
        ]
        conflict_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_param_option_conflict(self):
        """测试参数名与选项名冲突"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = [
            OptionSpec(short_name="v", long_name="verbose"),
        ]
        conflict_func.__command_params__ = [
            ParameterSpec(name="verbose"),  # 与选项名冲突
        ]
        conflict_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_option_group_validation(self):
        """测试选项组验证"""

        def valid_func():
            pass

        valid_func.__command_options__ = []
        valid_func.__command_params__ = []
        valid_func.__command_option_groups__ = [
            OptionGroupSpec(
                name="format", choices=["json", "xml", "yaml"], default="json"
            ),
        ]

        # 不应抛出异常
        DecoratorValidator.validate_function_decorators(valid_func)

    def test_option_group_empty_choices(self):
        """测试选项组空选项列表"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = []
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = [
            OptionGroupSpec(name="format", choices=[], default=None),
        ]

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)

    def test_option_group_invalid_default(self):
        """测试选项组无效默认值"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = []
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = [
            OptionGroupSpec(
                name="format",
                choices=["json", "xml"],
                default="yaml",  # 不在 choices 中
            ),
        ]

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)

    def test_option_group_name_conflict(self):
        """测试选项组名冲突"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = []
        conflict_func.__command_params__ = []
        conflict_func.__command_option_groups__ = [
            OptionGroupSpec(name="format", choices=["a", "b"], default="a"),
            OptionGroupSpec(name="format", choices=["c", "d"], default="c"),  # 重复
        ]

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_option_group_choice_conflict(self):
        """测试选项组值与短选项冲突"""

        def conflict_func():
            pass

        conflict_func.__command_options__ = [
            OptionSpec(short_name="a", long_name=None),
        ]
        conflict_func.__command_params__ = []
        conflict_func.__command_option_groups__ = [
            OptionGroupSpec(
                name="mode", choices=["a", "b", "c"], default="b"
            ),  # 'a' 与短选项冲突
        ]

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(conflict_func)

    def test_long_option_with_prefix(self):
        """测试长选项名带 -- 前缀（应该报错）"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = [
            OptionSpec(short_name=None, long_name="--verbose"),  # 不应包含 --
        ]
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = []

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)

    def test_duplicate_group_choices(self):
        """测试选项组重复选项"""

        def invalid_func():
            pass

        invalid_func.__command_options__ = []
        invalid_func.__command_params__ = []
        invalid_func.__command_option_groups__ = [
            OptionGroupSpec(
                name="format", choices=["json", "json", "xml"], default="json"
            ),  # 重复
        ]

        with pytest.raises(CommandRegistrationError):
            DecoratorValidator.validate_function_decorators(invalid_func)
