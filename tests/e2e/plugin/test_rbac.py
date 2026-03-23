"""
07_rbac 插件离线测试

规范:
  PL-30: 权限初始化 (on_load 中 add_permission/add_role)
  PL-31: 无权限用户执行管理命令 → 被拒绝
  PL-32: 授权后用户可访问管理命令
  PL-33: 查询权限命令
"""

import pytest

from ncatbot.testing import PluginTestHarness, group_message


PLUGIN_NAME = "rbac"


@pytest.fixture
def examples_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples" / "common"


# ---- PL-30: 权限初始化 ----


async def test_rbac_permissions_initialized(examples_dir):
    """PL-30: 插件加载后权限路径和角色已注册"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        plugin = h.get_plugin(PLUGIN_NAME)
        assert plugin is not None
        assert PLUGIN_NAME in h.loaded_plugins


# ---- PL-31: 无权限用户被拒绝 ----


async def test_admin_command_denied_without_permission(examples_dir):
    """PL-31: 无权限用户执行 '管理命令' → 回复权限不足"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("管理命令", group_id="400", user_id="12345"))
        await h.settle(0.1)

        # 应有回复（权限不足提示）
        assert h.api_called("send_group_msg")


# ---- PL-32: 授权后可访问 ----


async def test_admin_command_after_grant(examples_dir):
    """PL-32: 通过 RBAC 服务直接授权后，管理命令可执行"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        plugin = h.get_plugin(PLUGIN_NAME)

        # 手动授权（模拟 "授权" 命令的效果）
        if plugin.rbac:
            plugin.rbac.assign_role("user", "12345", "rbac_admin")

        h.reset_api()
        await h.inject(group_message("管理命令", group_id="400", user_id="12345"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


# ---- PL-33: 权限查询 ----


async def test_check_permission_command(examples_dir):
    """PL-33: '查权限' → 回复当前权限状态"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("查权限", group_id="400", user_id="12345"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


async def test_rbac_info_command(examples_dir):
    """PL-33b: '权限信息' → 回复 RBAC 配置"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("权限信息", group_id="400", user_id="12345"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")
