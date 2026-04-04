from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class TemplatePlugin(NcatBotPlugin):
    name = "template_plugin"
    version = "1.0.1"
    author = "cheng160"
    description = "空白模板插件（可自行扩展命令）"

    async def on_load(self) -> None:
        self.logger.info("%s 已加载", self.name)

    @registrar.qq.on_group_command("ping_template")
    async def ping(self, event: GroupMessageEvent):
        await event.reply(text="pong", at_sender=False)
