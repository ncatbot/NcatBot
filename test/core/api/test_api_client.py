"""
API 模块单元测试

测试 APIResponse、MockAPIClient、BotAPI.from_client 等核心组件。
"""

import pytest
from ncatbot.core.api.client import APIResponse, MockAPIClient, IAPIClient
from ncatbot.core.api.api import BotAPI


class TestAPIResponse:
    """APIResponse 数据类测试"""

    def test_from_dict_success(self):
        """测试成功响应的解析"""
        data = {
            "retcode": 0,
            "message": "ok",
            "data": {"user_id": 12345, "nickname": "test"},
        }
        response = APIResponse.from_dict(data)

        assert response.retcode == 0
        assert response.message == "ok"
        assert response.data == {"user_id": 12345, "nickname": "test"}
        assert response.raw == data
        assert response.is_success is True
        assert bool(response) is True

    def test_from_dict_error(self):
        """测试错误响应的解析"""
        data = {
            "retcode": 100,
            "message": "参数错误",
            "data": None,
        }
        response = APIResponse.from_dict(data)

        assert response.retcode == 100
        assert response.message == "参数错误"
        assert response.data is None
        assert response.is_success is False
        assert bool(response) is False

    def test_from_dict_missing_fields(self):
        """测试缺少字段时的默认值"""
        data = {}
        response = APIResponse.from_dict(data)

        assert response.retcode == -1
        assert response.message == ""
        assert response.data is None

    def test_from_dict_partial_fields(self):
        """测试部分字段缺失"""
        data = {"retcode": 0}
        response = APIResponse.from_dict(data)

        assert response.retcode == 0
        assert response.message == ""
        assert response.data is None


class TestMockAPIClient:
    """MockAPIClient 测试工具测试"""

    @pytest.fixture
    def client(self):
        return MockAPIClient()

    @pytest.mark.asyncio
    async def test_default_response(self, client):
        """测试默认响应"""
        response = await client.request("/get_login_info")

        assert response.retcode == 0
        assert response.message == "ok"

    @pytest.mark.asyncio
    async def test_set_response(self, client):
        """测试设置特定端点响应"""
        custom_response = APIResponse(
            retcode=0,
            message="success",
            data={"user_id": 99999},
        )
        client.set_response("/get_login_info", custom_response)

        response = await client.request("/get_login_info")

        assert response.data == {"user_id": 99999}

    @pytest.mark.asyncio
    async def test_request_history(self, client):
        """测试请求历史记录"""
        await client.request("/endpoint1", {"param1": "value1"})
        await client.request("/endpoint2", {"param2": "value2"})

        history = client.get_request_history()

        assert len(history) == 2
        assert history[0] == {"endpoint": "/endpoint1", "params": {"param1": "value1"}}
        assert history[1] == {"endpoint": "/endpoint2", "params": {"param2": "value2"}}

    @pytest.mark.asyncio
    async def test_clear_history(self, client):
        """测试清除历史记录"""
        await client.request("/test")
        client.clear_history()

        assert len(client.get_request_history()) == 0

    @pytest.mark.asyncio
    async def test_set_default_response(self, client):
        """测试设置默认响应"""
        new_default = APIResponse(retcode=999, message="custom default")
        client.set_default_response(new_default)

        response = await client.request("/unknown_endpoint")

        assert response.retcode == 999
        assert response.message == "custom default"


class TestBotAPIFactory:
    """BotAPI 工厂方法测试"""

    @pytest.fixture
    def mock_client(self):
        return MockAPIClient()

    def test_from_client_creates_instance(self, mock_client):
        """测试 from_client 正确创建实例"""
        api = BotAPI.from_client(mock_client)

        assert api is not None
        assert isinstance(api, BotAPI)
        assert api.client is mock_client

    def test_from_client_bypasses_init(self, mock_client):
        """测试 from_client 绑过 __init__"""
        # 如果调用了 __init__，会尝试包装 mock_client 为 CallbackAPIClient
        # 这会导致类型不匹配
        api = BotAPI.from_client(mock_client)

        # 验证 _client 直接是传入的 mock_client，而不是被包装
        assert api._client is mock_client
        assert isinstance(api._client, MockAPIClient)

    @pytest.mark.asyncio
    async def test_api_uses_injected_client(self, mock_client):
        """测试 API 方法使用注入的客户端"""
        # 注意：BotAPI 的方法通过 _request_raw 返回 response.raw
        # 所以需要设置完整的 raw 字典
        mock_client.set_response(
            "/get_login_info",
            APIResponse(
                retcode=0,
                message="ok",
                data={"user_id": "12345", "nickname": "TestBot"},
                raw={
                    "retcode": 0,
                    "message": "ok",
                    "data": {"user_id": "12345", "nickname": "TestBot"},
                },
            ),
        )

        api = BotAPI.from_client(mock_client)
        result = await api.get_login_info()

        # 验证请求被发送到 mock client
        history = mock_client.get_request_history()
        assert len(history) == 1
        assert history[0]["endpoint"] == "/get_login_info"

        # 验证返回数据
        assert result.user_id == "12345"
        assert result.nickname == "TestBot"


class TestIAPIClientProtocol:
    """IAPIClient 协议测试"""

    def test_mock_client_implements_protocol(self):
        """验证 MockAPIClient 实现了 IAPIClient 协议"""
        client = MockAPIClient()
        assert isinstance(client, IAPIClient)

    def test_protocol_has_request_method(self):
        """验证协议定义了 request 方法"""
        assert hasattr(IAPIClient, "request")
