"""
RBAC 服务

提供基于角色的访问控制功能，作为内置服务运行。
"""

from pathlib import Path
from typing import Dict, List, Literal, Optional, Set

from ncatbot.service.base import BaseService
from .trie import PermissionTrie
from .storage import (
    save_rbac_data,
    load_rbac_data,
    serialize_rbac_state,
    deserialize_rbac_state,
)
from .permission_checker import PermissionChecker
from .permission_assigner import PermissionAssigner
from .entity_manager import EntityManager
from ncatbot.utils import get_log

LOG = get_log("RBAC")


class RBACService(BaseService):
    """
    RBAC (Role-Based Access Control) 服务

    提供用户、角色、权限的管理功能：
    - 权限路径管理（支持通配符）
    - 角色管理（支持继承）
    - 用户权限分配（白名单/黑名单）
    - 权限检查（黑名单优先）
    """

    name = "rbac"
    description = "基于角色的访问控制服务"

    DEFAULT_STORAGE_PATH = "data/rbac.json"

    def __init__(
        self,
        storage_path: Optional[str] = DEFAULT_STORAGE_PATH,
        default_role: Optional[str] = None,
        case_sensitive: bool = True,
        **config,
    ):
        super().__init__(**config)
        self._storage_path = Path(storage_path) if storage_path else None
        self._default_role = default_role
        self._case_sensitive = case_sensitive

        self._permissions = PermissionTrie(case_sensitive)
        self._roles: Dict[str, Dict] = {}
        self._users: Dict[str, Dict] = {}
        self._role_users: Dict[str, Set[str]] = {}
        self._role_inheritance: Dict[str, List[str]] = {}

        self._permission_checker = PermissionChecker(self)
        self._permission_assigner = PermissionAssigner(self)
        self._entity_manager = EntityManager(self)

    # === 属性 ===

    @property
    def users(self) -> Dict[str, Dict]:
        return self._users

    @property
    def roles(self) -> Dict[str, Dict]:
        return self._roles

    # === 生命周期 ===

    async def on_load(self) -> None:
        if self._storage_path:
            data = load_rbac_data(self._storage_path)
            if data:
                self._restore_state(data)
                LOG.info(f"RBAC 数据已从 {self._storage_path} 加载")

        if self._default_role:
            self.add_role(self._default_role, exist_ok=True)

        LOG.info("RBAC 服务已加载")

    async def on_close(self) -> None:
        if self._storage_path:
            self.save()
        LOG.info("RBAC 服务已关闭")

    # === 持久化 ===

    def save(self, path: Optional[Path] = None) -> None:
        target = path or self._storage_path
        if not target:
            raise ValueError("未指定存储路径")

        data = serialize_rbac_state(
            users=self._users,
            roles=self._roles,
            role_users=self._role_users,
            role_inheritance=self._role_inheritance,
            permissions_trie=self._permissions.to_dict(),
            case_sensitive=self._case_sensitive,
            default_role=self._default_role,
        )
        save_rbac_data(target, data)
        LOG.debug(f"RBAC 数据已保存到 {target}")

    def _restore_state(self, data: Dict) -> None:
        state = deserialize_rbac_state(data)
        self._case_sensitive = state["case_sensitive"]
        self._default_role = state["default_role"]
        self._roles = state["roles"]
        self._users = state["users"]
        self._role_users = state["role_users"]
        self._role_inheritance = state["role_inheritance"]
        self._permissions.from_dict(state["permissions"])
        self._clear_cache()

    # === 权限路径管理 ===

    def add_permission(self, path: str) -> None:
        return self._entity_manager.add_permission(path)

    def remove_permission(self, path: str) -> None:
        return self._entity_manager.remove_permission(path)

    def permission_exists(self, path: str) -> bool:
        return self._entity_manager.permission_exists(path)

    # === 角色管理 ===

    def add_role(self, role: str, exist_ok: bool = False) -> None:
        return self._entity_manager.add_role(role, exist_ok)

    def remove_role(self, role: str) -> None:
        return self._entity_manager.remove_role(role)

    def role_exists(self, role: str) -> bool:
        return self._entity_manager.role_exists(role)

    def set_role_inheritance(self, role: str, parent: str) -> None:
        return self._entity_manager.set_role_inheritance(role, parent)

    # === 用户管理 ===

    def add_user(self, user: str, exist_ok: bool = False) -> None:
        return self._entity_manager.add_user(user, exist_ok)

    def remove_user(self, user: str) -> None:
        return self._entity_manager.remove_user(user)

    def user_exists(self, user: str) -> bool:
        return self._entity_manager.user_exists(user)

    def user_has_role(self, user: str, role: str, create_user: bool = True) -> bool:
        return self._entity_manager.user_has_role(user, role, create_user)

    def assign_role(
        self,
        target_type: Literal["user"],
        user: str,
        role: str,
        create_user: bool = True,
    ) -> None:
        if target_type != "user":
            raise ValueError("assign_role 只支持 user 类型")
        return self._entity_manager.assign_role(user, role, create_user)

    def unassign_role(
        self,
        target_type: Literal["user"],
        user: str,
        role: str,
    ) -> None:
        if target_type != "user":
            raise ValueError("unassign_role 只支持 user 类型")
        return self._entity_manager.unassign_role(user, role)

    # === 权限分配 ===

    def grant(
        self,
        target_type: Literal["user", "role"],
        target: str,
        permission: str,
        mode: Literal["white", "black"] = "white",
        create_permission: bool = True,
    ) -> None:
        return self._permission_assigner.grant(
            target_type, target, permission, mode, create_permission
        )

    def revoke(
        self,
        target_type: Literal["user", "role"],
        target: str,
        permission: str,
    ) -> None:
        return self._permission_assigner.revoke(target_type, target, permission)

    # === 权限检查 ===

    def check(self, user: str, permission: str, create_user: bool = True) -> bool:
        return self._permission_checker.check(user, permission, create_user)

    def _get_effective_permissions(self, user: str) -> Dict[str, frozenset]:
        return self._permission_checker._get_effective_permissions(user)

    def _clear_cache(self) -> None:
        self._permission_checker.clear_cache()
