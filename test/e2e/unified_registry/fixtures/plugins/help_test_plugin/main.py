"""帮助系统测试插件

测试各种命令配置，验证 help_system.py 的帮助生成功能。
"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.registry.decorators import (
    option,
    param,
    option_group,
)
from ncatbot.core import MessageEvent


class HelpTestPlugin(NcatBotPlugin):
    name = "help_test_plugin"
    version = "1.0.0"
    description = "帮助系统测试"

    async def on_load(self):
        pass

    # ==================== 基础命令 ====================

    @command_registry.command("help_basic", description="基础命令描述")
    async def basic_cmd(self, event: MessageEvent):
        """基础命令"""
        await event.reply("basic")

    @command_registry.command("help_no_desc")
    async def no_desc_cmd(self, event: MessageEvent):
        """无描述命令"""
        await event.reply("no_desc")

    # ==================== 带别名命令 ====================

    @command_registry.command(
        "help_alias", aliases=["ha", "halias"], description="带别名命令"
    )
    async def alias_cmd(self, event: MessageEvent):
        """带别名命令"""
        await event.reply("alias")

    # ==================== 带参数命令 ====================

    @command_registry.command("help_params", description="带参数命令")
    @param(name="input", help="输入文件路径")
    @param(name="output", default="out.txt", help="输出文件路径")
    async def params_cmd(
        self, event: MessageEvent, input: str, output: str = "out.txt"
    ):
        """带参数命令"""
        await event.reply(f"input={input}, output={output}")

    @command_registry.command("help_param_choices", description="带选择值的参数")
    @param(name="format", choices=["json", "xml", "csv"], help="输出格式")
    async def param_choices_cmd(self, event: MessageEvent, format: str):
        """带选择值参数命令"""
        await event.reply(f"format={format}")

    # ==================== 带选项命令 ====================

    @command_registry.command("help_options", description="带选项命令")
    @option(short_name="v", long_name="verbose", help="详细模式")
    @option(short_name="a", help="显示全部")
    @option(long_name="force", help="强制执行")
    async def options_cmd(
        self,
        event: MessageEvent,
        verbose: bool = False,
        a: bool = False,
        force: bool = False,
    ):
        """带选项命令"""
        await event.reply(f"verbose={verbose}, a={a}, force={force}")

    # ==================== 带选项组命令 ====================

    @command_registry.command("help_groups", description="带选项组命令")
    @option_group(
        name="mode",
        choices=["fast", "normal", "safe"],
        default="normal",
        help="处理模式",
    )
    async def groups_cmd(self, event: MessageEvent, mode: str = "normal"):
        """带选项组命令"""
        await event.reply(f"mode={mode}")

    # ==================== 复杂组合命令 ====================

    @command_registry.command(
        "help_complex", description="复杂组合命令，测试完整帮助生成"
    )
    @param(name="source", help="源文件路径")
    @param(name="dest", default="backup", help="目标路径")
    @option(short_name="v", long_name="verbose", help="详细输出")
    @option(short_name="f", long_name="force", help="强制覆盖")
    @option_group(
        name="compression",
        choices=["none", "gzip", "bzip2"],
        default="gzip",
        help="压缩方式",
    )
    async def complex_cmd(
        self,
        event: MessageEvent,
        source: str,
        dest: str = "backup",
        compression: str = "gzip",
        verbose: bool = False,
        force: bool = False,
    ):
        """复杂组合命令"""
        await event.reply(
            f"source={source}, dest={dest}, compression={compression}, "
            f"verbose={verbose}, force={force}"
        )
