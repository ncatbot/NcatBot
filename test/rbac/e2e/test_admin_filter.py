"""AdminFilter 与 RBAC 集成 E2E 测试

测试 AdminFilter 检查用户是否有 admin 或 root 角色。
"""

import pytest

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.utils.assets.literals import PermissionGroup

from .conftest import RBAC_PLUGIN_DIR, cleanup_modules


class TestAdminFilterWithRBAC:
    """测试 AdminFilter 与 RBAC 的联动"""

    @pytest.mark.asyncio
    async def test_admin_filter_allows_admin_role(self, rbac_service_for_e2e):
        """测试管理员角色可以通过 AdminFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 添加 admin 角色和用户
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("111111111")
        rbac.assign_role("user", "111111111", PermissionGroup.ADMIN.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 管理员执行 admin_cmd 应该成功
            await suite.inject_group_message(
                "/admin_cmd", user_id="111111111", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "admin_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_admin_filter_allows_root_role(self, rbac_service_for_e2e):
        """测试 root 角色也可以通过 AdminFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 添加 root 角色和用户
        rbac.add_role(PermissionGroup.ROOT.value, exist_ok=True)
        rbac.add_user("222222222")
        rbac.assign_role("user", "222222222", PermissionGroup.ROOT.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # root 用户执行 admin_cmd 应该成功
            await suite.inject_group_message(
                "/admin_cmd", user_id="222222222", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls = suite.get_api_calls("send_group_msg")
            msg = str(calls[-1].get("message", ""))
            assert "admin_cmd executed" in msg

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_admin_filter_denies_regular_user(self, rbac_service_for_e2e):
        """测试普通用户无法通过 AdminFilter"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 添加普通用户（没有 admin 或 root 角色）
        rbac.add_role(PermissionGroup.USER.value, exist_ok=True)
        rbac.add_user("333333333")

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 普通用户执行 admin_cmd 应该被过滤
            await suite.inject_group_message(
                "/admin_cmd", user_id="333333333", group_id="111222333"
            )

            # 应该没有回复（命令被过滤）
            calls = suite.get_api_calls("send_group_msg")
            for call in calls:
                msg = str(call.get("message", ""))
                assert "admin_cmd executed" not in msg

        cleanup_modules()


class TestDynamicRoleAssignment:
    """测试动态角色分配对过滤器的影响"""

    @pytest.mark.asyncio
    async def test_assign_role_enables_filter_passage(self, rbac_service_for_e2e):
        """测试分配角色后用户可以通过过滤器"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 初始没有 admin 角色的用户
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("444444444")

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 先尝试执行 admin_cmd（应该失败）
            await suite.inject_group_message(
                "/admin_cmd", user_id="444444444", group_id="111222333"
            )

            calls_before = suite.get_api_calls("send_group_msg")
            before_count = len(
                [
                    c
                    for c in calls_before
                    if "admin_cmd executed" in str(c.get("message", ""))
                ]
            )

            # 分配 admin 角色
            rbac.assign_role("user", "444444444", PermissionGroup.ADMIN.value)

            # 再次尝试执行 admin_cmd（应该成功）
            await suite.inject_group_message(
                "/admin_cmd", user_id="444444444", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls_after = suite.get_api_calls("send_group_msg")
            after_count = len(
                [
                    c
                    for c in calls_after
                    if "admin_cmd executed" in str(c.get("message", ""))
                ]
            )

            # 分配角色后应该多一次成功的回复
            assert after_count > before_count

        cleanup_modules()

    @pytest.mark.asyncio
    async def test_unassign_role_disables_filter_passage(self, rbac_service_for_e2e):
        """测试撤销角色后用户无法通过过滤器"""
        cleanup_modules()

        rbac = rbac_service_for_e2e

        # 初始有 admin 角色的用户
        rbac.add_role(PermissionGroup.ADMIN.value, exist_ok=True)
        rbac.add_user("444444444")
        rbac.assign_role("user", "444444444", PermissionGroup.ADMIN.value)

        async with E2ETestSuite() as suite:
            suite.index_plugin(str(RBAC_PLUGIN_DIR))
            await suite.register_plugin("rbac_test_plugin")

            # 先执行 admin_cmd（应该成功）
            await suite.inject_group_message(
                "/admin_cmd", user_id="444444444", group_id="111222333"
            )
            suite.assert_reply_sent()

            calls_before = suite.get_api_calls("send_group_msg")
            before_count = len(
                [
                    c
                    for c in calls_before
                    if "admin_cmd executed" in str(c.get("message", ""))
                ]
            )
            assert before_count >= 1

            # 撤销 admin 角色
            rbac.unassign_role("user", "444444444", PermissionGroup.ADMIN.value)

            # 再次尝试执行 admin_cmd（应该失败）
            await suite.inject_group_message(
                "/admin_cmd", user_id="444444444", group_id="111222333"
            )

            calls_after = suite.get_api_calls("send_group_msg")
            after_count = len(
                [
                    c
                    for c in calls_after
                    if "admin_cmd executed" in str(c.get("message", ""))
                ]
            )

            # 撤销角色后执行次数应该不变
            assert after_count == before_count

        cleanup_modules()
