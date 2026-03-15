"""
05_bot_api — Bot API 使用大全

演示功能:
  - self.api 消息发送 (post_group_msg / send_group_image)
  - self.api.manage 群管理 (禁言 / 踢人)
  - self.api.info 信息查询 (群列表 / 成员信息 / 登录信息)
  - self.api.info.get_msg() 通过消息 ID 查询消息
  - 消息语法糖 (text / image / at / reply 关键字参数)
  - @registrar.on_group_command() 命令匹配 + At/int 参数绑定
  - 合并转发：通过消息 ID 转发已有消息

使用方式:
  "查群列表"         → 返回 Bot 加入的群列表
  "查成员 @xxx"      → 返回被 @成员的信息
  "查登录信息"       → 返回 Bot 登录信息
  "发图片"           → 发送示例图片
  "发文件"           → 发送示例文件
  "戳我"            → Bot 戳你一下
  "禁言 @xxx 60"    → 禁言被 @用户 60 秒
  "解禁 @xxx"       → 解除被 @用户 的禁言
  回复任意消息 "转发" → 输出被回复消息的 raw_message，并转发到同一群
"""

from pathlib import Path

from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At, MessageArray, PlainText, Reply
from ncatbot.utils import get_log

LOG = get_log("BotAPI")

PLUGIN_DIR = Path(__file__).parent
EXAMPLE_IMAGE = PLUGIN_DIR / "resources" / "example.jpg"
EXAMPLE_FILE = PLUGIN_DIR / "resources" / "example.pdf"


class BotAPIPlugin(NcatBotPlugin):
    name = "bot_api"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bot API 使用大全"

    # ==================== 信息查询 ====================

    @registrar.on_group_command("查群列表")
    async def on_group_list(self, event: GroupMessageEvent):
        """查询 Bot 加入的群列表"""
        groups = await self.api.info.get_group_list()
        if not groups:
            await event.reply("未加入任何群")
            return

        lines = [f"📋 共加入 {len(groups)} 个群:"]
        for g in groups[:10]:
            lines.append(f"  {g.get('group_name', '未知')} ({g.get('group_id')})")
        if len(groups) > 10:
            lines.append(f"  ...还有 {len(groups) - 10} 个群")

        await event.reply("\n".join(lines))

    @registrar.on_group_command("查成员")
    async def on_member_info(self, event: GroupMessageEvent, target: At = None):
        """查询被 @用户的成员信息 — At 参数由 CommandHook 自动绑定"""
        if target is None:
            await event.reply("请 @一个用户，例如: 查成员 @xxx")
            return

        info = await self.api.info.get_group_member_info(event.group_id, target.qq)
        if not info:
            await event.reply("获取信息失败")
            return

        lines = [
            "👤 成员信息:",
            f"  昵称: {info.get('nickname', '未知')}",
            f"  群名片: {info.get('card', '无')}",
            f"  角色: {info.get('role', '未知')}",
            f"  入群时间: {info.get('join_time', '未知')}",
        ]
        await event.reply("\n".join(lines))

    @registrar.on_group_command("查登录信息")
    async def on_login_info(self, event: GroupMessageEvent):
        """查询 Bot 登录信息"""
        info = await self.api.info.get_login_info()
        await event.reply(
            f"🤖 Bot 信息:\n"
            f"  QQ: {info.get('user_id', '未知')}\n"
            f"  昵称: {info.get('nickname', '未知')}"
        )

    # ==================== 消息发送 ====================

    @registrar.on_group_command("发图片")
    async def on_send_image(self, event: GroupMessageEvent):
        """发送示例图片"""
        await self.api.post_group_msg(
            event.group_id,
            text="📸 这是通过语法糖发送的图片:",
            image=str(EXAMPLE_IMAGE),
        )

    @registrar.on_group_command("发文件")
    async def on_send_file(self, event: GroupMessageEvent):
        """发送示例文件"""
        await self.api.send_group_file(
            event.group_id,
            str(EXAMPLE_FILE),
            name="示例文件.pdf",
        )

    @registrar.on_group_command("戳我")
    async def on_poke(self, event: GroupMessageEvent):
        """戳一戳"""
        await self.api.send_poke(event.group_id, event.user_id)

    # ==================== 群管理 ====================

    @registrar.on_group_command("禁言")
    async def on_ban(
        self, event: GroupMessageEvent, target: At = None, duration: int = 60
    ):
        """禁言用户 — At + int 参数由 CommandHook 自动绑定"""
        if target is None:
            await event.reply("请 @一个用户，例如: 禁言 @xxx 60")
            return

        await self.api.manage.set_group_ban(event.group_id, target.qq, duration)
        await event.reply(f"已禁言 {duration} 秒")

    @registrar.on_group_command("解禁")
    async def on_unban(self, event: GroupMessageEvent, target: At = None):
        """解除禁言 — At 参数由 CommandHook 自动绑定"""
        if target is None:
            await event.reply("请 @一个用户，例如: 解禁 @xxx")
            return

        await self.api.manage.set_group_ban(event.group_id, target.qq, 0)
        await event.reply("已解除禁言")

    # ==================== 转发（通过消息 ID）====================

    @registrar.on_group_command("转发")
    async def on_forward_by_quote(self, event: GroupMessageEvent):
        """回复任意消息并发送"转发"，Bot 输出被引用消息的 raw_message 并转发到群里"""
        # 从消息中提取 Reply 段，判断是否引用了某条消息
        replies = event.message.filter(Reply)
        if not replies:
            await event.reply("请先回复（引用）一条消息，再发送「转发」")
            return

        quoted_msg_id = replies[0].id

        # 通过 get_msg 获取被引用消息的详情
        msg_data = await self.api.info.get_msg(quoted_msg_id)
        if not msg_data:
            await event.reply("获取被引用消息失败")
            return

        raw = msg_data.get("raw_message", "（无内容）")
        # 用 PlainText 直接构造纯文本段，避免 raw_message 中的 CQ 码被解析为实际消息段
        info = MessageArray()
        info.add_segment(PlainText(text=f"被转发消息的 raw_message:\n{raw}"))
        await event.reply(rtf=info)

        # 通过消息 ID 直接转发到同一个群
        await self.api.send_group_forward_msg_by_id(event.group_id, [quoted_msg_id])
