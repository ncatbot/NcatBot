"""
RBAC 集成测试

测试完整生命周期、持久化、E2E 场景
"""

import pytest

from ncatbot.core.service.builtin.rbac import RBACService
from ncatbot.utils import run_coroutine


class TestLifecycle:
    """生命周期测试"""

    def test_load_empty_storage(self, temp_storage_path):
        """测试从空存储加载"""
        service = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service.on_load)

        assert service.users == {}
        assert service.roles == {}

    def test_load_with_default_role(self, temp_storage_path):
        """测试加载时创建默认角色"""
        service = RBACService(
            storage_path=str(temp_storage_path), default_role="member"
        )
        run_coroutine(service.on_load)

        assert service.role_exists("member")

    def test_save_on_close(self, temp_storage_path):
        """测试关闭时保存"""
        service = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service.on_load)

        service.add_role("admin")
        service.add_user("user1")
        service.assign_role("user", "user1", "admin")

        run_coroutine(service.on_close)

        # 验证文件已保存
        assert temp_storage_path.exists()

    def test_load_saved_data(self, temp_storage_path):
        """测试加载已保存的数据"""
        # 第一个服务实例：创建并保存数据
        service1 = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service1.on_load)

        service1.add_permission("plugin.admin.kick")
        service1.add_role("admin")
        service1.add_user("user1")
        service1.assign_role("user", "user1", "admin")
        service1.grant("user", "user1", "plugin.admin.kick")

        run_coroutine(service1.on_close)

        # 第二个服务实例：加载数据
        service2 = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service2.on_load)

        assert service2.role_exists("admin")
        assert service2.user_exists("user1")
        assert "admin" in service2._users["user1"]["roles"]
        assert service2.check("user1", "plugin.admin.kick")


class TestPersistence:
    """持久化测试"""

    def test_save_and_restore_complete_state(self, temp_storage_path):
        """测试保存和恢复完整状态"""
        service1 = RBACService(
            storage_path=str(temp_storage_path),
            default_role="member",
            case_sensitive=False,
        )
        run_coroutine(service1.on_load)

        # 创建复杂状态
        service1.add_permission("plugin.admin.kick")
        service1.add_permission("plugin.admin.ban")
        service1.add_permission("plugin.user.profile")

        service1.add_role("admin")
        service1.add_role("moderator")
        service1.set_role_inheritance("admin", "moderator")
        service1.set_role_inheritance("moderator", "member")

        service1.grant("role", "admin", "plugin.admin.kick")
        service1.grant("role", "admin", "plugin.admin.ban")
        service1.grant("role", "member", "plugin.user.profile")

        service1.add_user("user1")
        service1.add_user("user2")
        service1.assign_role("user", "user1", "admin")
        service1.assign_role("user", "user2", "moderator")

        # 添加用户级别的黑名单
        service1.grant("user", "user1", "plugin.admin.ban", mode="black")

        run_coroutine(service1.on_close)

        # 恢复状态
        service2 = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service2.on_load)

        # 验证配置
        assert service2._case_sensitive is False
        assert service2._default_role == "member"

        # 验证角色
        assert service2.role_exists("admin")
        assert service2.role_exists("moderator")
        assert service2.role_exists("member")

        # 验证继承
        assert "moderator" in service2._role_inheritance.get("admin", [])
        assert "member" in service2._role_inheritance.get("moderator", [])

        # 验证用户
        assert service2.user_exists("user1")
        assert service2.user_exists("user2")

        # 验证权限检查
        assert service2.check("user1", "plugin.admin.kick")
        assert not service2.check("user1", "plugin.admin.ban")  # 黑名单
        assert service2.check("user2", "plugin.user.profile")  # 继承

    def test_manual_save(self, temp_storage_path):
        """测试手动保存"""
        service = RBACService(storage_path=str(temp_storage_path))
        service.add_role("admin")

        service.save()

        assert temp_storage_path.exists()

    def test_save_to_different_path(self, temp_storage_path, tmp_path):
        """测试保存到不同路径"""
        service = RBACService(storage_path=str(temp_storage_path))
        service.add_role("admin")

        other_path = tmp_path / "other_rbac.json"
        service.save(other_path)

        assert other_path.exists()
        assert not temp_storage_path.exists()  # 原路径不应该有文件

    def test_save_without_path_error(self):
        """测试无路径保存报错"""
        service = RBACService(storage_path=None)
        service.add_role("admin")

        with pytest.raises(ValueError, match="未指定存储路径"):
            service.save()


