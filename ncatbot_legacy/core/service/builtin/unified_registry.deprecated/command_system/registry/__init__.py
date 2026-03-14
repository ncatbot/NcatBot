"""现代化命令注册系统

提供直观、类型安全的命令注册API。
"""

from .registry import command_registry
from .decorators import option, param, option_group

__all__ = [
    "command_registry",
    "option",
    "param",
    "option_group",
]
