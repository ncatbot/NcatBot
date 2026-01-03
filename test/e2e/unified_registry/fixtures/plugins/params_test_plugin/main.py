"""参数解析测试插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.registry.decorators import (
    option,
    param,
    option_group,
)
from ncatbot.core import MessageEvent


class ParamsTestPlugin(NcatBotPlugin):
    name = "params_test_plugin"
    version = "1.0.0"
    description = "参数解析测试"

    async def on_load(self):
        pass

    # ==================== 基础参数 ====================

    @command_registry.command("say")
    async def say_cmd(self, event: MessageEvent, message: str):
        """单参数命令"""
        await event.reply(f"你说: {message}")

    @command_registry.command("concat")
    async def concat_cmd(self, event: MessageEvent, a: str, b: str):
        """多参数命令"""
        await event.reply(f"{a}{b}")

    # ==================== 类型转换 ====================

    @command_registry.command("calc")
    async def calc_cmd(self, event: MessageEvent, x: int, y: int, op: str = "+"):
        """数学计算命令"""
        if op == "+":
            result = x + y
        elif op == "-":
            result = x - y
        elif op == "*":
            result = x * y
        elif op == "/":
            result = x / y if y != 0 else "除数不能为0"
        else:
            result = "未知操作"
        await event.reply(f"结果: {result}")

    @command_registry.command("repeat")
    async def repeat_cmd(self, event: MessageEvent, text: str, times: int = 1):
        """重复文本命令"""
        await event.reply(text * times)

    # ==================== 短选项 ====================

    @command_registry.command("list")
    @option(short_name="l", long_name="long", help="长格式")
    @option(short_name="a", long_name="all", help="显示隐藏文件")
    @option(short_name="h", long_name="human", help="人类可读格式")
    async def list_cmd(
        self,
        event: MessageEvent,
        path: str = ".",
        long: bool = False,
        all: bool = False,
        human: bool = False,
    ):
        """列出目录内容"""
        result = f"列出目录: {path}"
        flags = []
        if long:
            flags.append("长格式")
        if all:
            flags.append("显示隐藏")
        if human:
            flags.append("人类可读")
        if flags:
            result += f" ({', '.join(flags)})"
        await event.reply(result)

    # ==================== 长选项和命名参数 ====================

    @command_registry.command("backup")
    @option(long_name="compress", help="压缩备份")
    @option(long_name="encrypt", help="加密备份")
    @param(name="dest", default="/backup", help="目标路径")
    async def backup_cmd(
        self,
        event: MessageEvent,
        source: str,
        dest: str = "/backup",
        compress: bool = False,
        encrypt: bool = False,
    ):
        """备份命令"""
        result = f"备份 {source} 到 {dest}"
        options = []
        if compress:
            options.append("压缩")
        if encrypt:
            options.append("加密")
        if options:
            result += f" [{', '.join(options)}]"
        await event.reply(result)

    # ==================== 选项组 ====================

    @command_registry.command("export")
    @option_group(
        name="format", choices=["json", "csv", "xml"], default="json", help="导出格式"
    )
    async def export_cmd(
        self,
        event: MessageEvent,
        data_name: str,
        format: str = "json",
    ):
        """导出数据命令"""
        await event.reply(f"导出 {data_name} 数据为 {format} 格式")

    # ==================== 复杂组合 ====================

    @command_registry.command("process")
    @option(short_name="v", long_name="verbose", help="详细输出")
    @option(long_name="force", help="强制处理")
    @param(name="output", default="result.txt", help="输出文件")
    @param(name="format", default="json", help="输出格式")
    async def process_cmd(
        self,
        event: MessageEvent,
        input_file: str,
        output: str = "result.txt",
        format: str = "json",
        verbose: bool = False,
        force: bool = False,
    ):
        """文件处理命令"""
        result = f"处理文件: {input_file} → {output} ({format}格式)"
        if verbose:
            result += " [详细模式]"
        if force:
            result += " [强制模式]"
        await event.reply(result)
