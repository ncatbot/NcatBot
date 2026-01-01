# -------------------------
# @Author       : Fish-LP fish.zh@outlook.com
# @Date         : 2025-03-21 18:06:59
# @LastEditors  : Fish-LP fish.zh@outlook.com
# @LastEditTime : 2025-08-04 14:24:40
# @Description  : 喵喵喵, 我还没想好怎么介绍文件喵
# @Copyright (c) 2025 by Fish-LP, Fcatbot使用许可协议
# -------------------------
from .base_plugin import BasePlugin
from .loader import PluginLoader
from .builtin_mixin import NcatBotPlugin
from .decorator import CompatibleHandler
from ncatbot.core import NcatBotEvent

# 统一注册模块
from .builtin_plugin.unified_registry import (
    filter_registry,
    command_registry,
    option,
    param,
    option_group,
)
# 过滤器系统：导入所有过滤器、装饰器和基础类
from .builtin_plugin.unified_registry.filter_system import *

# 动态构建 __all__
__all__ = [
    "BasePlugin", "PluginLoader",
    "NcatBotPlugin", "CompatibleHandler",
    "filter_registry", "command_registry", "option", "param", "option_group",
    
    "NcatBotEvent",
]

# 从 filter_system 扩展 __all__
from .builtin_plugin.unified_registry import filter_system
__all__.extend(getattr(filter_system, "__all__", [])) # type: ignore
