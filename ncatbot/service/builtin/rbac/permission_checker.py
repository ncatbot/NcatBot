"""
RBAC 权限检查和缓存管理模块
"""

from functools import lru_cache
from typing import Dict
from .path import PermissionPath


class PermissionChecker:
    """权限检查逻辑的抽象"""

    def __init__(self, service):
        self.service = service

    def check(self, user: str, permission: str, create_user: bool = True) -> bool:
        """
        检查用户是否有权限

        规则：黑名单 > 白名单 > 默认拒绝
        """
        if not self.service.user_exists(user):
            if create_user:
                self.service.add_user(user)
            else:
                raise ValueError(f"用户 {user} 不存在")

        perms = self._get_effective_permissions(user)
        ppath = PermissionPath(permission)

        for black in perms["blacklist"]:
            if PermissionPath(black).matches(ppath.raw):
                return False

        for white in perms["whitelist"]:
            if PermissionPath(white).matches(ppath.raw):
                return True

        return False

    @lru_cache(maxsize=256)
    def _get_effective_permissions(self, user: str) -> Dict[str, frozenset]:
        """获取用户的有效权限集（带缓存）"""
        if user not in self.service._users:
            return {"whitelist": frozenset(), "blacklist": frozenset()}

        whitelist = set(self.service._users[user]["whitelist"])
        blacklist = set(self.service._users[user]["blacklist"])

        all_roles = set()

        def collect_roles(role: str):
            if role in all_roles:
                return
            all_roles.add(role)
            for parent in self.service._role_inheritance.get(role, []):
                collect_roles(parent)

        for role in self.service._users[user]["roles"]:
            collect_roles(role)

        for role in all_roles:
            if role in self.service._roles:
                whitelist.update(self.service._roles[role]["whitelist"])
                blacklist.update(self.service._roles[role]["blacklist"])

        return {"whitelist": frozenset(whitelist), "blacklist": frozenset(blacklist)}

    def clear_cache(self) -> None:
        """清除缓存"""
        self._get_effective_permissions.cache_clear()
