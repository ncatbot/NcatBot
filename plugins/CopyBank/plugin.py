import json
import random
from pathlib import Path

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("CopyBank")

BANK_FILE = Path(__file__).resolve().parent / "CopyBank.json"


class CopyBank(NcatBotPlugin):
    name = "CopyBank"
    version = "1.0.1"
    author = "cheng160"
    description = "本地 JSON 文案库，/wa 随机发送"

    async def on_load(self) -> None:
        if not BANK_FILE.exists():
            default = [
                "默认文案第一行\n默认文案第二行",
                "早安～\n今天也要开心呀！",
                "晚安 🌙\n好梦～",
            ]
            BANK_FILE.write_text(
                json.dumps(default, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            LOG.info("已创建默认文案库：%s", BANK_FILE)

    @registrar.qq.on_command("/wa", "wa")
    async def wa_cmd(self, event: GroupMessageEvent | PrivateMessageEvent):
        try:
            texts = json.loads(BANK_FILE.read_text(encoding="utf-8"))
            if not isinstance(texts, list) or not texts:
                await event.reply("文案库为空～", at_sender=False)
                return
            await event.reply(random.choice(texts), at_sender=False)
        except Exception:
            LOG.exception("读取文案库失败")
            await event.reply("文案库开小差了…", at_sender=False)
