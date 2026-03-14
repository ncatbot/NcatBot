"""
API 调用验证测试 — 验证 MockBotAPI 正确记录 API 调用
"""

import pytest

from ncatbot.adapter.mock import MockAdapter, MockBotAPI
from ncatbot.api.client import BotAPIClient


pytestmark = pytest.mark.asyncio


# ---- MockBotAPI 单元测试 ----


async def test_mock_api_records_calls():
    """MockBotAPI 正确记录 API 调用"""
    api = MockBotAPI()

    await api.send_group_msg("12345", [{"type": "text", "data": {"text": "hi"}}])

    assert api.called("send_group_msg")
    assert api.call_count("send_group_msg") == 1

    call = api.last_call("send_group_msg")
    assert call.args == ("12345", [{"type": "text", "data": {"text": "hi"}}])


async def test_mock_api_custom_response():
    """MockBotAPI 返回预设的响应"""
    api = MockBotAPI()
    api.set_response("send_group_msg", {"message_id": "42"})

    result = await api.send_group_msg("12345", [])
    assert result == {"message_id": "42"}


async def test_mock_api_reset():
    """reset() 清空调用记录"""
    api = MockBotAPI()

    await api.send_group_msg("12345", [])
    assert api.call_count("send_group_msg") == 1

    api.reset()
    assert api.call_count("send_group_msg") == 0
    assert not api.called("send_group_msg")


async def test_mock_api_multiple_actions():
    """多种 API 调用互不干扰"""
    api = MockBotAPI()

    await api.send_group_msg("12345", [])
    await api.send_private_msg("99999", [])
    await api.delete_msg("1001")

    assert api.call_count("send_group_msg") == 1
    assert api.call_count("send_private_msg") == 1
    assert api.call_count("delete_msg") == 1
    assert len(api.calls) == 3


# ---- BotAPIClient + MockBotAPI 集成 ----


async def test_bot_api_client_wraps_mock():
    """BotAPIClient 包装 MockBotAPI 后仍正确记录"""
    mock = MockBotAPI()
    mock.set_response("send_group_msg", {"message_id": "99"})

    client = BotAPIClient(mock)
    result = await client.send_group_msg("12345", [])

    assert result == {"message_id": "99"}
    assert mock.called("send_group_msg")


# ---- MockAdapter 单元测试 ----


async def test_mock_adapter_lifecycle():
    """MockAdapter 生命周期方法正常工作"""
    adapter = MockAdapter()

    assert not adapter.connected
    await adapter.setup()
    await adapter.connect()
    assert adapter.connected

    await adapter.disconnect()
    assert not adapter.connected


async def test_mock_adapter_inject_without_callback():
    """未设置回调时 inject_event 抛出 RuntimeError"""
    adapter = MockAdapter()
    await adapter.connect()

    from ncatbot.testing import factory

    with pytest.raises(RuntimeError, match="事件回调未设置"):
        await adapter.inject_event(factory.group_message("test"))
