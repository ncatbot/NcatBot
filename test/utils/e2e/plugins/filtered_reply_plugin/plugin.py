"""过滤器回复插件 - 测试过滤器与 reply 功能"""

from typing import List

from ncatbot.plugin_system import (
    NcatBotPlugin,
    command_registry,
    filter,
    GroupFilter,
    PrivateFilter,
)
from ncatbot.core import GroupMessageEvent, PrivateMessageEvent


class FilteredReplyPlugin(NcatBotPlugin):
    """过滤器回复插件 - 测试过滤器与 reply 功能"""

    name = "filtered_reply_plugin"
    version = "1.0.0"

    handled_events: List[str] = []

    async def on_load(self):
        FilteredReplyPlugin.handled_events = []

        @command_registry.command("group_ping", description="仅群聊命令")
        @filter(GroupFilter())
        async def group_ping_handler(event: GroupMessageEvent):
            FilteredReplyPlugin.handled_events.append("group_ping")
            await event.reply("Group pong!")

        @command_registry.command("private_ping", description="仅私聊命令")
        @filter(PrivateFilter())
        async def private_ping_handler(event: PrivateMessageEvent):
            FilteredReplyPlugin.handled_events.append("private_ping")
            await event.reply("Private pong!")
