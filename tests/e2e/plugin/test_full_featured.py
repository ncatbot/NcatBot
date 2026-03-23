"""
15_full_featured_bot 插件离线测试

规范:
  PL-50: 多功能同时加载
  PL-51: 签到/积分功能
  PL-52: Config/Data 读写
  PL-53: 帮助/关键词/配置 命令
"""

import pytest

from ncatbot.testing import PluginTestHarness, group_message


PLUGIN_NAME = "full_featured_bot_qq"
GROUP_ID = "600"
USER_ID = "11111"


@pytest.fixture
def examples_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples" / "qq"


# ---- PL-50: 插件加载 ----


async def test_full_featured_loads(examples_dir):
    """PL-50: full_featured_bot 插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        assert PLUGIN_NAME in h.loaded_plugins
        plugin = h.get_plugin(PLUGIN_NAME)
        assert plugin is not None


# ---- PL-51: 签到与积分 ----


async def test_sign_in(examples_dir):
    """PL-51: '签到' → 获取积分 → send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("签到", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")

        # 验证 data 中记录了积分
        plugin = h.get_plugin(PLUGIN_NAME)
        scores = plugin.data.get("scores", {})
        assert USER_ID in scores, "签到后应有积分记录"
        assert scores[USER_ID] > 0


async def test_sign_in_duplicate(examples_dir):
    """PL-51b: 同一天重复签到 → 提示已签到"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        # 第一次签到
        await h.inject(group_message("签到", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        h.reset_api()

        # 第二次签到
        await h.inject(group_message("签到", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg"), "应回复已签到提示"


async def test_score_query(examples_dir):
    """PL-51c: '积分' → 查看积分"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("积分", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


# ---- PL-52: Config/Data ----


async def test_config_initialized(examples_dir):
    """PL-52: 加载后 config 有默认值"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        plugin = h.get_plugin(PLUGIN_NAME)
        assert plugin.get_config("welcome_msg") is not None


async def test_data_initialized(examples_dir):
    """PL-52b: 加载后 data 有初始化结构"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        plugin = h.get_plugin(PLUGIN_NAME)
        assert "scores" in plugin.data
        assert "keywords" in plugin.data


# ---- PL-53: 帮助/关键词/配置 ----


async def test_help_command(examples_dir):
    """PL-53: '帮助' → 回复帮助文本"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("帮助", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


async def test_keyword_add_and_list(examples_dir):
    """PL-53b: 添加关键词 → 关键词列表"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        # 添加关键词
        await h.inject(
            group_message("添加关键词 你好=世界", group_id=GROUP_ID, user_id=USER_ID)
        )
        await h.settle(0.1)
        assert h.api_called("send_group_msg")

        # 验证 data
        plugin = h.get_plugin(PLUGIN_NAME)
        assert plugin.data.get("keywords", {}).get("你好") == "世界"

        h.reset_api()

        # 查看关键词列表
        await h.inject(group_message("关键词列表", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)
        assert h.api_called("send_group_msg")


async def test_view_config(examples_dir):
    """PL-53c: '查看配置' → 回复当前配置"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("查看配置", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


async def test_ranking(examples_dir):
    """排行榜命令（无数据时也应回复）"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("排行榜", group_id=GROUP_ID, user_id=USER_ID))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")
