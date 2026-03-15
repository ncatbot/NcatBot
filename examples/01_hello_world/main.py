"""
01_hello_world — 最小可运行插件

演示功能:
  - NcatBotPlugin 基类继承
  - manifest.toml 插件清单
  - on_load / on_close 生命周期
  - @registrar.on_group_command() 命令匹配装饰器
  - event.reply() 回复消息

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
群里发送 "hello" 即可收到回复。
群里发送 "hi" 即可收到引用回复 + @提及。
"""

from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import MessageArray
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")


class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world"
    version = "1.0.0"
    author = "NcatBot"
    description = "最小可运行插件 — 回复 hello"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorld 插件已卸载。")

    @registrar.on_group_command("hello", ignore_case=True)
    async def on_hello(self, event: GroupMessageEvent):
        """收到群消息 'hello' 时回复"""
        await self.api.post_group_msg(event.group_id, text="Hello, World! 👋")

    @registrar.on_group_command("hi", ignore_case=True)
    async def on_hi(self, event: GroupMessageEvent):
        """用 event.reply() 快速回复富文本消息（自动引用 + @发送者 + 文字）"""
        await event.reply(text="你好呀！这是通过 event.reply() 发送的富文本快速回复 🎉")

    @registrar.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent):
        """收到私聊消息 'hello' 时回复"""
        await event.reply(text="你好！这是来自 HelloWorld 插件的私聊回复 👋")
