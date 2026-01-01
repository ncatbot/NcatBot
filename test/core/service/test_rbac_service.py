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
import asyncio
from pathlib import Path

from ncatbot.core.service.builtin.rbac import RBACService, PermissionPath, PermissionTrie


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
        rbac_service.assign_role("user", "admin_user", "admin")
        
        # 管理员应该有基础权限（继承）和管理权限
        assert rbac_service.check("admin_user", "basic.read")
        assert rbac_service.check("admin_user", "admin.write")
    
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

class TestDynamicPermissionManagement:
    """动态权限管理测试"""
    
    def test_grant_revoke_permission(self, rbac_service):
        """测试授予和撤销权限"""
        rbac_service.add_permission("plugin.test.action")
        rbac_service.add_user("user1")
        
        # 授予权限
        rbac_service.grant("user", "user1", "plugin.test.action")
        assert rbac_service.check("user1", "plugin.test.action")
        
        # 撤销权限
        rbac_service.revoke("user", "user1", "plugin.test.action")
        assert not rbac_service.check("user1", "plugin.test.action")
    
    def test_add_remove_role(self, rbac_service):
        """测试添加和移除角色"""
        rbac_service.add_permission("role.perm")
        rbac_service.add_role("temp_role")
        rbac_service.grant("role", "temp_role", "role.perm")
        
        # 添加角色
        rbac_service.assign_role("user", "user1", "temp_role")
        assert rbac_service.check("user1", "role.perm")
        
        # 移除角色
        rbac_service.unassign_role("user", "user1", "temp_role")
        assert not rbac_service.check("user1", "role.perm")


# =============================================================================
# 持久化测试
# =============================================================================

class TestRBACPersistence:
    """RBAC 持久化测试"""
    
    def test_save_and_load(self, temp_rbac_file):
        """测试保存和加载"""
        # 创建并配置服务
        service1 = RBACService(storage_path=temp_rbac_file, default_role="user")
        service1.add_role("user")  # 必须先创建默认角色
        service1.add_permission("plugin.test.action")
        service1.add_role("tester")
        service1.grant("role", "tester", "plugin.test.action")
        service1.assign_role("user", "user1", "tester")
        
        # 保存
        service1.save()
        
        # 加载到新实例
        service2 = RBACService(storage_path=temp_rbac_file)
        from ncatbot.core.service.builtin.rbac.storage import load_rbac_data
        data = load_rbac_data(Path(temp_rbac_file))
        if data:
            service2._restore_state(data)
        
        # 验证权限保持一致
        assert service2.check("user1", "plugin.test.action")
    
    def test_load_preserves_inheritance(self, temp_rbac_file):
        """测试加载保留继承关系"""
        service1 = RBACService(storage_path=temp_rbac_file, default_role="base")  # 使用 base 作为默认角色
        service1.add_role("base")
        service1.add_role("derived")
        service1.add_permission("base.perm")
        service1.grant("role", "base", "base.perm")
        service1.set_role_inheritance("derived", "base")
        service1.assign_role("user", "user1", "derived")
        
        # 保存
        service1.save()
        
        # 加载到新实例
        service2 = RBACService(storage_path=temp_rbac_file)
        from ncatbot.core.service.builtin.rbac.storage import load_rbac_data
        data = load_rbac_data(Path(temp_rbac_file))
        if data:
            service2._restore_state(data)
        
        # 继承的权限应该保留
        assert service2.check("user1", "base.perm")


# =============================================================================
# 边界条件测试
# =============================================================================

class TestRBACEdgeCases:
    """边界条件测试"""
    
    def test_non_existent_permission_path_raises_error(self, rbac_service):
        """测试不存在的权限路径抛出错误（禁用自动创建）"""
        # 先确保用户存在
        rbac_service.add_user("user1")
        
        with pytest.raises(ValueError, match="权限.*不存在"):
            rbac_service.grant("user", "user1", "ghost.permission", create_permission=False)
    
    def test_duplicate_role_raises_error(self, rbac_service):
        """测试重复添加角色抛出错误"""
        rbac_service.add_role("role1")
        
        with pytest.raises(ValueError, match="已存在"):
            rbac_service.add_role("role1")
    
    def test_auto_create_user_on_check(self, rbac_service):
        """测试检查权限时自动创建用户"""
        rbac_service.add_permission("test.perm")
        
        # 检查一个不存在的用户，应该自动创建
        result = rbac_service.check("auto_user", "test.perm")
        assert not result  # 没有权限
        
        # 用户现在应该存在
        assert "auto_user" in rbac_service.users


