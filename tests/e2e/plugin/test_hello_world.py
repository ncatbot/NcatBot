"""
01_hello_world 插件离线测试

规范:
  PL-01: 插件加载成功，on_load 执行
  PL-02: 群消息 "hello" → send_group_msg 调用
  PL-03: 私聊消息 "hello" → send_private_msg 调用
  PL-04: 插件卸载，on_close 执行
"""

import pytest

from ncatbot.testing import PluginTestHarness, group_message, private_message


PLUGIN_NAME = "hello_world_qq"


@pytest.fixture
def examples_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples" / "qq"


# ---- PL-01: 加载 ----


async def test_plugin_loads_successfully(examples_dir):
    """PL-01: hello_world 插件加载成功"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        assert PLUGIN_NAME in h.loaded_plugins
        plugin = h.get_plugin(PLUGIN_NAME)
        assert plugin is not None
        assert plugin.name == PLUGIN_NAME


# ---- PL-02: 群消息 hello ----


async def test_group_hello_reply(examples_dir):
    """PL-02: 群里发 'hello' → 调用 send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("hello", group_id="10001", user_id="99999"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


async def test_group_hi_reply(examples_dir):
    """PL-02b: 群里发 'hi' → event.reply() → send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("hi", group_id="10001", user_id="99999"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


# ---- PL-03: 私聊消息 hello ----


async def test_private_hello_reply(examples_dir):
    """PL-03: 私聊发 'hello' → event.reply() → send_private_msg"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(private_message("hello", user_id="99999"))
        await h.settle(0.1)

        assert h.api_called("send_private_msg")


# ---- PL-04: 卸载 ----


async def test_plugin_unloads(examples_dir):
    """PL-04: 插件卸载后从列表中移除"""
    harness = PluginTestHarness(plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir)
    await harness.start()
    assert PLUGIN_NAME in harness.loaded_plugins

    await harness.bot.plugin_loader.unload_plugin(PLUGIN_NAME)
    assert PLUGIN_NAME not in harness.loaded_plugins

    await harness.stop()
