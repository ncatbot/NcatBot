"""
RBAC 服务

提供基于角色的访问控制功能，作为内置服务运行。
"""

from pathlib import Path
from typing import Dict, List, Literal, Optional, Set
from functools import lru_cache

from ...base import BaseService
from .path import PermissionPath
from .trie import PermissionTrie
from .storage import (
    save_rbac_data,
    load_rbac_data,
    serialize_rbac_state,
    deserialize_rbac_state,
)
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

    # 默认存储路径
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

        # 核心数据结构
        self._permissions = PermissionTrie(case_sensitive)
        self._roles: Dict[str, Dict] = {}  # {role: {whitelist: set, blacklist: set}}
        self._users: Dict[str, Dict] = {}  # {user: {whitelist, blacklist, roles}}
        self._role_users: Dict[str, Set[str]] = {}  # {role: {users}}
        self._role_inheritance: Dict[str, List[str]] = {}  # {role: [parent_roles]}

    # ==========================================================================
    # 属性
    # ==========================================================================

    @property
    def users(self) -> Dict[str, Dict]:
        """获取所有用户"""
        return self._users

    @property
    def roles(self) -> Dict[str, Dict]:
        """获取所有角色"""
        return self._roles

    # ==========================================================================
    # 生命周期
    # ==========================================================================

    async def on_load(self) -> None:
        """加载服务"""
        if self._storage_path:
            data = load_rbac_data(self._storage_path)
            if data:
                self._restore_state(data)
                LOG.info(f"RBAC 数据已从 {self._storage_path} 加载")

        # 确保默认角色存在
        if self._default_role:
            self.add_role(self._default_role, exist_ok=True)

        LOG.info("RBAC 服务已加载")

    async def on_close(self) -> None:
        """关闭服务"""
        if self._storage_path:
            self.save()
        LOG.info("RBAC 服务已关闭")

    # ==========================================================================
    # 持久化
    # ==========================================================================

    def save(self, path: Optional[Path] = None) -> None:
        """保存当前状态"""
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
        """从数据恢复状态"""
        state = deserialize_rbac_state(data)
        self._case_sensitive = state["case_sensitive"]
        self._default_role = state["default_role"]
        self._roles = state["roles"]
        self._users = state["users"]
        self._role_users = state["role_users"]
        self._role_inheritance = state["role_inheritance"]
        self._permissions.from_dict(state["permissions"])
        self._clear_cache()

    # ==========================================================================
    # 权限路径管理
    # ==========================================================================

    def add_permission(self, path: str) -> None:
        """添加权限路径"""
        if not self._permissions.exists(path, exact=True):
            self._permissions.add(path)
            self._clear_cache()

    def remove_permission(self, path: str) -> None:
        """删除权限路径"""
        self._permissions.remove(path)
        self._clear_cache()

    def permission_exists(self, path: str) -> bool:
        """检查权限路径是否存在"""
        return self._permissions.exists(path, exact=True)

    # ==========================================================================
    # 角色管理
    # ==========================================================================

    def add_role(self, role: str, exist_ok: bool = False) -> None:
        """添加角色"""
        if role in self._roles:
            if not exist_ok:
                raise ValueError(f"角色 {role} 已存在")
            return

        self._roles[role] = {"whitelist": set(), "blacklist": set()}
        self._role_users[role] = set()
        self._clear_cache()

    def remove_role(self, role: str) -> None:
        """删除角色"""
        if role not in self._roles:
            raise ValueError(f"角色 {role} 不存在")

        # 清理继承关系
        self._role_inheritance.pop(role, None)
        for parents in self._role_inheritance.values():
            if role in parents:
                parents.remove(role)

        # 清理用户关联
        for user in self._role_users.get(role, []):
            if user in self._users:
                self._users[user]["roles"].remove(role)

        del self._roles[role]
        del self._role_users[role]
        self._clear_cache()

    def role_exists(self, role: str) -> bool:
        """检查角色是否存在"""
        return role in self._roles

    def set_role_inheritance(self, role: str, parent: str) -> None:
        """设置角色继承"""
        if role not in self._roles:
            raise ValueError(f"角色 {role} 不存在")
        if parent not in self._roles:
            raise ValueError(f"父角色 {parent} 不存在")
        if role == parent:
            raise ValueError("角色不能继承自身")

        # 检查循环继承
        if self._would_create_cycle(role, parent):
            raise ValueError(f"检测到循环继承: {role} -> {parent}")

        if role not in self._role_inheritance:
            self._role_inheritance[role] = []

        if parent not in self._role_inheritance[role]:
            self._role_inheritance[role].append(parent)
            self._clear_cache()

    def _would_create_cycle(self, role: str, new_parent: str) -> bool:
        """检查是否会形成循环继承"""
        visited = set()

        def check(current: str) -> bool:
            if current == role:
                return True
            if current in visited:
                return False
            visited.add(current)
            for parent in self._role_inheritance.get(current, []):
                if check(parent):
                    return True
            return False

        return check(new_parent)

    # ==========================================================================
    # 用户管理
    # ==========================================================================

    def add_user(self, user: str, exist_ok: bool = False) -> None:
        """添加用户"""
        if user in self._users:
            if not exist_ok:
                raise ValueError(f"用户 {user} 已存在")
            return

        roles = [self._default_role] if self._default_role else []
        self._users[user] = {"whitelist": set(), "blacklist": set(), "roles": roles}

        # 添加到默认角色的用户列表
        if self._default_role and self._default_role in self._role_users:
            self._role_users[self._default_role].add(user)

        self._clear_cache()

    def remove_user(self, user: str) -> None:
        """删除用户"""
        if user not in self._users:
            raise ValueError(f"用户 {user} 不存在")

        # 从所有角色中移除
        for role in self._users[user]["roles"]:
            if role in self._role_users:
                self._role_users[role].discard(user)

        del self._users[user]
        self._clear_cache()

    def user_exists(self, user: str) -> bool:
        """检查用户是否存在"""
        return user in self._users

    def user_has_role(self, user: str, role: str, create_user: bool = True) -> bool:
        """
        检查用户是否拥有指定角色（包括继承的角色）

        Args:
            user: 用户 ID
            role: 角色名
            create_user: 用户不存在时是否自动创建

        Returns:
            用户是否拥有该角色
        """
        if not self.user_exists(user):
            if create_user:
                self.add_user(user)
            else:
                return False

        # 获取用户所有角色（包括继承的）
        all_roles = set()

        def collect_roles(r: str):
            if r in all_roles:
                return
            all_roles.add(r)
            for parent in self._role_inheritance.get(r, []):
                collect_roles(parent)

        for r in self._users[user]["roles"]:
            collect_roles(r)

        return role in all_roles

    def assign_role(
        self,
        target_type: Literal["user"],  # 现在只支持给用户分配角色
        user: str,
        role: str,
        create_user: bool = True,
    ) -> None:
        """为用户分配角色"""
        if not self.user_exists(user):
            if create_user:
                self.add_user(user)
            else:
                raise ValueError(f"用户 {user} 不存在")

        if not self.role_exists(role):
            raise ValueError(f"角色 {role} 不存在")

        if role not in self._users[user]["roles"]:
            self._users[user]["roles"].append(role)
            self._role_users[role].add(user)
            self._clear_cache()

    def unassign_role(
        self,
        target_type: Literal["user"],  # 现在只支持给用户撤销角色
        user: str,
        role: str,
    ) -> None:
        """撤销用户角色"""
        if user not in self._users:
            raise ValueError(f"用户 {user} 不存在")

        if role in self._users[user]["roles"]:
            self._users[user]["roles"].remove(role)
            self._role_users[role].discard(user)
            self._clear_cache()

    # ==========================================================================
    # 权限分配
    # ==========================================================================

    def grant(
        self,
        target_type: Literal["user", "role"],
        target: str,
        permission: str,
        mode: Literal["white", "black"] = "white",
        create_permission: bool = True,
    ) -> None:
        """
        授予权限

        Args:
            target_type: 目标类型 ("user" 或 "role")
            target: 用户名或角色名
            permission: 权限路径
            mode: white=白名单, black=黑名单
            create_permission: 权限不存在时是否自动创建
        """
        if not self.permission_exists(permission):
            if create_permission:
                self.add_permission(permission)
            else:
                raise ValueError(f"权限 {permission} 不存在")

        if target_type == "user":
            if target not in self._users:
                raise ValueError(f"用户 {target} 不存在")
            target_data = self._users[target]
        else:
            if target not in self._roles:
                raise ValueError(f"角色 {target} 不存在")
            target_data = self._roles[target]

        list_key = "whitelist" if mode == "white" else "blacklist"
        opposite_key = "blacklist" if mode == "white" else "whitelist"

        target_data[list_key].add(permission)
        target_data[opposite_key].discard(permission)  # 从相反列表移除
        self._clear_cache()

    def revoke(
        self,
        target_type: Literal["user", "role"],
        target: str,
        permission: str,
    ) -> None:
        """撤销权限"""
        if target_type == "user":
            if target not in self._users:
                raise ValueError(f"用户 {target} 不存在")
            target_data = self._users[target]
        else:
            if target not in self._roles:
                raise ValueError(f"角色 {target} 不存在")
            target_data = self._roles[target]

        target_data["whitelist"].discard(permission)
        target_data["blacklist"].discard(permission)
        self._clear_cache()

    # ==========================================================================
    # 权限检查
    # ==========================================================================

    def check(self, user: str, permission: str, create_user: bool = True) -> bool:
        """
        检查用户是否有权限

        规则：黑名单 > 白名单 > 默认拒绝
        """
        if not self.user_exists(user):
            if create_user:
                self.add_user(user)
            else:
                raise ValueError(f"用户 {user} 不存在")

        perms = self._get_effective_permissions(user)
        ppath = PermissionPath(permission)

        # 检查黑名单
        for black in perms["blacklist"]:
            if PermissionPath(black).matches(ppath.raw):
                return False

        # 检查白名单
        for white in perms["whitelist"]:
            if PermissionPath(white).matches(ppath.raw):
                return True

        return False

    @lru_cache(maxsize=256)
    def _get_effective_permissions(self, user: str) -> Dict[str, frozenset]:
        """获取用户的有效权限集（带缓存）"""
        if user not in self._users:
            return {"whitelist": frozenset(), "blacklist": frozenset()}

        whitelist = set(self._users[user]["whitelist"])
        blacklist = set(self._users[user]["blacklist"])

        # 收集所有角色（包括继承的）
        all_roles = set()

        def collect_roles(role: str):
            if role in all_roles:
                return
            all_roles.add(role)
            for parent in self._role_inheritance.get(role, []):
                collect_roles(parent)

        for role in self._users[user]["roles"]:
            collect_roles(role)

        # 合并角色权限
        for role in all_roles:
            if role in self._roles:
                whitelist.update(self._roles[role]["whitelist"])
                blacklist.update(self._roles[role]["blacklist"])

        return {"whitelist": frozenset(whitelist), "blacklist": frozenset(blacklist)}

    def _clear_cache(self) -> None:
        """清除缓存"""
        self._get_effective_permissions.cache_clear()
