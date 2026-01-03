"""简单回复插件 - 测试 reply 功能"""

from typing import List

from ncatbot.plugin_system import NcatBotPlugin, command_registry
from ncatbot.core import GroupMessageEvent


class SimpleReplyPlugin(NcatBotPlugin):
    """简单回复插件 - 测试 reply 功能"""

    name = "simple_reply_plugin"
    version = "1.0.0"

    handled_commands: List[str] = []

    async def on_load(self):
        SimpleReplyPlugin.handled_commands = []

        @command_registry.command("ping", description="ping 命令")
        async def ping_handler(event: GroupMessageEvent):
            SimpleReplyPlugin.handled_commands.append("ping")
            await event.reply("pong")

        @command_registry.command("echo", description="回显命令")
        async def echo_handler(event: GroupMessageEvent, text: str = ""):
            SimpleReplyPlugin.handled_commands.append(f"echo:{text}")
            await event.reply(f"Echo: {text}")

        @command_registry.command("greet", description="问候命令")
        async def greet_handler(event: GroupMessageEvent, name: str = "World"):
            SimpleReplyPlugin.handled_commands.append(f"greet:{name}")
            await event.reply(f"Hello, {name}!")
