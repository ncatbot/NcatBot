"""装饰器验证测试插件

测试各种装饰器组合，验证 decorator_validator.py 的功能。
"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.registry.decorators import (
    option,
    param,
    option_group,
)
from ncatbot.core import MessageEvent


class DecoratorTestPlugin(NcatBotPlugin):
    name = "decorator_test_plugin"
    version = "1.0.0"
    description = "装饰器验证测试"

    async def on_load(self):
        pass

    # ==================== 单短选项 ====================

    @command_registry.command("opt_short")
    @option(short_name="v", help="详细模式")
    async def opt_short_cmd(self, event: MessageEvent, v: bool = False):
        """单短选项命令"""
        await event.reply(f"verbose={v}")

    # ==================== 单长选项 ====================

    @command_registry.command("opt_long")
    @option(long_name="verbose", help="详细模式")
    async def opt_long_cmd(self, event: MessageEvent, verbose: bool = False):
        """单长选项命令"""
        await event.reply(f"verbose={verbose}")

    # ==================== 短选项和长选项组合 ====================

    @command_registry.command("opt_both")
    @option(short_name="v", long_name="verbose", help="详细模式")
    @option(short_name="q", long_name="quiet", help="静默模式")
    async def opt_both_cmd(
        self, event: MessageEvent, verbose: bool = False, quiet: bool = False
    ):
        """短选项和长选项组合"""
        await event.reply(f"verbose={verbose}, quiet={quiet}")

    # ==================== 多个选项 ====================

    @command_registry.command("opt_multi")
    @option(short_name="a", help="选项A")
    @option(short_name="b", help="选项B")
    @option(short_name="c", help="选项C")
    @option(long_name="debug", help="调试模式")
    @option(long_name="trace", help="追踪模式")
    async def opt_multi_cmd(
        self,
        event: MessageEvent,
        a: bool = False,
        b: bool = False,
        c: bool = False,
        debug: bool = False,
        trace: bool = False,
    ):
        """多选项命令"""
        opts = []
        if a:
            opts.append("a")
        if b:
            opts.append("b")
        if c:
            opts.append("c")
        if debug:
            opts.append("debug")
        if trace:
            opts.append("trace")
        await event.reply(f"options={opts}")

    # ==================== 命名参数 ====================

    @command_registry.command("param_basic")
    @param(name="name", help="名称")
    @param(name="value", default="default_value", help="值")
    async def param_basic_cmd(
        self, event: MessageEvent, name: str, value: str = "default_value"
    ):
        """基础命名参数"""
        await event.reply(f"name={name}, value={value}")

    # ==================== 选项组 ====================

    @command_registry.command("group_basic")
    @option_group(
        name="format", choices=["json", "xml", "yaml"], default="json", help="输出格式"
    )
    async def group_basic_cmd(self, event: MessageEvent, format: str = "json"):
        """基础选项组"""
        await event.reply(f"format={format}")

    # ==================== 复杂组合 ====================

    @command_registry.command("complex")
    @option(short_name="v", long_name="verbose", help="详细模式")
    @option(short_name="f", long_name="force", help="强制模式")
    @param(name="input", help="输入路径")
    @param(name="output", default="out.txt", help="输出路径")
    @option_group(
        name="mode",
        choices=["fast", "normal", "safe"],
        default="normal",
        help="处理模式",
    )
    async def complex_cmd(
        self,
        event: MessageEvent,
        input: str,
        output: str = "out.txt",
        mode: str = "normal",
        verbose: bool = False,
        force: bool = False,
    ):
        """复杂组合命令"""
        result = f"input={input}, output={output}, mode={mode}"
        if verbose:
            result += ", verbose"
        if force:
            result += ", force"
        await event.reply(result)

    # ==================== 长选项名格式验证 ====================

    @command_registry.command("opt_format")
    @option(long_name="with_dash", help="带连字符的选项")
    @option(long_name="with_underscore", help="带下划线的选项")
    @option(long_name="mixedCase123", help="混合大小写和数字")
    async def opt_format_cmd(
        self,
        event: MessageEvent,
        with_dash: bool = False,
        with_underscore: bool = False,
        mixedCase123: bool = False,
    ):
        """选项名格式验证"""
        await event.reply("ok")
