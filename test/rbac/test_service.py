"""
RBACService 单元测试
"""

import pytest
from ncatbot.core.service.builtin.rbac import RBACService
from pathlib import Path


class TestRBACServiceInit:
    """初始化测试"""

    def test_default_storage_path(self):
        """测试默认存储路径"""
        service = RBACService()
        assert service._storage_path is not None
        assert str(service._storage_path) == str(Path("data/rbac.json"))

    def test_custom_storage_path(self, temp_storage_path):
        """测试自定义存储路径"""
        service = RBACService(storage_path=str(temp_storage_path))
        assert str(service._storage_path) == str(temp_storage_path)

    def test_no_storage_path(self):
        """测试无存储路径"""
        service = RBACService(storage_path=None)
        assert service._storage_path is None

    def test_default_role(self):
        """测试默认角色配置"""
        service = RBACService(storage_path=None, default_role="member")
        assert service._default_role == "member"

    def test_case_sensitive(self):
        """测试大小写敏感配置"""
        service = RBACService(storage_path=None, case_sensitive=False)
        assert service._case_sensitive is False


class TestPermissionManagement:
    """权限路径管理测试"""

    def test_add_permission(self, rbac_service):
        """测试添加权限"""
        rbac_service.add_permission("plugin.admin.kick")
        assert rbac_service.permission_exists("plugin.admin.kick")

    def test_add_duplicate_permission(self, rbac_service):
        """测试添加重复权限（不报错）"""
        rbac_service.add_permission("plugin.admin.kick")
        rbac_service.add_permission("plugin.admin.kick")  # 不应报错
        assert rbac_service.permission_exists("plugin.admin.kick")

    def test_remove_permission(self, rbac_service):
        """测试删除权限"""
        rbac_service.add_permission("plugin.admin.kick")
        rbac_service.remove_permission("plugin.admin.kick")
        assert not rbac_service.permission_exists("plugin.admin.kick")

    def test_permission_exists(self, rbac_service):
        """测试检查权限存在"""
        assert not rbac_service.permission_exists("plugin.admin.kick")
        rbac_service.add_permission("plugin.admin.kick")
        assert rbac_service.permission_exists("plugin.admin.kick")


class TestRoleManagement:
    """角色管理测试"""

    def test_add_role(self, rbac_service):
        """测试添加角色"""
        rbac_service.add_role("admin")
        assert rbac_service.role_exists("admin")
        assert "admin" in rbac_service.roles

    def test_add_duplicate_role(self, rbac_service):
        """测试添加重复角色"""
        rbac_service.add_role("admin")

        with pytest.raises(ValueError, match="已存在"):
            rbac_service.add_role("admin")

    def test_add_duplicate_role_exist_ok(self, rbac_service):
        """测试添加重复角色（exist_ok=True）"""
        rbac_service.add_role("admin")
        rbac_service.add_role("admin", exist_ok=True)  # 不应报错
        assert rbac_service.role_exists("admin")

    def test_remove_role(self, rbac_service):
        """测试删除角色"""
        rbac_service.add_role("admin")
        rbac_service.remove_role("admin")
        assert not rbac_service.role_exists("admin")

    def test_remove_nonexistent_role(self, rbac_service):
        """测试删除不存在的角色"""
        with pytest.raises(ValueError, match="不存在"):
            rbac_service.remove_role("admin")

    def test_remove_role_cleans_inheritance(self, rbac_service):
        """测试删除角色时清理继承关系"""
        rbac_service.add_role("admin")
        rbac_service.add_role("moderator")
        rbac_service.set_role_inheritance("admin", "moderator")

        rbac_service.remove_role("moderator")

        # admin 不应该再继承 moderator
        assert "moderator" not in rbac_service._role_inheritance.get("admin", [])

    def test_remove_role_cleans_user_association(self, rbac_service):
        """测试删除角色时清理用户关联"""
        rbac_service.add_role("admin")
        rbac_service.add_user("user1")
        rbac_service.assign_role("user", "user1", "admin")

        rbac_service.remove_role("admin")

        # user1 不应该再有 admin 角色
        assert "admin" not in rbac_service._users["user1"]["roles"]


