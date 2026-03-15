"""
03_message_types — 消息构造与解析

演示功能:
  - MessageArray 链式构造
  - 多种消息段: PlainText / At / Image / Reply / Record / Video / File
  - ForwardConstructor 合并转发消息
  - ForwardConstructor 嵌套合并转发消息
  - 从收到的消息中提取图片 URL
  - 使用插件自带的示例图片资源

使用方式:
  群里发 "图文"     → 收到图文混排消息（含示例图片）
  群里发 "转发"     → 收到合并转发消息
  群里发 "嵌套转发"  → 收到嵌套合并转发消息
  群里发 "at我"     → 收到 @你 的消息
  群里发送图片      → Bot 提取并回显图片信息
"""

from pathlib import Path

from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import (
    Image,
    MessageArray,
    ForwardConstructor,
)
from ncatbot.utils import get_log

LOG = get_log("MessageTypes")

# 插件自带的示例资源路径
PLUGIN_DIR = Path(__file__).parent
EXAMPLE_IMAGE = PLUGIN_DIR / "resources" / "example.jpg"
EXAMPLE_VEDIO = PLUGIN_DIR / "resources" / "example.mp4"


class MessageTypesPlugin(NcatBotPlugin):
    name = "message_types"
    version = "1.0.0"
    author = "NcatBot"
    description = "消息构造与解析演示"

    async def on_load(self):
        LOG.info("MessageTypes 插件已加载")

    # ---- 图文混排 ----

    @registrar.on_group_command("图文")
    async def on_rich_text(self, event: GroupMessageEvent):
        """发送图文混排消息"""
        msg = MessageArray()
        msg.add_text("📸 这是一条图文混排消息:\n")
        msg.add_image(str(EXAMPLE_IMAGE))
        msg.add_text("\n以上是示例图片！")

        await self.api.post_group_array_msg(event.group_id, msg)

    # ---- url 链接格式的图片 ----
    
    @registrar.on_group_command("图片")
    async def on_image_url(self, event: GroupMessageEvent):
        """发送 URL 格式的图片消息"""
        msg = MessageArray()
        msg.add_text("📸 这是一条包含 URL 图片的消息:\n")
        msg.add_image("https://pic.3gbizhi.com/uploadmark/20260225/0149243f6bbe37c5c5c6e657b4b77762.webp")  # 直接使用文件路径，底层会上传并转换为 URL

        await self.api.post_group_array_msg(event.group_id, msg)

    # ---- 视频 ----
    @registrar.on_group_command("视频")
    async def on_video(self, event: GroupMessageEvent):
        """发送视频消息"""
        await self.api.post_group_msg(event.group_id, video=str(EXAMPLE_VEDIO))

    # ---- 文件视频 ----
    @registrar.on_group_command("文件视频")
    async def on_file_video(self, event: GroupMessageEvent):
        """发送文件视频消息"""
        await self.api.send_group_file(event.group_id, str(EXAMPLE_VEDIO), name="示例视频.mp4")

    # ---- 动画表情 ----
    @registrar.on_group_command("表情")
    async def on_sticker(self, event: GroupMessageEvent):
        """发送一个动画表情"""
        await self.api.send_group_sticker(event.group_id, str(EXAMPLE_IMAGE))

    # ---- @某人 ----
    @registrar.on_group_command("at我")
    async def on_at_me(self, event: GroupMessageEvent):
        """发送 @你 的消息"""
        msg = MessageArray()
        msg.add_at(event.user_id)
        msg.add_text(" 你被 At 了！")

        await self.api.post_group_array_msg(event.group_id, msg)

    # ---- 合并转发 ----

    @registrar.on_group_command("转发")
    async def on_forward(self, event: GroupMessageEvent):
        """发送合并转发消息"""
        fc = ForwardConstructor(user_id=str(event.self_id), nickname="Bot")

        fc.attach_text("这是转发消息的第一条 📝")
        fc.attach_text("这是转发消息的第二条 📝")

        # 也可以构造图文节点
        msg = MessageArray()
        msg.add_text("这条包含图片: ")
        msg.add_image(str(EXAMPLE_IMAGE))
        fc.attach_message(msg)

        forward = fc.build()
        await self.api.post_group_forward_msg(event.group_id, forward)

    # ---- 嵌套合并转发 ----

    @registrar.on_group_command("嵌套转发")
    async def on_nested_forward(self, event: GroupMessageEvent):
        """发送嵌套合并转发消息（转发里套转发）"""
        bot_id = str(event.self_id)

        # 构造内层转发
        inner_fc = ForwardConstructor(user_id=bot_id, nickname="Bot 内层")
        inner_fc.attach_text("🔹 内层第一条消息")
        inner_fc.attach_text("🔹 内层第二条消息")
        inner_forward = inner_fc.build()

        # 构造外层转发，将内层嵌套进去
        outer_fc = ForwardConstructor(user_id=bot_id, nickname="Bot")
        outer_fc.attach_text("🔸 外层第一条消息")
        outer_fc.attach_forward(inner_forward)  # 嵌套内层转发
        outer_fc.attach_text("🔸 外层第三条消息（在嵌套转发之后）")

        forward = outer_fc.build()
        await self.api.post_group_forward_msg(event.group_id, forward)

    # ---- 提取图片 ----

    @registrar.on_group_message()
    async def on_extract_image(self, event: GroupMessageEvent):
        """收到含图片的消息时，提取并回显图片信息"""
        images = event.message.filter(Image)
        if not images:
            return

        lines = [f"🖼️ 检测到 {len(images)} 张图片:"]
        for i, img in enumerate(images, 1):
            url = getattr(img, "url", None) or getattr(img, "file", "未知")
            lines.append(f"  图片 {i}: {url}")

        await event.reply("\n".join(lines))
