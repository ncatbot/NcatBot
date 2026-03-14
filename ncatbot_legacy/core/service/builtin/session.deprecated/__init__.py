"""
Session 系统

完全通过 Hook 实现的会话管理。
"""

from .session import Session
from .manager import SessionManager
from .hooks import (
    SessionStartHook,
    SessionStepHook,
    SessionEndHook,
    session_start,
    session_step,
    session_end,
    default_key_func,
)

__all__ = [
    "Session",
    "SessionManager",
    "SessionStartHook",
    "SessionStepHook",
    "SessionEndHook",
    "session_start",
    "session_step",
    "session_end",
    "default_key_func",
]
