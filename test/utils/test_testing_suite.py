"""
测试套件集成测试

验证 E2ETestSuite 和相关测试工具是否正常工作。
"""

import pytest

from ncatbot.utils.testing import E2ETestSuite, EventFactory


class TestTestSuite:
    """E2ETestSuite 测试"""

    @pytest.mark.asyncio
    async def test_suite_setup_teardown(self):
        """测试 E2ETestSuite 的 setup 和 teardown"""
        suite = E2ETestSuite()
        client = await suite.setup()

        assert client is not None
        assert suite.mock_server is not None

        await suite.teardown()

    @pytest.mark.asyncio
    async def test_suite_async_context_manager(self):
        """测试 E2ETestSuite 作为异步上下文管理器"""
        async with E2ETestSuite() as suite:
            assert suite.client is not None

    @pytest.mark.asyncio
    async def test_api_call_recording(self):
        """测试 API 调用记录"""
        async with E2ETestSuite() as suite:
            # 直接调用 API
            await suite.api.send_group_text(group_id="123", text="test")

            # 验证调用被记录
            suite.assert_api_called("send_group_msg")
            calls = suite.get_api_calls("send_group_msg")
            assert len(calls) == 1
            assert calls[0]["group_id"] == "123"

    @pytest.mark.asyncio
    async def test_helper_send_group_message(self):
        """测试 E2ETestSuite 发送群消息"""
        async with E2ETestSuite() as suite:
            await suite.inject_group_message("/test command")
            # 事件应该被处理（虽然没有插件处理，但不应该报错）


class TestEventFactory:
    """EventFactory 测试"""

    def test_create_group_message(self):
        """测试创建群消息事件"""
        event = EventFactory.create_group_message(
            message="hello world",
            group_id="123456",
            user_id="654321",
        )
        # GroupMessageEvent 使用 pydantic 模型
        assert str(event.group_id) == "123456"
        assert str(event.user_id) == "654321"
        assert event.raw_message == "hello world"

    def test_create_private_message(self):
        """测试创建私聊消息事件"""
        event = EventFactory.create_private_message(
            message="hello",
            user_id="654321",
        )
        assert str(event.user_id) == "654321"
        assert event.raw_message == "hello"

    def test_create_notice_event(self):
        """测试创建通知事件"""
        event = EventFactory.create_notice_event(
            notice_type="group_increase",
            user_id="654321",
            group_id="123456",
        )
        # NoticeEvent 的 notice_type 可能是枚举或字符串
        assert (
            str(event.notice_type) == "group_increase"
            or event.notice_type.value == "group_increase"
        )


class TestMockServer:
    """MockServer 测试"""

    @pytest.mark.asyncio
    async def test_call_history(self):
        """测试调用历史记录"""
        async with E2ETestSuite() as suite:
            await suite.api.send_group_text(group_id="123", text="test")
            history = suite.get_api_calls()
            assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_assert_called(self):
        """测试断言方法"""
        async with E2ETestSuite() as suite:
            await suite.api.get_login_info()
            suite.assert_api_called("get_login_info")
            suite.assert_api_not_called("send_group_msg")

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """测试清空历史"""
        async with E2ETestSuite() as suite:
            await suite.api.send_group_text(group_id="123", text="test")
            assert len(suite.get_api_calls()) >= 1
            suite.clear_call_history()
            assert len(suite.get_api_calls()) == 0
