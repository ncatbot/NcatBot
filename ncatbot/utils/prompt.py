"""
统一交互模型

提供 confirm / ask / select 三种交互原语，支持交互模式与非交互模式。
非交互模式下自动返回默认值，适用于 CI、后台服务、自动化脚本等场景。

模式判断优先级（高→低）：
    1. 显式调用 set_non_interactive() / set_interactive()
    2. 环境变量 NCATBOT_NON_INTERACTIVE=1
    3. sys.stdin.isatty() fallback
"""

import asyncio
import functools
import os
import sys
from enum import Enum
from typing import List, Optional

from ncatbot.utils.logger import get_log

LOG = get_log("Prompt")


# ==================== 模式管理 ====================


class PromptMode(Enum):
    INTERACTIVE = "interactive"
    NON_INTERACTIVE = "non_interactive"


_explicit_mode: Optional[PromptMode] = None


def set_non_interactive() -> None:
    """显式设置为非交互模式。"""
    global _explicit_mode
    _explicit_mode = PromptMode.NON_INTERACTIVE


def set_interactive() -> None:
    """显式设置为交互模式。"""
    global _explicit_mode
    _explicit_mode = PromptMode.INTERACTIVE


def is_interactive() -> bool:
    """判断当前是否为交互模式。"""
    if _explicit_mode is not None:
        return _explicit_mode == PromptMode.INTERACTIVE
    if os.environ.get("NCATBOT_NON_INTERACTIVE", "").strip() in ("1", "true", "yes"):
        return False
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


# ==================== 同步交互原语 ====================


def confirm(message: str, *, default: bool = False) -> bool:
    """确认操作（y/n）。

    Args:
        message: 提示信息
        default: 非交互模式或直接回车时的默认值

    Returns:
        用户是否确认
    """
    if not is_interactive():
        LOG.debug("非交互模式，confirm 返回默认值: %s", default)
        return default

    hint = " [Y/n] " if default else " [y/N] "
    try:
        answer = input(message + hint).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


def ask(message: str, *, default: str = "") -> str:
    """文本输入。

    Args:
        message: 提示信息
        default: 非交互模式或直接回车时的默认值

    Returns:
        用户输入的文本
    """
    if not is_interactive():
        LOG.debug("非交互模式，ask 返回默认值: %r", default)
        return default

    suffix = f" [{default}] " if default else " "
    try:
        answer = input(message + suffix).strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return answer if answer else default


def select(message: str, choices: List[str], *, default_index: int = 0) -> str:
    """选择列表。

    Args:
        message: 提示信息
        choices: 可选项列表
        default_index: 非交互模式或无效输入时的默认选项索引

    Returns:
        用户选择的选项
    """
    if not choices:
        raise ValueError("choices 不能为空")
    default_index = max(0, min(default_index, len(choices) - 1))

    if not is_interactive():
        LOG.debug("非交互模式，select 返回默认值: %r", choices[default_index])
        return choices[default_index]

    print(message)
    for i, choice in enumerate(choices):
        marker = "*" if i == default_index else " "
        print(f"  {marker} [{i + 1}] {choice}")

    try:
        answer = input(f"请选择 [1-{len(choices)}] (默认 {default_index + 1}): ").strip()
    except (EOFError, KeyboardInterrupt):
        return choices[default_index]

    if not answer:
        return choices[default_index]
    try:
        idx = int(answer) - 1
        if 0 <= idx < len(choices):
            return choices[idx]
    except ValueError:
        pass
    LOG.warning("无效输入 %r，使用默认选项", answer)
    return choices[default_index]


# ==================== 异步交互原语 ====================


async def _async_input(prompt_text: str = "") -> str:
    """在线程池中执行 input()，避免阻塞 asyncio 事件循环。"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(input, prompt_text))


async def async_confirm(message: str, *, default: bool = False) -> bool:
    """confirm 的异步版本。"""
    if not is_interactive():
        LOG.debug("非交互模式，async_confirm 返回默认值: %s", default)
        return default

    hint = " [Y/n] " if default else " [y/N] "
    try:
        answer = (await _async_input(message + hint)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    if not answer:
        return default
    return answer in ("y", "yes")


async def async_ask(message: str, *, default: str = "") -> str:
    """ask 的异步版本。"""
    if not is_interactive():
        LOG.debug("非交互模式，async_ask 返回默认值: %r", default)
        return default

    suffix = f" [{default}] " if default else " "
    try:
        answer = (await _async_input(message + suffix)).strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return answer if answer else default


async def async_select(
    message: str, choices: List[str], *, default_index: int = 0
) -> str:
    """select 的异步版本。"""
    if not choices:
        raise ValueError("choices 不能为空")
    default_index = max(0, min(default_index, len(choices) - 1))

    if not is_interactive():
        LOG.debug("非交互模式，async_select 返回默认值: %r", choices[default_index])
        return choices[default_index]

    print(message)
    for i, choice in enumerate(choices):
        marker = "*" if i == default_index else " "
        print(f"  {marker} [{i + 1}] {choice}")

    try:
        answer = (
            await _async_input(
                f"请选择 [1-{len(choices)}] (默认 {default_index + 1}): "
            )
        ).strip()
    except (EOFError, KeyboardInterrupt):
        return choices[default_index]

    if not answer:
        return choices[default_index]
    try:
        idx = int(answer) - 1
        if 0 <= idx < len(choices):
            return choices[idx]
    except ValueError:
        pass
    LOG.warning("无效输入 %r，使用默认选项", answer)
    return choices[default_index]
