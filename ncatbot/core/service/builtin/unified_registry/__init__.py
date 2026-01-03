"""统一注册服务

提供命令和过滤器的统一管理功能。
"""

from .service import UnifiedRegistryService
from .filter_system import filter_registry
from .filter_system.decorators import *  # noqa: F401,F403
from .command_system import command_registry
from .command_system.registry import option, param, option_group
from .filter_system import *  # noqa: F401,F403

__all__ = [
    "UnifiedRegistryService",
    "command_registry",
    "filter_registry",
    "option",
    "param",
    "option_group",
]

from . import filter_system

__all__.extend(getattr(filter_system, "__all__", []))  # type: ignore
