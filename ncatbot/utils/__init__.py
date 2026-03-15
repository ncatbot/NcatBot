"""NcatBot 工具包。"""

from .logger import get_log, BoundLogger, setup_logging, tqdm  # noqa
from .config import (  # noqa
    ConfigManager,
    get_config_manager,
    Config,
    CONFIG_PATH,
    ConfigValueError,
)
from .network import (  # noqa
    post_json,
    get_json,
    download_file,
    get_proxy_url,
    gen_url_with_proxy,
)
from .status import Status, status  # noqa
from .error import NcatBotError, NcatBotValueError, NcatBotConnectionError  # noqa
from .prompt import (  # noqa
    confirm,
    ask,
    select,
    async_confirm,
    async_ask,
    async_select,
    is_interactive,
    set_interactive,
    set_non_interactive,
)
from .assets import *  # noqa: F401,F403

ncatbot_config = get_config_manager()

__all__ = [
    "ncatbot_config",
    "Config",
    "ConfigManager",
    "get_config_manager",
    "ConfigValueError",
    "CONFIG_PATH",
    "get_log",
    "BoundLogger",
    "setup_logging",
    "tqdm",
    "status",
    "Status",
    "post_json",
    "get_json",
    "download_file",
    "get_proxy_url",
    "gen_url_with_proxy",
    "NcatBotError",
    "NcatBotValueError",
    "NcatBotConnectionError",
    "confirm",
    "ask",
    "select",
    "async_confirm",
    "async_ask",
    "async_select",
    "is_interactive",
    "set_interactive",
    "set_non_interactive",
]
