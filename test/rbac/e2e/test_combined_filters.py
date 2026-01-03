"""组合过滤器与 RBAC 集成 E2E 测试

测试多种过滤器组合（AdminFilter + GroupFilter 等）与 RBAC 的配合。
"""

import pytest

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils.assets.literals import PermissionGroup

from .conftest import RBAC_PLUGIN_DIR, cleanup_modules


class TestRoleInheritanceWithFilters:
    """测试角色继承对过滤器的影响"""

    @pytest.mark.asyncio
    async def test_inherited_admin_role(self, rbac_service_for_e2e):
        """测试继承的管理员角色可以通过 AdminFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 创建角色层次: custom_role 继承自 admin
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_role("custom_role", exist_ok=True)
        rbac.set_role_inheritance("custom_role", PermissionGroup.ADMIN.value)

        # 用户只有 custom_role
        rbac.add_user("777777777")
        rbac.assign_role("user", "777777777", "custom_role")

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 应该可以执行 admin_cmd（因为继承了 admin 角色）
            await suite.inject_group_message(
                "/admin_cmd", user_id="777777777", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "admin_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_inherited_root_role(self, rbac_service_for_e2e):
        """测试继承的 root 角色可以通过 RootFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 创建角色层次: super_admin 继承自 root
        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_role("super_admin", exist_ok=True)
        rbac.set_role_inheritance("super_admin", PermissionGroup.ROOT.value)

        rbac.add_user("555555555")
        rbac.assign_role("user", "555555555", "super_admin")

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 应该可以执行 root_cmd（因为继承了 root 角色）
            await suite.inject_group_message(
                "/root_cmd", user_id="555555555", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "root_cmd executed" in msg

        cleanup_modules()


class TestCombinedFiltersWithRBAC:
    """测试组合过滤器与 RBAC 的联动"""

    @pytest.mark.asyncio
    async def test_admin_and_group_filter(self, rbac_service_for_e2e):
        """测试 AdminFilter + GroupFilter 组合"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("111111111")
        rbac.assign_role("user", "111111111", PermissionGroup.ADMIN.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 群聊中的管理员应该可以执行
            await suite.inject_group_message(
                "/group_admin_cmd", user_id="111111111", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "group_admin_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_admin_in_private_fails_group_filter(self, rbac_service_for_e2e):
        """测试管理员在私聊中无法通过 GroupFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("111111111")
        rbac.assign_role("user", "111111111", PermissionGroup.ADMIN.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 私聊中执行 group_admin_cmd 应该失败（不满足 GroupFilter）
            await suite.inject_private_message("/group_admin_cmd", user_id="111111111")

            # 检查没有执行成功的回复
            calls = suite.get_api_calls("send_private_msg")
            for call in calls:
                msg = str(call.get("message", ""))
                assert "group_admin_cmd executed" not in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_root_and_private_filter(self, rbac_service_for_e2e):
        """测试 RootFilter + PrivateFilter 组合"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_user("222222222")
        rbac.assign_role("user", "222222222", PermissionGroup.ROOT.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 私聊中的 root 应该可以执行
            await suite.inject_private_message("/private_root_cmd", user_id="222222222")
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_private_msg")
            msg = str(calls[-1].get("message", ""))
            assert "private_root_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_root_in_group_fails_private_filter(self, rbac_service_for_e2e):
        """测试 root 在群聊中无法通过 PrivateFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_user("222222222")
        rbac.assign_role("user", "222222222", PermissionGroup.ROOT.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 群聊中执行 private_root_cmd 应该失败
            await suite.inject_group_message(
                "/private_root_cmd", user_id="222222222", group_id="111222333"
            )

            calls = suite.get_api_calls("send_group_msg")
            for call in calls:
                msg = str(call.get("message", ""))
                assert "private_root_cmd executed" not in msg

        cleanup_modules()


class TestPublicCommandsWithRBAC:
    """测试无权限要求的命令"""

    @pytest.mark.asyncio
    async def test_public_command_no_rbac(self, rbac_service_for_e2e):
        """测试公开命令不需要 RBAC 权限"""
        cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 任何用户都应该可以执行 public_cmd
            await suite.inject_group_message(
                "/public_cmd", user_id="19260817", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "public_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_group_filter_only_no_rbac(self, rbac_service_for_e2e):
        """测试只有 GroupFilter 的命令"""
        cleanup_modules()

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 群聊中任何用户都应该可以执行
            await suite.inject_group_message(
                "/group_cmd", user_id="19260817", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "group_cmd executed" in msg

        cleanup_modules()


class TestUserHasRoleMethod:
    """测试 user_has_role 方法"""

    def test_user_has_role_direct(self, rbac_service_for_e2e):
        """测试直接分配的角色"""
        rbac = rbac_service_for_e2e

        rbac.add_role("test_role")
        rbac.add_user("user1")
        rbac.assign_role("user", "user1", "test_role")

        assert rbac.user_has_role("user1", "test_role") is True
        assert rbac.user_has_role("user1", "other_role") is False

    def test_user_has_role_inherited(self, rbac_service_for_e2e):
        """测试继承的角色"""
        rbac = rbac_service_for_e2e

        rbac.add_role("parent_role")
        rbac.add_role("child_role")
        rbac.set_role_inheritance("child_role", "parent_role")

        rbac.add_user("user1")
        rbac.assign_role("user", "user1", "child_role")

        # 用户有 child_role 和继承的 parent_role
        assert rbac.user_has_role("user1", "child_role") is True
        assert rbac.user_has_role("user1", "parent_role") is True
        assert rbac.user_has_role("user1", "other_role") is False

    def test_user_has_role_creates_user(self, rbac_service_for_e2e):
        """测试 create_user 参数"""
        rbac = rbac_service_for_e2e

        rbac.add_role("test_role")

        # 用户不存在，create_user=True 时应该创建用户
        assert rbac.user_has_role("new_user", "test_role", create_user=True) is False
        assert rbac.user_exists("new_user") is True

        # 用户不存在，create_user=False 时不创建
        assert (
            rbac.user_has_role("another_user", "test_role", create_user=False) is False
        )
        assert rbac.user_exists("another_user") is False
