from pathlib import Path

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import File, MessageArray


class JmComicPlugin(NcatBotPlugin):
    name = "JmComicPlugin"
    version = "0.0.2"
    author = "FunEnn"
    description = "禁漫本子下载插件，支持通过/jm命令下载本子并发送PDF文件"

    async def on_load(self) -> None:
        import jmcomic

        self.base_dir = Path(self.workspace) / "pdf"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        config_path = Path(__file__).resolve().parent / "option.yml"
        self.jm_option = jmcomic.JmOption.from_file(str(config_path))

    @registrar.qq.on_command("/jm", "jm")
    async def jm_download_cmd(
        self, event: GroupMessageEvent | PrivateMessageEvent, album_id: str
    ):
        try:
            if not album_id.isdigit():
                await event.reply("本子ID必须是数字，例如: /jm 422866", at_sender=False)
                return

            pdf_path = self.base_dir / f"{album_id}.pdf"

            if not pdf_path.exists():
                await event.reply(f"开始下载本子 {album_id}，请稍候...", at_sender=False)
                self.jm_option.download_album([album_id])

            if pdf_path.exists():
                await self._send_pdf_file(event, str(pdf_path))
            else:
                await event.reply("未找到 PDF 文件，可能下载失败。", at_sender=False)
        except Exception as e:
            await event.reply(f"下载过程中发生错误: {e!s}", at_sender=False)

    async def _send_pdf_file(
        self, event: GroupMessageEvent | PrivateMessageEvent, pdf_path: str
    ):
        try:
            pdf_file = File(file=pdf_path)
            await event.reply(rtf=MessageArray([pdf_file]), at_sender=False)
        except Exception as e:
            await event.reply(f"发送文件失败: {e!s}", at_sender=False)
