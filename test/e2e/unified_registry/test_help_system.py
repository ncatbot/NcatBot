"""帮助系统 E2E 测试

测试 help_system.py 的功能，包括：
- 命令帮助文档生成
- 命令组帮助文档生成
- 命令列表生成
- 错误信息格式化
"""

import sys
from pathlib import Path

import pytest

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.core.service.builtin.unified_registry.command_system.registry.help_system import (
    HelpGenerator,
    format_error_with_help,
)

# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
HELP_PLUGIN_DIR = PLUGINS_DIR / "help_test_plugin"


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name
        for name in list(sys.modules.keys())
        if "help_test_plugin" in name or "ncatbot_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


class TestHelpSystemE2E:
    """帮助系统 E2E 测试 - 使用真实插件"""

    @pytest.mark.asyncio
    async def test_plugin_loads_and_basic_help(self):
        """测试插件加载和基础帮助功能（综合测试）

        测试内容：
        - 插件加载成功
        - 基础命令的帮助生成
        - 无描述命令的帮助生成
        """
        _cleanup_modules()

        from ncatbot.core.service.builtin.unified_registry import command_registry

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(HELP_PLUGIN_DIR))
            await suite.register_plugin("help_test_plugin")

            # 1. 验证命令已注册
            all_commands = command_registry.get_all_commands()
            assert any("help_basic" in path for path in all_commands.keys())
            assert any("help_params" in path for path in all_commands.keys())
            assert any("help_options" in path for path in all_commands.keys())
            assert any("help_complex" in path for path in all_commands.keys())

            # 2. 测试基础命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_basic" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            generator = HelpGenerator()
            help_text = generator.generate_command_help(cmd_spec)

            assert "📋 命令: help_basic" in help_text
            assert "基础命令描述" in help_text
            assert "💡 用法:" in help_text

            # 3. 测试无描述命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_no_desc" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "📋 命令: help_no_desc" in help_text
            assert "📝 描述:" not in help_text

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_help_with_aliases_and_params(self):
        """测试带别名和参数的命令帮助（综合测试）

        测试内容：
        - 带别名命令的帮助生成
        - 带参数命令的帮助生成
        - 带选择值参数的帮助生成
        """
        _cleanup_modules()

        from ncatbot.core.service.builtin.unified_registry import command_registry

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(HELP_PLUGIN_DIR))
            await suite.register_plugin("help_test_plugin")

            all_commands = command_registry.get_all_commands()
            generator = HelpGenerator()

            # 1. 测试带别名命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_alias" in path and spec.name == "help_alias":
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "📋 命令: help_alias" in help_text
            assert "📋 别名:" in help_text
            assert "ha" in help_text
            assert "halias" in help_text

            # 2. 测试带参数命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_params" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "🏷️ 参数:" in help_text
            assert "--input" in help_text
            assert "输入文件路径" in help_text
            assert "--output" in help_text
            assert "(可选)" in help_text
            assert "默认值: out.txt" in help_text

            # 3. 测试带选择值参数的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_param_choices" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "可选值: json, xml, csv" in help_text

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_help_with_options_and_groups(self):
        """测试带选项和选项组的命令帮助（综合测试）

        测试内容：
        - 带选项命令的帮助生成
        - 带选项组命令的帮助生成
        """
        _cleanup_modules()

        from ncatbot.core.service.builtin.unified_registry import command_registry

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(HELP_PLUGIN_DIR))
            await suite.register_plugin("help_test_plugin")

            all_commands = command_registry.get_all_commands()
            generator = HelpGenerator()

            # 1. 测试带选项命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_options" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "⚙️ 选项:" in help_text
            assert "-v, --verbose" in help_text
            assert "详细模式" in help_text
            assert "-a" in help_text
            assert "显示全部" in help_text
            assert "--force" in help_text
            assert "强制执行" in help_text

            # 2. 测试带选项组命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_groups" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            assert "📦 选项组:" in help_text
            assert "mode" in help_text
            assert "处理模式" in help_text
            assert "--fast" in help_text
            assert "--normal (默认)" in help_text
            assert "--safe" in help_text

        _cleanup_modules()

    @pytest.mark.asyncio
    async def test_complex_command_and_utilities(self):
        """测试复杂命令和工具函数（综合测试）

        测试内容：
        - 复杂组合命令的帮助生成
        - 从注册表生成命令列表
        - 使用注册命令的错误格式化
        """
        _cleanup_modules()

        from ncatbot.core.service.builtin.unified_registry import command_registry

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(HELP_PLUGIN_DIR))
            await suite.register_plugin("help_test_plugin")

            all_commands = command_registry.get_all_commands()
            generator = HelpGenerator()

            # 1. 测试复杂组合命令的帮助生成
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_complex" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            help_text = generator.generate_command_help(cmd_spec)

            # 验证各部分都存在
            assert "📋 命令: help_complex" in help_text
            assert "复杂组合命令，测试完整帮助生成" in help_text
            assert "🏷️ 参数:" in help_text
            assert "--source" in help_text
            assert "--dest" in help_text
            assert "⚙️ 选项:" in help_text
            assert "-v, --verbose" in help_text
            assert "-f, --force" in help_text
            assert "📦 选项组:" in help_text
            assert "compression" in help_text
            assert "--gzip (默认)" in help_text
            assert "🌰 示例:" in help_text

            # 2. 测试从注册表生成命令列表
            # 过滤出测试插件的命令
            test_commands = [
                spec
                for path, spec in all_commands.items()
                if spec.name and spec.name.startswith("help_")
            ]

            list_text = generator.generate_command_list(test_commands)

            assert "📋 所有可用命令:" in list_text
            assert "help_basic" in list_text
            assert "help_params" in list_text
            assert "help_options" in list_text
            assert "💡 使用 /<命令名> --help 查看详细帮助" in list_text

            # 3. 测试使用注册命令的错误格式化
            cmd_spec = None
            for path, spec in all_commands.items():
                if "help_params" in path:
                    cmd_spec = spec
                    break

            assert cmd_spec is not None

            result = format_error_with_help("缺少必需参数 input", cmd_spec)

            assert "❌ 缺少必需参数 input" in result
            assert "💡 正确用法:" in result
            assert "/help_params" in result
            assert "📖 详细帮助: /help_params --help" in result

        _cleanup_modules()