class TestRoleInheritance:
    """角色继承测试"""

    def test_set_inheritance(self, rbac_service):
        """测试设置角色继承"""
        rbac_service.add_role("admin")
        rbac_service.add_role("member")
        rbac_service.set_role_inheritance("admin", "member")

        assert "member" in rbac_service._role_inheritance.get("admin", [])

    def test_inheritance_nonexistent_role(self, rbac_service):
        """测试不存在的角色继承"""
        rbac_service.add_role("admin")

        with pytest.raises(ValueError, match="不存在"):
            rbac_service.set_role_inheritance("admin", "member")

    def test_inheritance_self(self, rbac_service):
        """测试角色不能继承自身"""
        rbac_service.add_role("admin")

        with pytest.raises(ValueError, match="不能继承自身"):
            rbac_service.set_role_inheritance("admin", "admin")

    def test_inheritance_cycle_detection(self, rbac_service):
        """测试循环继承检测"""
        rbac_service.add_role("admin")
        rbac_service.add_role("moderator")
        rbac_service.add_role("member")

        rbac_service.set_role_inheritance("admin", "moderator")
        rbac_service.set_role_inheritance("moderator", "member")

        with pytest.raises(ValueError, match="循环继承"):
            rbac_service.set_role_inheritance("member", "admin")


class TestUserManagement:
    """用户管理测试"""

    def test_add_user(self, rbac_service):
        """测试添加用户"""
        rbac_service.add_user("user1")
        assert rbac_service.user_exists("user1")
        assert "user1" in rbac_service.users

    def test_add_duplicate_user(self, rbac_service):
        """测试添加重复用户"""
        rbac_service.add_user("user1")

        with pytest.raises(ValueError, match="已存在"):
            rbac_service.add_user("user1")

    def test_add_duplicate_user_exist_ok(self, rbac_service):
        """测试添加重复用户（exist_ok=True）"""
        rbac_service.add_user("user1")
        rbac_service.add_user("user1", exist_ok=True)
        assert rbac_service.user_exists("user1")

    def test_add_user_with_default_role(self, rbac_service_with_default_role):
        """测试添加用户时分配默认角色"""
        rbac_service_with_default_role.add_user("user1")
        assert "member" in rbac_service_with_default_role._users["user1"]["roles"]

    def test_remove_user(self, rbac_service):
        """测试删除用户"""
        rbac_service.add_user("user1")
        rbac_service.remove_user("user1")
        assert not rbac_service.user_exists("user1")

    def test_remove_nonexistent_user(self, rbac_service):
        """测试删除不存在的用户"""
        with pytest.raises(ValueError, match="不存在"):
            rbac_service.remove_user("user1")

    def test_remove_user_cleans_role_users(self, rbac_service):
        """测试删除用户时清理角色用户映射"""
        rbac_service.add_role("admin")
        rbac_service.add_user("user1")
        rbac_service.assign_role("user", "user1", "admin")

        rbac_service.remove_user("user1")

        assert "user1" not in rbac_service._role_users["admin"]


class TestRoleAssignment:
    """角色分配测试"""

    def test_assign_role(self, rbac_service):
        """测试分配角色"""
        rbac_service.add_role("admin")
        rbac_service.add_user("user1")
        rbac_service.assign_role("user", "user1", "admin")

        assert "admin" in rbac_service._users["user1"]["roles"]
        assert "user1" in rbac_service._role_users["admin"]

    def test_assign_role_creates_user(self, rbac_service):
        """测试分配角色时自动创建用户"""
        rbac_service.add_role("admin")
        rbac_service.assign_role("user", "user1", "admin", create_user=True)

        assert rbac_service.user_exists("user1")
        assert "admin" in rbac_service._users["user1"]["roles"]

    def test_assign_role_no_create_user(self, rbac_service):
        """测试分配角色不创建用户"""
        rbac_service.add_role("admin")

        with pytest.raises(ValueError, match="不存在"):
            rbac_service.assign_role("user", "user1", "admin", create_user=False)

    def test_assign_nonexistent_role(self, rbac_service):
        """测试分配不存在的角色"""
        rbac_service.add_user("user1")

        with pytest.raises(ValueError, match="不存在"):
            rbac_service.assign_role("user", "user1", "admin")

    def test_unassign_role(self, rbac_service):
        """测试撤销角色"""
        rbac_service.add_role("admin")
        rbac_service.add_user("user1")
        rbac_service.assign_role("user", "user1", "admin")
        rbac_service.unassign_role("user", "user1", "admin")

        assert "admin" not in rbac_service._users["user1"]["roles"]
        assert "user1" not in rbac_service._role_users["admin"]


