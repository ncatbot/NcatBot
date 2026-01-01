"""
内置服务

提供 NcatBot 核心功能所需的内置服务。
"""

from .message_router import MessageRouter
from .preupload import PreUploadService
from .rbac import RBACService, PermissionPath, PermissionTrie

__all__ = [
    "MessageRouter",
    "PreUploadService",
    "RBACService",
    "PermissionPath",
    "PermissionTrie",
]
