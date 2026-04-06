"""
Session 便利方法的辅助类型

- ``SessionCancelled`` — 取消词触发时由 ``wait_session_event`` 抛出的异常
- ``SessionResult`` — 高层 session 方法的统一返回类型
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ncatbot.core import Event

__all__ = ["SessionCancelled", "SessionResult"]


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class SessionCancelled(Exception):
    """用户输入了取消词，由 ``wait_session_event`` 抛出。

    Attributes:
        event: 触发取消的事件
        word: 匹配到的取消词
    """

    def __init__(self, event: "Event", word: str) -> None:
        self.event = event
        self.word = word
        super().__init__(f"Session cancelled by keyword {word!r}")


# ---------------------------------------------------------------------------
# 返回值
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SessionResult:
    """高层 session 便利方法的统一返回类型。

    Attributes:
        ok: ``True`` 表示用户正常回复
        text: 回复文本（``raw_message.strip()``），仅 ``ok=True`` 时有值
        event: 原始 :class:`Event`，仅 ``ok=True`` 时有值
        cancelled: ``True`` 表示用户输入了取消词
        timed_out: ``True`` 表示等待超时
        cancel_word: 匹配到的取消词，仅 ``cancelled=True`` 时有值
        key: ``session_choose`` 专用，匹配到的选项 key
    """

    ok: bool
    text: Optional[str] = None
    event: Optional["Event"] = None
    cancelled: bool = False
    timed_out: bool = False
    cancel_word: Optional[str] = None
    key: Optional[str] = None

    # ---- 工厂方法 ----

    @staticmethod
    def of(
        event: "Event",
        text: str,
        *,
        key: Optional[str] = None,
    ) -> "SessionResult":
        """创建成功结果。"""
        return SessionResult(ok=True, text=text, event=event, key=key)

    @staticmethod
    def from_timeout() -> "SessionResult":
        """创建超时结果。"""
        return SessionResult(ok=False, timed_out=True)

    @staticmethod
    def from_cancel(event: "Event", word: str) -> "SessionResult":
        """创建取消结果。"""
        return SessionResult(
            ok=False,
            cancelled=True,
            event=event,
            cancel_word=word,
        )

    @staticmethod
    def from_invalid(text: str, event: "Event") -> "SessionResult":
        """创建无效输入结果（选择题模式，重试耗尽）。"""
        return SessionResult(ok=False, text=text, event=event)
