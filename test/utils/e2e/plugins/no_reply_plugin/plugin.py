"""无回复插件 - 测试不发送回复的情况"""

from typing import List

from ncatbot.plugin_system import NcatBotPlugin, command_registry
from ncatbot.core import GroupMessageEvent


class NoReplyPlugin(NcatBotPlugin):
    """无回复插件 - 测试不发送回复的情况"""

    name = "no_reply_plugin"
    version = "1.0.0"

    handled_commands: List[str] = []

    async def on_load(self):
        NoReplyPlugin.handled_commands = []

        @command_registry.command("silent", description="静默命令")
        async def silent_handler(event: GroupMessageEvent):
            NoReplyPlugin.handled_commands.append("silent")
            # 不回复