class TestPermissionGrant:
    """权限授予测试"""

    def test_grant_to_user(self, rbac_service):
        """测试授予用户权限"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick")

        assert "plugin.admin.kick" in rbac_service._users["user1"]["whitelist"]

    def test_grant_to_role(self, rbac_service):
        """测试授予角色权限"""
        rbac_service.add_role("admin")
        rbac_service.grant("role", "admin", "plugin.admin.kick")

        assert "plugin.admin.kick" in rbac_service._roles["admin"]["whitelist"]

    def test_grant_blacklist(self, rbac_service):
        """测试授予黑名单权限"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick", mode="black")

        assert "plugin.admin.kick" in rbac_service._users["user1"]["blacklist"]

    def test_grant_removes_opposite(self, rbac_service):
        """测试授予权限时移除相反列表"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick", mode="black")
        rbac_service.grant("user", "user1", "plugin.admin.kick", mode="white")

        assert "plugin.admin.kick" in rbac_service._users["user1"]["whitelist"]
        assert "plugin.admin.kick" not in rbac_service._users["user1"]["blacklist"]

    def test_grant_creates_permission(self, rbac_service):
        """测试授予权限时自动创建权限"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick", create_permission=True)

        assert rbac_service.permission_exists("plugin.admin.kick")

    def test_grant_no_create_permission(self, rbac_service):
        """测试授予权限不创建权限"""
        rbac_service.add_user("user1")

        with pytest.raises(ValueError, match="不存在"):
            rbac_service.grant(
                "user", "user1", "plugin.admin.kick", create_permission=False
            )

    def test_revoke_from_user(self, rbac_service):
        """测试撤销用户权限"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick")
        rbac_service.revoke("user", "user1", "plugin.admin.kick")

        assert "plugin.admin.kick" not in rbac_service._users["user1"]["whitelist"]

    def test_revoke_from_role(self, rbac_service):
        """测试撤销角色权限"""
        rbac_service.add_role("admin")
        rbac_service.grant("role", "admin", "plugin.admin.kick")
        rbac_service.revoke("role", "admin", "plugin.admin.kick")

        assert "plugin.admin.kick" not in rbac_service._roles["admin"]["whitelist"]


class TestPermissionCheck:
    """权限检查测试"""

    def test_check_whitelist(self, populated_rbac_service):
        """测试白名单权限检查"""
        # admin_user 有 admin 角色，有 plugin.admin.kick 权限
        assert populated_rbac_service.check("111111111", "plugin.admin.kick")

    def test_check_blacklist_priority(self, rbac_service):
        """测试黑名单优先"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick", mode="white")
        rbac_service.grant("user", "user1", "plugin.admin.kick", mode="black")

        # 黑名单优先，应该被拒绝
        # 注意：grant 会移除相反列表，所以这里只有黑名单
        assert not rbac_service.check("user1", "plugin.admin.kick")

    def test_check_no_permission(self, rbac_service):
        """测试无权限"""
        rbac_service.add_user("user1")
        assert not rbac_service.check("user1", "plugin.admin.kick")

    def test_check_inherited_permission(self, populated_rbac_service):
        """测试继承的权限"""
        # user2 有 moderator 角色，继承 member 角色
        # member 有 plugin.user.profile 权限
        assert populated_rbac_service.check("user2", "plugin.user.profile")

    def test_check_creates_user(self, rbac_service):
        """测试检查权限时自动创建用户"""
        assert not rbac_service.check("new_user", "plugin.admin.kick", create_user=True)
        assert rbac_service.user_exists("new_user")

    def test_check_no_create_user(self, rbac_service):
        """测试检查权限不创建用户"""
        with pytest.raises(ValueError, match="不存在"):
            rbac_service.check("new_user", "plugin.admin.kick", create_user=False)

    def test_check_matching_with_wildcard_in_whitelist(self, rbac_service):
        """测试白名单中的权限与目标匹配"""
        # 注意：权限路径本身不能包含通配符（Trie 不允许）
        # 但权限检查使用 PermissionPath.matches()，支持在检查时使用通配符匹配
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick")
        rbac_service.grant("user", "user1", "plugin.admin.ban")

        # 精确匹配
        assert rbac_service.check("user1", "plugin.admin.kick")
        assert rbac_service.check("user1", "plugin.admin.ban")
        assert not rbac_service.check("user1", "plugin.user.profile")


class TestCacheClearing:
    """缓存清理测试"""

    def test_cache_cleared_on_permission_change(self, rbac_service):
        """测试权限变更时清理缓存"""
        rbac_service.add_user("user1")
        rbac_service.grant("user", "user1", "plugin.admin.kick")

        # 首次检查，结果会被缓存
        assert rbac_service.check("user1", "plugin.admin.kick")

        # 撤销权限
        rbac_service.revoke("user", "user1", "plugin.admin.kick")

        # 缓存应该被清理，返回新结果
        assert not rbac_service.check("user1", "plugin.admin.kick")

    def test_cache_cleared_on_role_change(self, rbac_service):
        """测试角色变更时清理缓存"""
        rbac_service.add_role("admin")
        rbac_service.add_user("user1")
        rbac_service.grant("role", "admin", "plugin.admin.kick")
        rbac_service.assign_role("user", "user1", "admin")

        assert rbac_service.check("user1", "plugin.admin.kick")

        # 撤销角色
        rbac_service.unassign_role("user", "user1", "admin")

        assert not rbac_service.check("user1", "plugin.admin.kick")
