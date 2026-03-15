"""日志格式化器。"""

import os
import logging

from ncatbot.utils.assets.color import Color

# 项目根目录，用于计算相对路径
_PROJECT_ROOT = os.path.normcase(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)


def _set_relpath(record: logging.LogRecord) -> None:
    """为 LogRecord 添加 relpath 属性。"""
    abs_path = os.path.normcase(os.path.abspath(record.pathname))
    if abs_path.startswith(_PROJECT_ROOT):
        record.relpath = os.path.relpath(record.pathname, _PROJECT_ROOT).replace(
            "\\", "/"
        )  # type: ignore[attr-defined]
    else:
        record.relpath = record.filename  # type: ignore[attr-defined]


CONSOLE_FORMATS = {
    "DEBUG": (
        f"{Color.CYAN}[%(asctime)s.%(msecs)03d]{Color.RESET} "
        f"{Color.BLUE}%(levelname)-8s{Color.RESET} "
        f"{Color.MAGENTA}%(name)s{Color.RESET} "
        f"{Color.YELLOW}'%(relpath)s:%(lineno)d'{Color.RESET} "
        "| %(message)s"
    ),
    "INFO": (
        f"{Color.CYAN}[%(asctime)s.%(msecs)03d]{Color.RESET} "
        f"{Color.GREEN}%(levelname)-8s{Color.RESET} "
        f"{Color.MAGENTA}%(name)s{Color.RESET} "
        f"{Color.GRAY}'%(relpath)s:%(lineno)d'{Color.RESET} ➜ "
        f"{Color.WHITE}%(message)s{Color.RESET}"
    ),
    "WARNING": (
        f"{Color.CYAN}[%(asctime)s.%(msecs)03d]{Color.RESET} "
        f"{Color.YELLOW}%(levelname)-8s{Color.RESET} "
        f"{Color.MAGENTA}%(name)s{Color.RESET} "
        f"{Color.GRAY}'%(relpath)s:%(lineno)d'{Color.RESET} "
        f"{Color.RED}➜{Color.RESET} "
        f"{Color.YELLOW}%(message)s{Color.RESET}"
    ),
    "ERROR": (
        f"{Color.CYAN}[%(asctime)s.%(msecs)03d]{Color.RESET} "
        f"{Color.RED}%(levelname)-8s{Color.RESET} "
        f"{Color.GRAY}'%(relpath)s:%(lineno)d'{Color.RESET}"
        f"{Color.MAGENTA} %(name)s{Color.RESET} "
        f"{Color.RED}➜{Color.RESET} "
        f"{Color.RED}%(message)s{Color.RESET}"
    ),
    "CRITICAL": (
        f"{Color.CYAN}[%(asctime)s.%(msecs)03d]{Color.RESET} "
        f"{Color.BG_RED}{Color.WHITE}%(levelname)-8s{Color.RESET} "
        f"{Color.GRAY}{{%(module)s}}{Color.RESET}"
        f"{Color.MAGENTA} '%(relpath)s:%(lineno)d'{Color.RESET}"
        f"{Color.MAGENTA} %(name)s{Color.RESET} "
        f"{Color.BG_RED}➜{Color.RESET} "
        f"{Color.BOLD}%(message)s{Color.RESET}"
    ),
}

FILE_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(levelname)-8s %(name)s "
    "'%(relpath)s:%(lineno)d' ➜ %(message)s"
)


class ColoredFormatter(logging.Formatter):
    """根据日志级别动态切换格式模板的控制台 Formatter。"""

    def __init__(self, datefmt: str = "%H:%M:%S"):
        super().__init__(datefmt=datefmt)
        self._formatters = {
            level: logging.Formatter(fmt, datefmt=datefmt)
            for level, fmt in CONSOLE_FORMATS.items()
        }
        self._default = logging.Formatter(CONSOLE_FORMATS["INFO"], datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        _set_relpath(record)
        formatter = self._formatters.get(record.levelname, self._default)
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    """文件日志 Formatter，无颜色码。"""

    def __init__(self, datefmt: str = "%Y-%m-%d %H:%M:%S"):
        super().__init__(FILE_FORMAT, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        _set_relpath(record)
        return super().format(record)
