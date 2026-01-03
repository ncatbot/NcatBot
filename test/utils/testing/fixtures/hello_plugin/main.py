"""HelloPlugin - 用于测试工具验证的简单插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core import MessageEvent
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.registry.decorators import (
    param,
    option,
)


class HelloPlugin(NcatBotPlugin):
    """用于测试工具验证的简单插件"""

    name = "hello_plugin"
    version = "1.0.0"
    description = "用于测试工具验证的简单插件"

    async def on_load(self):
        pass

    @command_registry.command("hello", aliases=["hi"], description="问候")
    async def hello_command(self, event: MessageEvent):
        """问候命令"""
        await event.reply("你好！这是来自 HelloPlugin 的问候。")

    @command_registry.command("echo", description="回显文本")
    @param(name="lang", default="zh", help="语言")
    @option(short_name="v", long_name="verbose", help="详细输出")
    async def echo_command(
        self,
        event: MessageEvent,
        text: str,
        lang: str = "zh",
        verbose: bool = False,
    ):
        """回显命令"""
        reply = f"[{lang}] 你说的是：{text}"
        if verbose:
            reply += " (verbose)"
        await event.reply(reply)
