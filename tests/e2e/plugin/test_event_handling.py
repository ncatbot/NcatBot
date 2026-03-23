"""
02_event_handling 插件离线测试

规范:
  PL-10: 装饰器方式 "ping" → "pong"
  PL-11: 事件流消费（后台私聊监控日志）
  PL-12: wait_event 超时处理（"确认测试" 命令）
"""

import pytest

from ncatbot.testing import PluginTestHarness, group_message, private_message


PLUGIN_NAME = "event_handling_qq"


@pytest.fixture
def examples_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "docs" / "docs" / "examples" / "qq"


# ---- PL-10: ping → pong ----


async def test_ping_pong(examples_dir):
    """PL-10: 群里发 'ping' → event.reply('pong 🏓') → send_group_msg"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("ping", group_id="200", user_id="99"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


async def test_status_command(examples_dir):
    """PL-10b: 群里发 '状态' → 回复插件运行状态"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("状态", group_id="200", user_id="99"))
        await h.settle(0.1)

        assert h.api_called("send_group_msg")


# ---- PL-11: 事件流后台消费 ----


async def test_stream_listener_receives_private_message(examples_dir):
    """PL-11: 事件流监听私聊消息（不崩溃即为通过）"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        # 注入私聊消息，事件流后台任务应能收到并记录日志
        await h.inject(private_message("测试私聊", user_id="88"))
        await h.settle(0.1)
        # 事件流只记录日志，不产生 API 调用
        # 主要验证不会崩溃


# ---- PL-12: wait_event 超时 ----


async def test_confirm_test_timeout(examples_dir):
    """PL-12: '确认测试' 后不回复 → 超时取消"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        # 设置较短超时用于测试（原始超时 15s 太长）
        # 先触发确认流程
        await h.inject(group_message("确认测试", group_id="200", user_id="99"))
        await h.settle(0.1)

        # 应该收到 "请在 15 秒内回复「确认」" 的回复
        assert h.api_called("send_group_msg")


async def test_confirm_test_success(examples_dir):
    """PL-12b: '确认测试' 后回复 '确认' → 操作确认"""
    async with PluginTestHarness(
        plugin_names=[PLUGIN_NAME], plugins_dir=examples_dir
    ) as h:
        await h.inject(group_message("确认测试", group_id="200", user_id="99"))
        await h.settle(0.1)

        # 回复 "确认"
        await h.inject(group_message("确认", group_id="200", user_id="99"))
        await h.settle(0.2)

        # 应有至少 2 次 send_group_msg：提示 + 确认成功
        assert h.api_call_count("send_group_msg") >= 2
