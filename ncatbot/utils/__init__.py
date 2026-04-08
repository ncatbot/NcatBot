"""NcatBot 工具包。"""

from .logger import (
    get_log,
    get_early_logger,
    resolve_event_log_level,
    format_event_summary,
    BoundLogger,
    setup_logging,
    tqdm,
)  # noqa
from .config import (  # noqa
    ConfigManager,
    get_config_manager,
    Config,
    CONFIG_PATH,
    ConfigValueError,
    MISSING,
    NapCatConfig,
    DEFAULT_BOT_UIN,
    AdapterEntry,
)
from .network import (  # noqa
    post_json,
    get_json,
    download_file,
    get_proxy_url,
    gen_url_with_proxy,
    async_download_to_file,
    async_download_to_bytes,
    async_http_get,
    async_check_proxy,
)
from .status import Status, status  # noqa
from .error import (  # noqa
    NcatBotError,
    NcatBotValueError,
    NcatBotConnectionError,
    AdapterEventError,
)
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
from .pip_helper import (  # noqa
    check_requirements,
    install_packages,
    format_missing_report,
)
from .assets import *  # noqa: F401,F403

ncatbot_config = get_config_manager()

__all__ = [
    "ncatbot_config",
    "Config",
    "ConfigManager",
    "get_config_manager",
    "ConfigValueError",
    "MISSING",
    "CONFIG_PATH",
    "NapCatConfig",
    "DEFAULT_BOT_UIN",
    "AdapterEntry",
    "get_log",
    "get_early_logger",
    "resolve_event_log_level",
    "format_event_summary",
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
    "async_download_to_file",
    "async_download_to_bytes",
    "async_http_get",
    "async_check_proxy",
    "NcatBotError",
    "NcatBotValueError",
    "NcatBotConnectionError",
    "AdapterEventError",
    "confirm",
    "ask",
    "select",
    "async_confirm",
    "async_ask",
    "async_select",
    "is_interactive",
    "set_interactive",
    "set_non_interactive",
    "check_requirements",
    "install_packages",
    "format_missing_report",
]
