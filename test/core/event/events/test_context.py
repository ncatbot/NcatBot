"""
context.py 模块测试 - 测试上下文和依赖注入
"""

import pytest

from ncatbot.core.event.context import IBotAPI, ContextMixin


class TestIBotAPI:
    """测试 IBotAPI 协议"""

    def test_protocol_methods_defined(self):
        """验证协议定义了必要的方法"""
        # IBotAPI 是一个 Protocol，检查其定义的方法
        expected_methods = [
            "post_group_msg",
            "post_private_msg",
            "delete_msg",
            "set_group_kick",
            "set_group_ban",
            "set_friend_add_request",
            "set_group_add_request",
        ]
        for method in expected_methods:
            assert hasattr(IBotAPI, method)


class TestContextMixin:
    """测试 ContextMixin 混入类"""

    def test_api_initially_none(self):
        """测试 API 初始为 None"""
        mixin = ContextMixin()
        assert mixin._api is None

    def test_bind_api(self, mock_api):
        """测试绑定 API"""
        mixin = ContextMixin()
        mixin.bind_api(mock_api)
        assert mixin._api is mock_api

    def test_api_property_returns_bound_api(self, mock_api):
        """测试 api 属性返回已绑定的 API"""
        mixin = ContextMixin()
        mixin.bind_api(mock_api)
        assert mixin.api is mock_api

    def test_api_property_raises_when_not_bound(self):
        """测试未绑定 API 时访问 api 属性抛出异常"""
        mixin = ContextMixin()
        with pytest.raises(RuntimeError, match="API context not initialized"):
            _ = mixin.api

    def test_rebind_api(self, mock_api):
        """测试重新绑定 API"""
        mixin = ContextMixin()

        # 第一次绑定
        first_api = mock_api
        mixin.bind_api(first_api)
        assert mixin.api is first_api

        # 第二次绑定（新的 API）
        from .conftest import MockBotAPI

        second_api = MockBotAPI()
        mixin.bind_api(second_api)
        assert mixin.api is second_api

    def test_context_mixin_is_pydantic_model(self):
        """测试 ContextMixin 是 Pydantic BaseModel"""
        from pydantic import BaseModel

        assert issubclass(ContextMixin, BaseModel)

    def test_api_is_private_attr(self):
        """测试 _api 是私有属性，不会被序列化"""
        mixin = ContextMixin()
        data = mixin.model_dump()
        assert "_api" not in data
        assert "api" not in data


class TestMockAPIProtocolCompliance:
    """测试 MockBotAPI 是否符合 IBotAPI 协议"""

    def test_mock_api_has_all_methods(self, mock_api):
        """验证 Mock API 实现了所有协议方法"""
        expected_methods = [
            "post_group_msg",
            "post_private_msg",
            "delete_msg",
            "set_group_kick",
            "set_group_ban",
            "set_friend_add_request",
            "set_group_add_request",
        ]
        for method in expected_methods:
            assert hasattr(mock_api, method)
            assert callable(getattr(mock_api, method))

    @pytest.mark.asyncio
    async def test_mock_api_post_group_msg(self, mock_api):
        """测试 Mock API 的 post_group_msg"""
        result = await mock_api.post_group_msg("123456", "hello")
        assert "message_id" in result
        assert mock_api.get_last_call()[0] == "post_group_msg"

    @pytest.mark.asyncio
    async def test_mock_api_post_private_msg(self, mock_api):
        """测试 Mock API 的 post_private_msg"""
        result = await mock_api.post_private_msg("123456", "hello")
        assert "message_id" in result
        assert mock_api.get_last_call()[0] == "post_private_msg"

    @pytest.mark.asyncio
    async def test_mock_api_records_calls(self, mock_api):
        """测试 Mock API 记录调用"""
        await mock_api.post_group_msg("111", "text1")
        await mock_api.post_private_msg("222", "text2")
        await mock_api.delete_msg("333")

        assert len(mock_api.calls) == 3
        assert mock_api.calls[0] == ("post_group_msg", "111", "text1", {})
        assert mock_api.calls[1] == ("post_private_msg", "222", "text2", {})
        assert mock_api.calls[2] == ("delete_msg", "333")

    @pytest.mark.asyncio
    async def test_mock_api_clear_calls(self, mock_api):
        """测试清空调用记录"""
        await mock_api.post_group_msg("123", "test")
        assert len(mock_api.calls) == 1

        mock_api.clear_calls()
        assert len(mock_api.calls) == 0
