from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin

_MENU = """
    🍊OrangeBot功能菜单🍊

【测试】😶 原神文案(GenshinCopyBank)(数据库未完善)
/wa - 一句原神文案

【测试】‍🌫️ 自动对话(AutoChat)
/chat on - 开启自动对话
/chat off - 关闭自动对话
仅限私聊使用，开启后可与猫娘对话

📚 禁漫本子下载(JmComicPlugin)
/jm <车牌> - 下载jm本子PDF

🎨 二次元图片(Lolicon)
/loli <数量> <标签> - 随机二次元图片
/r18 <数量> <标签> - R18图片(需权限)

📋 群聊关键词回复(KeywordReply)
/kw 查看热管理菜单
热管理功能仅限管理员使用
"""


class BotMenuPlugin(NcatBotPlugin):
    name = "bot_menu"
    version = "1.0.0"
    author = "migrated"
    description = "功能菜单"

    @registrar.qq.on_private_message()
    async def on_private_test(self, event: PrivateMessageEvent):
        if event.raw_message.strip() == "测试":
            await event.reply("NcatBot 测试成功喵~", at_sender=False)

    @registrar.qq.on_group_command("/menu", "/菜单", "menu", "菜单")
    async def on_group_menu(self, event: GroupMessageEvent):
        await event.reply(_MENU.strip(), at_sender=False)

    @registrar.qq.on_private_command("/menu", "/菜单", "menu", "菜单")
    async def on_private_menu(self, event: PrivateMessageEvent):
        await event.reply(_MENU.strip(), at_sender=False)
