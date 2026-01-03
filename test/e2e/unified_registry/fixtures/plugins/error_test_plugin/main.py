"""异常处理测试插件

测试命令系统的异常处理和错误反馈。
"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core import MessageEvent


class ErrorTestPlugin(NcatBotPlugin):
    name = "error_test_plugin"
    version = "1.0.0"
    description = "异常处理测试"

    async def on_load(self):
        pass

    # ==================== 正常命令 ====================

    @command_registry.command("normal")
    async def normal_cmd(self, event: MessageEvent, text: str):
        """正常命令"""
        await event.reply(f"正常: {text}")

    @command_registry.command("number")
    async def number_cmd(self, event: MessageEvent, value: int):
        """需要整数参数的命令"""
        await event.reply(f"数字: {value}")

    @command_registry.command("multi")
    async def multi_cmd(self, event: MessageEvent, a: str, b: str, c: str):
        """需要多个参数的命令"""
        await event.reply(f"参数: {a}, {b}, {c}")

    # ==================== 会抛出异常的命令 ====================

    @command_registry.command("crash")
    async def crash_cmd(self, event: MessageEvent):
        """会崩溃的命令"""
        raise RuntimeError("命令执行时发生了预期的错误")

    @command_registry.command("divide")
    async def divide_cmd(self, event: MessageEvent, a: int, b: int):
        """可能除零的命令"""
        result = a / b
        await event.reply(f"结果: {result}")

    @command_registry.command("valueerror")
    async def value_error_cmd(self, event: MessageEvent, value: str):
        """抛出 ValueError 的命令"""
        if not value.isdigit():
            raise ValueError(f"期望数字字符串，但收到: {value}")
        await event.reply(f"数字字符串: {value}")
