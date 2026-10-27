"""NapCat 查询 API 单元测试。

规范:
  NQ-01: get_forward_msg 使用 NapCat 规范的 message_id 参数
  NQ-02: get_forward_msg 保留超过 JavaScript 安全整数范围的完整 ID
  NQ-03: fetch_ptt_text 调用 NapCat 的 fetch_ptt_text 动作并解析 text
  NQ-04: fetch_ptt_text 在 data 为 null 时返回空文本而不抛异常
"""

from unittest.mock import AsyncMock

import pytest

from ncatbot.adapter.napcat.api.query import QueryAPIMixin


class _FakeQueryMixin(QueryAPIMixin):
    """为测试提供底层 API 调用方法。"""

    def __init__(self, data=None):
        self._call_data = AsyncMock(return_value=data)


class TestNapCatQueryAPI:
    """NapCat 查询 API 参数转换测试。"""

    @pytest.mark.parametrize(
        "message_id",
        [
            "7672696335120716277",
            7672696335120716277,
        ],
    )
    @pytest.mark.asyncio
    async def test_nq01_get_forward_msg_preserves_long_id(self, message_id):
        """NQ-01/02: 转发消息长 ID 始终通过字符串 message_id 原样传递。"""
        api = _FakeQueryMixin(data={"messages": []})

        result = await api.get_forward_msg(message_id)

        api._call_data.assert_awaited_once_with(
            "get_forward_msg",
            {"message_id": "7672696335120716277"},
        )
        assert result.messages == []

    @pytest.mark.parametrize(
        "message_id",
        [
            "7701320072321480080",
            7701320072321480080,
        ],
    )
    @pytest.mark.asyncio
    async def test_nq03_fetch_ptt_text_passes_string_id(self, message_id):
        """NQ-03: 语音转文字按字符串 message_id 调用 fetch_ptt_text 并解析 text。"""
        api = _FakeQueryMixin(data={"text": "你好世界"})

        result = await api.fetch_ptt_text(message_id)

        api._call_data.assert_awaited_once_with(
            "fetch_ptt_text",
            {"message_id": "7701320072321480080"},
        )
        assert result.text == "你好世界"

    @pytest.mark.asyncio
    async def test_nq04_fetch_ptt_text_null_data(self):
        """NQ-04: fetch_ptt_text 返回 data=null 时得到空文本而不是异常。"""
        api = _FakeQueryMixin(data=None)

        result = await api.fetch_ptt_text("7701320072321480080")

        assert result.text == ""
