"""
RBAC 服务单元测试

测试 RBACService 的完整功能，包括：
- 用户/角色权限分配
- 权限检查
- 角色继承
- 黑白名单优先级
- 持久化
"""

import pytest
import tempfile
import os

from ncatbot.core.service.builtin.rbac import (
    RBACService,
    PermissionPath,
    PermissionTrie,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rbac_service():
    """创建新的 RBAC 服务实例"""
    service = RBACService(default_role="user")
    # 必须先创建默认角色
    service.add_role("user")
    return service


@pytest.fixture
def temp_rbac_file():
    """创建临时文件用于持久化测试"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# =============================================================================
# PermissionPath 单元测试
# =============================================================================


class TestPermissionPath:
    """权限路径测试"""

    def test_parse_simple_path(self):
        """测试解析简单路径"""
        path = PermissionPath("plugin.admin.kick")
        assert path.parts == ("plugin", "admin", "kick")

    def test_parse_wildcard_path(self):
        """测试解析通配符路径"""
        path = PermissionPath("plugin.*.read")
        assert path.parts == ("plugin", "*", "read")

    def test_match_exact(self):
        """测试精确匹配"""
        pattern = PermissionPath("plugin.admin.kick")
        assert pattern.matches("plugin.admin.kick")
        assert not pattern.matches("plugin.admin.ban")

    def test_match_wildcard(self):
        """测试通配符匹配"""
        pattern = PermissionPath("plugin.*.read")
        assert pattern.matches("plugin.admin.read")
        assert pattern.matches("plugin.user.read")
        assert not pattern.matches("plugin.admin.write")

    def test_match_double_wildcard(self):
        """测试双通配符匹配"""
        pattern = PermissionPath("plugin.**")
        assert pattern.matches("plugin.admin")
        assert pattern.matches("plugin.admin.kick")
        assert pattern.matches("plugin.admin.user.delete")
        assert not pattern.matches("other.admin")

    def test_str_representation(self):
        """测试字符串表示"""
        path = PermissionPath("plugin.admin.kick")
        assert str(path) == "plugin.admin.kick"


# =============================================================================
# PermissionTrie 单元测试
# =============================================================================


class TestPermissionTrie:
    """权限 Trie 测试"""

    def test_add_and_exists(self):
        """测试添加和检查存在"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        assert trie.exists("plugin.admin.kick")
        assert not trie.exists("plugin.admin.ban")

    def test_remove(self):
        """测试移除"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        assert trie.exists("plugin.admin.kick")
        trie.remove("plugin.admin.kick")
        assert not trie.exists("plugin.admin.kick")

    def test_list_all(self):
        """测试列出所有权限"""
        trie = PermissionTrie()
        trie.add("plugin.admin.kick")
        trie.add("plugin.admin.ban")
        trie.add("plugin.user.read")

        all_perms = trie.list_all()
        assert len(all_perms) == 3
        assert "plugin.admin.kick" in all_perms
        assert "plugin.admin.ban" in all_perms
        assert "plugin.user.read" in all_perms


# =============================================================================
# 基础权限管理测试
# =============================================================================


class TestRBACBasicIntegration:
    """基础 RBAC 集成测试"""

    def test_register_and_check_permission(self, rbac_service):
        """测试注册权限并检查"""
        # 添加权限路径
        rbac_service.add_permission("plugin.greeter.send")

        # 添加用户
        rbac_service.add_user("user1")

        # 授予权限给用户
        rbac_service.grant("user", "user1", "plugin.greeter.send")

        # 检查权限
        assert rbac_service.check("user1", "plugin.greeter.send")

    def test_user_without_permission_denied(self, rbac_service):
        """测试用户没有权限时被拒绝"""
        rbac_service.add_permission("plugin.admin.kick")

        # 检查一个不存在的用户（会自动创建并使用默认角色）
        assert not rbac_service.check("user1", "plugin.admin.kick")

    def test_role_based_permission(self, rbac_service):
        """测试基于角色的权限"""
        # 添加权限和角色
        rbac_service.add_permission("plugin.admin.kick")
        rbac_service.add_role("moderator")

        # 给角色分配权限
        rbac_service.grant("role", "moderator", "plugin.admin.kick")

        # 将角色分配给用户
        rbac_service.assign_role("user", "mod_user", "moderator")

        # 用户应该通过角色获得权限
        assert rbac_service.check("mod_user", "plugin.admin.kick")


# =============================================================================
# 角色继承测试
# =============================================================================


class TestPermissionInheritance:
    """权限继承测试"""

    def test_role_inheritance(self, rbac_service):
        """测试角色继承"""
        # 创建基础角色和高级角色
        rbac_service.add_role("basic")
        rbac_service.add_role("admin")

        # 添加权限
        rbac_service.add_permission("basic.read")
        rbac_service.add_permission("admin.write")

        # 给基础角色分配基础权限
        rbac_service.grant("role", "basic", "basic.read")

        # 给管理员角色分配管理权限
        rbac_service.grant("role", "admin", "admin.write")

        # 设置继承：admin 继承 basic
        rbac_service.set_role_inheritance("admin", "basic")

        # 创建管理员用户并分配角色
        rbac_service.assign_role("user", "111111111", "admin")

        # 管理员应该有基础权限（继承）和管理权限
        assert rbac_service.check("111111111", "basic.read")
        assert rbac_service.check("111111111", "admin.write")

    def test_circular_inheritance_rejected(self, rbac_service):
        """测试循环继承被拒绝"""
        rbac_service.add_role("role_a")
        rbac_service.add_role("role_b")
        rbac_service.add_role("role_c")

        rbac_service.set_role_inheritance("role_a", "role_b")
        rbac_service.set_role_inheritance("role_b", "role_c")

        # role_c -> role_a 会形成循环 (role_a -> role_b -> role_c -> role_a)
        with pytest.raises(ValueError, match="循环继承"):
            rbac_service.set_role_inheritance("role_c", "role_a")


# =============================================================================
# 黑名单测试
# =============================================================================


class TestBlacklistPermission:
    """黑名单权限测试"""

    def test_blacklist_overrides_whitelist(self, rbac_service):
        """测试黑名单覆盖白名单"""
        rbac_service.add_permission("plugin.danger.execute")
        rbac_service.add_user("user1")

        # 同时添加到白名单和黑名单
        rbac_service.grant("user", "user1", "plugin.danger.execute")
        rbac_service.grant("user", "user1", "plugin.danger.execute", mode="black")

        # 黑名单优先，应该被拒绝
        assert not rbac_service.check("user1", "plugin.danger.execute")

    def test_role_blacklist_overrides_role_whitelist(self, rbac_service):
        """测试角色黑名单覆盖角色白名单"""
        rbac_service.add_permission("action.dangerous")
        rbac_service.add_role("mixed_role")

        # 添加到角色的白名单和黑名单
        rbac_service.grant("role", "mixed_role", "action.dangerous")
        rbac_service.grant("role", "mixed_role", "action.dangerous", mode="black")

        # 分配角色给用户
        rbac_service.assign_role("user", "user1", "mixed_role")

        # 黑名单优先
        assert not rbac_service.check("user1", "action.dangerous")


# =============================================================================
# 动态权限管理测试
# =============================================================================