# =============================================================================
# 多用户多角色场景测试
# =============================================================================

class TestMultiUserMultiRole:
    """多用户多角色场景测试"""
    
    def test_multiple_users_same_role(self, rbac_service):
        """测试多个用户共享角色"""
        rbac_service.add_permission("shared.action")
        rbac_service.add_role("shared_role")
        rbac_service.grant("role", "shared_role", "shared.action")
        
        for i in range(5):
            rbac_service.assign_role("user", f"user{i}", "shared_role")
        
        for i in range(5):
            assert rbac_service.check(f"user{i}", "shared.action")
    
    def test_user_multiple_roles(self, rbac_service):
        """测试用户拥有多个角色"""
        rbac_service.add_permission("role1.perm")
        rbac_service.add_permission("role2.perm")
        rbac_service.add_permission("role3.perm")
        
        rbac_service.add_role("role1")
        rbac_service.add_role("role2")
        rbac_service.add_role("role3")
        
        rbac_service.grant("role", "role1", "role1.perm")
        rbac_service.grant("role", "role2", "role2.perm")
        rbac_service.grant("role", "role3", "role3.perm")
        
        rbac_service.assign_role("user", "multi_role_user", "role1")
        rbac_service.assign_role("user", "multi_role_user", "role2")
        rbac_service.assign_role("user", "multi_role_user", "role3")
        
        assert rbac_service.check("multi_role_user", "role1.perm")
        assert rbac_service.check("multi_role_user", "role2.perm")
        assert rbac_service.check("multi_role_user", "role3.perm")
    
    def test_complex_inheritance_chain(self, rbac_service):
        """测试复杂的继承链"""
        # 创建继承链: root -> admin -> moderator -> user_role
        rbac_service.add_role("user_role")
        rbac_service.add_role("moderator")
        rbac_service.add_role("admin")
        rbac_service.add_role("root")
        
        rbac_service.add_permission("user.read")
        rbac_service.add_permission("mod.ban")
        rbac_service.add_permission("admin.config")
        rbac_service.add_permission("root.all")
        
        rbac_service.grant("role", "user_role", "user.read")
        rbac_service.grant("role", "moderator", "mod.ban")
        rbac_service.grant("role", "admin", "admin.config")
        rbac_service.grant("role", "root", "root.all")
        
        rbac_service.set_role_inheritance("moderator", "user_role")
        rbac_service.set_role_inheritance("admin", "moderator")
        rbac_service.set_role_inheritance("root", "admin")
        
        rbac_service.assign_role("user", "root_user", "root")
        
        # root 用户应该拥有所有权限
        assert rbac_service.check("root_user", "user.read")
        assert rbac_service.check("root_user", "mod.ban")
        assert rbac_service.check("root_user", "admin.config")
        assert rbac_service.check("root_user", "root.all")


# =============================================================================
# Service 生命周期测试
# =============================================================================

class TestRBACServiceLifecycle:
    """服务生命周期测试"""
    
    @pytest.mark.asyncio
    async def test_on_load_without_file(self, temp_rbac_file):
        """测试无数据文件时的加载"""
        # 删除临时文件
        if os.path.exists(temp_rbac_file):
            os.unlink(temp_rbac_file)
        
        service = RBACService(storage_path=temp_rbac_file)
        await service.on_load()
        
        # 应该正常工作，只是没有加载数据
        assert service.roles == {}
    
    @pytest.mark.asyncio
    async def test_on_close_saves_data(self, temp_rbac_file):
        """测试关闭时保存数据"""
        service = RBACService(storage_path=temp_rbac_file)
        service.add_role("test_role")
        service.add_permission("test.perm")
        
        await service.on_close()
        
        # 数据应该被保存
        assert os.path.exists(temp_rbac_file)
        
        # 加载并验证
        service2 = RBACService(storage_path=temp_rbac_file)
        await service2.on_load()
        assert "test_role" in service2.roles
