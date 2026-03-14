"""统一注册服务

提供命令和过滤器的统一管理功能。
"""

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

__all__.extend(getattr(filter_system.decorators, "__all__", []))  # type: ignore


def __getattr__(name):
    """向后兼容: UnifiedRegistryService 已移至 ncatbot.legacy"""
    if name == "UnifiedRegistryService":
        from ncatbot.legacy.unified_registry.service import UnifiedRegistryService

        return UnifiedRegistryService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__.extend(getattr(filter_system.decorators, "__all__", []))  # type: ignore
