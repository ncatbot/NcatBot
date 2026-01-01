from ncatbot.utils import get_log

LOG = get_log("Event")
LOG.warning("ncatbot.plugin_system.event 模块已废弃, 请从 ncatbot.core 模块导入 NcatBotEvent")

from ncatbot.core import NcatBotEvent

__all__ = ["NcatBotEvent"]