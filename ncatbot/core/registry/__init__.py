"""
注册引擎（Registry Engine）

Core 层核心组件，负责命令/过滤器/事件处理器的统一管理。
从 UnifiedRegistryService 提升而来，不再继承 BaseService。

由 BotClient 直接持有和管理。
"""

from .engine import RegistryEngine

# 导出全局注册表（从原 unified_registry 位置）
from ncatbot.core.service.builtin.unified_registry.filter_system import filter_registry
from ncatbot.core.service.builtin.unified_registry.filter_system.event_registry import (
    event_registry,
)
from ncatbot.core.service.builtin.unified_registry.command_system.registry.registry import (
    command_registry,
)

# 导出装饰器 API
from ncatbot.core.service.builtin.unified_registry.filter_system.decorators import *  # noqa: F401,F403
from ncatbot.core.service.builtin.unified_registry.command_system.registry import (
    option,
    param,
    option_group,
)

__all__ = [
    "RegistryEngine",
    "command_registry",
    "filter_registry",
    "event_registry",
    "option",
    "param",
    "option_group",
]
