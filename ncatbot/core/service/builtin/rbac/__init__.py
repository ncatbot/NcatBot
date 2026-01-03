"""
RBAC (Role-Based Access Control) 服务

提供基于角色的访问控制功能。
"""

from .service import RBACService
from .path import PermissionPath
from .trie import PermissionTrie

__all__ = [
    "RBACService",
    "PermissionPath",
    "PermissionTrie",
]
