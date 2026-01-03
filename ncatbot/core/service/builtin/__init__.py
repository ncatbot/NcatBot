"""
内置服务

提供 NcatBot 核心功能所需的内置服务。
"""

from .message_router import MessageRouter
from .preupload import PreUploadService
from .rbac import RBACService, PermissionPath, PermissionTrie
from .plugin_config import PluginConfigService, ConfigItem, PluginConfig
from .unified_registry import UnifiedRegistryService
from .file_watcher import FileWatcherService

__all__ = [
    "MessageRouter",
    "PreUploadService",
    "RBACService",
    "PermissionPath",
    "PermissionTrie",
    "PluginConfigService",
    "ConfigItem",
    "PluginConfig",
    "UnifiedRegistryService",
    "FileWatcherService",
]
