"""
10_multi_step_dialog 插件离线测试

规范:
  PL-40: 完整注册流程 (名字 → 年龄 → 确认 → 存储)
  PL-41: 超时退出
  PL-42: 用户取消 ("取消" 关键词)
  PL-43: data 持久化验证
"""

import pytest

from ncatbot.testing import PluginTestHarness, group_message


PLUGIN_NAME = "multi_step_dialog"
GROUP_ID = "500"
USER_ID = "67890"


@pytest.fixture
def examples_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples" / "common"


# ---- PL-40: 完整注册流程 ----


async def test_full_registration_flow(examples_dir):
    """PL-40: 注册 → 输入名字 → 输入年龄 → 确认 → 保存"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=examples_dir
    ) as h:
        # 触发注册
        await h.inject(group_message("注册", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复要求输入名字"

        # 输入名字
        h.reset_api()
        await h.inject(group_message("张三", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复要求输入年龄"

        # 输入年龄
        h.reset_api()
        await h.inject(group_message("25", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复要求确认"

        # 确认
        h.reset_api()
        await h.inject(group_message("确认", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        assert h.api_called("send_group_msg"), "应回复注册成功"


# ---- PL-42: 用户取消 ----


async def test_registration_cancel(examples_dir):
    """PL-42: 注册过程中输入 '取消' → 退出"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=examples_dir
    ) as h:
        await h.inject(group_message("注册", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        h.reset_api()
        await h.inject(group_message("取消", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg"), "应回复注册已取消"


# ---- PL-43: data 持久化 ----


async def test_data_persistence_after_registration(examples_dir):
    """PL-43: 完整注册后 data 中应有用户信息"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=examples_dir
    ) as h:
        # 完整注册流程
        await h.inject(group_message("注册", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        await h.inject(group_message("李四", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        await h.inject(group_message("30", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        await h.inject(group_message("确认", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        # 验证 plugin.data 中有用户数据
        plugin = h.get_plugin(PLUGIN_NAME)
        users = plugin.data.get("users", {})
        assert USER_ID in users, f"用户 {USER_ID} 应在 data.users 中"
        assert users[USER_ID]["name"] == "李四"
        assert users[USER_ID]["age"] == 30


# ---- PL-40b: 查看信息 ----


async def test_my_info_after_registration(examples_dir):
    """注册后发 '我的信息' → 回复注册数据"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugin_dir=examples_dir
    ) as h:
        # 完整注册
        await h.inject(group_message("注册", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        await h.inject(group_message("王五", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        await h.inject(group_message("20", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        await h.inject(group_message("确认", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        # 查看信息
        h.reset_api()
        await h.inject(group_message("我的信息", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg"), "应回复用户注册信息"
