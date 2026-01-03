"""
Mock 数据库模块

提供基于内存的测试数据存储，支持状态变更和重置。
"""

from .models import (
    MockUser,
    MockGroupMember,
    MockGroup,
    MockMessage,
    MockFile,
    MockFolder,
)
from .core import MockDatabase

__all__ = [
    "MockUser",
    "MockGroupMember",
    "MockGroup",
    "MockMessage",
    "MockFile",
    "MockFolder",
    "MockDatabase",
]
