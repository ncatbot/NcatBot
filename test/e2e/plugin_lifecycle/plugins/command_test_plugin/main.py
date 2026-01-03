"""命令测试插件 - 测试与 unified_registry 的协作"""

from typing import List
from ncatbot.plugin_system import NcatBotPlugin, command_registry
from ncatbot.core import GroupMessageEvent
from ncatbot.utils import get_log

LOG = get_log("TestPlugins")


class CommandTestPlugin(NcatBotPlugin):
    """命令测试插件 - 测试与 unified_registry 的协作"""

    name = "command_test_plugin"
    version = "1.0.0"

    # 命令调用追踪
    command_calls: List[str] = []
    alias_calls: List[str] = []

    async def on_load(self):
        LOG.debug("CommandTestPlugin on_load called")

    async def on_close(self):
        LOG.debug("CommandTestPlugin on_close called")

    @command_registry.command(
        "cmd_test", aliases=["ct"], description="测试命令", prefixes=["", "/"]
    )
    async def cmd_test(self, event: GroupMessageEvent):
        CommandTestPlugin.command_calls.append("cmd_test")
        await event.reply("cmd_test executed")

    @command_registry.command("cmd_echo", description="回声命令", prefixes=["", "/"])
    async def cmd_echo(self, event: GroupMessageEvent, text: str = ""):
        CommandTestPlugin.command_calls.append(f"cmd_echo:{text}")
        await event.reply(f"Echo: {text}")

    @classmethod
    def reset_counters(cls):
        cls.command_calls = []
        cls.alias_calls = []
