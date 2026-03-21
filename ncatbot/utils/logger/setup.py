"""日志系统全局初始化。"""

import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Sequence

from .core import cleanup_early_handlers
from .formatter import ColoredFormatter, FileFormatter
from .filters import MessageFoldFilter, ThirdPartyNameFilter

DEFAULT_ROUTING_RULES: list[tuple[str, str]] = [
    ("database", "db.log"),
    ("network", "network.log"),
]

_initialized = False


def setup_logging(
    *,
    debug: bool = False,
    console_level: str | None = None,
    file_level: str | None = None,
    log_dir: str | None = None,
    backup_count: int | None = None,
    routing_rules: Sequence[tuple[str, str]] | None = None,
) -> None:
    """初始化全局日志系统。应在应用启动时调用一次。

    Args:
        debug:         是否开启调试模式，为 True 时控制台/文件默认输出 DEBUG。
        console_level: 控制台日志级别，默认读 LOG_LEVEL 环境变量，兜底由 debug 决定。
        file_level:    文件日志级别，默认读 FILE_LOG_LEVEL 环境变量，兜底 DEBUG。
        log_dir:       日志目录，默认读 LOG_FILE_PATH 环境变量，兜底 ./logs。
        backup_count:  日志保留天数，默认读 BACKUP_COUNT 环境变量，兜底 7。
        routing_rules: 路由规则列表，None 使用 DEFAULT_ROUTING_RULES。
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    # 清理早期 handler，避免重复输出
    cleanup_early_handlers()

    default_console = "DEBUG" if debug else "INFO"
    console_level = (console_level or os.getenv("LOG_LEVEL", default_console)).upper()
    file_level = (file_level or os.getenv("FILE_LOG_LEVEL", "DEBUG")).upper()
    log_dir = log_dir or os.getenv("LOG_FILE_PATH", "./logs")
    backup_count = backup_count or int(os.getenv("BACKUP_COUNT", "7"))
    rules = routing_rules if routing_rules is not None else DEFAULT_ROUTING_RULES

    os.makedirs(log_dir, exist_ok=True)

    # 同步 debug 标志到 core 模块，供 get_log() 使用
    from .core import set_debug_mode

    set_debug_mode(debug)

    # root 设为 DEBUG（若调试）或 INFO（第三方库继承此级别）
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.handlers.clear()

    # 压制高频第三方库日志
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("schedule").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("Session").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # 控制台 handler — level 由 console_level 控制
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(ColoredFormatter())
    console_handler.addFilter(MessageFoldFilter())
    console_handler.addFilter(ThirdPartyNameFilter())
    root.addHandler(console_handler)

    # 主文件 handler
    main_fh = TimedRotatingFileHandler(
        os.path.join(log_dir, "bot.log"),
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8",
    )
    main_fh.suffix = "%Y_%m_%d"
    main_fh.setLevel(file_level)
    main_fh.setFormatter(FileFormatter())
    main_fh.addFilter(MessageFoldFilter())
    main_fh.addFilter(ThirdPartyNameFilter())
    root.addHandler(main_fh)

    # 路由规则 handler
    for pattern_str, filename in rules:
        try:
            compiled = re.compile(pattern_str)
        except re.error:
            continue

        class _RegexFilter(logging.Filter):
            def __init__(self, pattern):
                super().__init__()
                self.pattern = pattern

            def filter(self, record: logging.LogRecord) -> bool:
                return bool(self.pattern.match(record.name))

        fh = TimedRotatingFileHandler(
            os.path.join(log_dir, filename),
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.suffix = "%Y_%m_%d"
        fh.setLevel(file_level)
        fh.setFormatter(FileFormatter())
        fh.addFilter(_RegexFilter(compiled))
        root.addHandler(fh)