class TestE2EScenarios:
    """端到端场景测试"""

    def test_typical_bot_permission_scenario(self, temp_storage_path):
        """测试典型的 Bot 权限场景"""
        service = RBACService(storage_path=str(temp_storage_path), default_role="user")
        run_coroutine(service.on_load)

        # 1. 设置权限结构
        # 命令权限
        service.add_permission("command.admin.kick")
        service.add_permission("command.admin.ban")
        service.add_permission("command.admin.mute")
        service.add_permission("command.mod.warn")
        service.add_permission("command.user.help")
        service.add_permission("command.user.info")

        # 2. 创建角色层级
        service.add_role("owner")
        service.add_role("admin")
        service.add_role("moderator")
        # user 角色已在 on_load 时创建

        service.set_role_inheritance("owner", "admin")
        service.set_role_inheritance("admin", "moderator")
        service.set_role_inheritance("moderator", "user")

        # 3. 分配角色权限
        service.grant("role", "owner", "command.**")  # owner 有所有权限
        service.grant("role", "admin", "command.admin.**")
        service.grant("role", "moderator", "command.mod.**")
        service.grant("role", "user", "command.user.**")

        # 4. 添加用户
        owner_id = "123456789"
        admin_id = "987654321"
        mod_id = "111222333"
        user_id = "444555666"

        service.add_user(owner_id)
        service.add_user(admin_id)
        service.add_user(mod_id)
        service.add_user(user_id)

        service.assign_role("user", owner_id, "owner")
        service.assign_role("user", admin_id, "admin")
        service.assign_role("user", mod_id, "moderator")
        # user_id 使用默认角色

        # 5. 验证权限
        # Owner 可以做任何事
        assert service.check(owner_id, "command.admin.kick")
        assert service.check(owner_id, "command.mod.warn")
        assert service.check(owner_id, "command.user.help")

        # Admin 可以管理员命令
        assert service.check(admin_id, "command.admin.kick")
        assert service.check(admin_id, "command.mod.warn")  # 继承
        assert service.check(admin_id, "command.user.help")  # 继承

        # Moderator 只能警告
        assert not service.check(mod_id, "command.admin.kick")
        assert service.check(mod_id, "command.mod.warn")
        assert service.check(mod_id, "command.user.help")  # 继承

        # 普通用户只能使用用户命令
        assert not service.check(user_id, "command.admin.kick")
        assert not service.check(user_id, "command.mod.warn")
        assert service.check(user_id, "command.user.help")

    def test_blacklist_override_scenario(self, temp_storage_path):
        """测试黑名单覆盖场景"""
        service = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service.on_load)

        # 设置基础结构
        service.add_permission("command.admin.ban")
        service.add_role("admin")
        service.grant("role", "admin", "command.admin.ban")

        # 管理员用户
        service.add_user("admin1")
        service.assign_role("user", "admin1", "admin")

        # 验证管理员有权限
        assert service.check("admin1", "command.admin.ban")

        # 临时禁用该管理员的 ban 权限（用户级别黑名单）
        service.grant("user", "admin1", "command.admin.ban", mode="black")

        # 即使有角色权限，黑名单优先
        assert not service.check("admin1", "command.admin.ban")

        # 移除黑名单恢复权限
        service.revoke("user", "admin1", "command.admin.ban")
        assert service.check("admin1", "command.admin.ban")

    def test_dynamic_permission_scenario(self, temp_storage_path):
        """测试动态权限场景"""
        service = RBACService(storage_path=str(temp_storage_path))
        run_coroutine(service.on_load)

        user_id = "12345"
        service.add_user(user_id)

        # 初始无权限
        assert not service.check(user_id, "plugin.feature.use")

        # 动态授予权限
        service.grant("user", user_id, "plugin.feature.use")
        assert service.check(user_id, "plugin.feature.use")

        # 动态撤销权限
        service.revoke("user", user_id, "plugin.feature.use")
        assert not service.check(user_id, "plugin.feature.use")

    def test_new_user_auto_registration(self, temp_storage_path):
        """测试新用户自动注册场景"""
        service = RBACService(storage_path=str(temp_storage_path), default_role="guest")
        run_coroutine(service.on_load)

        # 设置 guest 权限
        service.grant("role", "guest", "command.user.help")

        # 新用户首次检查权限时自动创建
        new_user = "new_user_123"
        result = service.check(new_user, "command.user.help", create_user=True)

        # 用户被创建并有默认角色权限
        assert service.user_exists(new_user)
        assert "guest" in service._users[new_user]["roles"]
        assert result is True


class TestConcurrentAccess:
    """并发访问测试"""

    def test_multiple_permission_checks(self, populated_rbac_service):
        """测试多次权限检查"""
        # 模拟多次快速检查
        for _ in range(100):
            assert populated_rbac_service.check("111111111", "plugin.admin.kick")
            assert not populated_rbac_service.check("user1", "plugin.admin.kick")

    def test_cache_effectiveness(self, populated_rbac_service):
        """测试缓存效果"""
        # 首次检查
        populated_rbac_service.check("111111111", "plugin.admin.kick")

        # 获取缓存信息
        cache_info = populated_rbac_service._get_effective_permissions.cache_info()
        assert cache_info.misses >= 1

        # 再次检查应该命中缓存
        populated_rbac_service.check("111111111", "plugin.admin.kick")
        new_cache_info = populated_rbac_service._get_effective_permissions.cache_info()
        assert new_cache_info.hits > cache_info.hits
