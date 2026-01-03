"""
mixins.py 模块测试 - 测试 Mixin 功能
"""

import pytest
from typing import Any

from ncatbot.core.event.mixins import (
    MessageActionMixin,
    GroupAdminMixin,
    RequestActionMixin,
)


# 创建测试用的 Mock 事件类（需要有类型注解）
class MockGroupMessageEvent(MessageActionMixin):
    """模拟群消息事件"""

    message_type: str = "group"
    group_id: str = "123456"
    user_id: str = "789"
    message_id: str = "111"


class MockPrivateMessageEvent(MessageActionMixin):
    """模拟私聊消息事件"""

    message_type: str = "private"
    group_id: Any = None
    user_id: str = "123456"
    message_id: str = "111"


class MockUnknownTypeEvent(MessageActionMixin):
    """模拟未知类型事件"""

    message_type: str = "unknown"
    group_id: Any = None
    user_id: Any = None
    message_id: str = "111"


class MockGroupAdminEvent(GroupAdminMixin):
    """模拟群管理事件"""

    group_id: str = "123456"
    user_id: str = "789012"


class MockFriendRequestEvent(RequestActionMixin):
    """模拟好友请求事件"""

    request_type: str = "friend"
    flag: str = "friend_flag_123"
    sub_type: Any = None


class MockGroupRequestEvent(RequestActionMixin):
    """模拟群请求事件"""

    request_type: str = "group"
    flag: str = "group_flag_456"
    sub_type: str = "add"


class TestMessageActionMixin:
    """测试 MessageActionMixin"""

    @pytest.mark.asyncio
    async def test_reply_to_group_message(self, mock_api):
        """测试回复群消息"""
        event = MockGroupMessageEvent()
        event.bind_api(mock_api)

        await event.reply("hello group")

        assert mock_api.get_last_call()[0] == "post_group_msg"
        assert mock_api.get_last_call()[1] == "123456"  # group_id
        assert mock_api.get_last_call()[2] == "hello group"  # text

    @pytest.mark.asyncio
    async def test_reply_to_private_message(self, mock_api):
        """测试回复私聊消息"""
        event = MockPrivateMessageEvent()
        event.bind_api(mock_api)

        await event.reply("hello private")

        assert mock_api.get_last_call()[0] == "post_private_msg"
        assert mock_api.get_last_call()[1] == "123456"  # user_id
        assert mock_api.get_last_call()[2] == "hello private"  # text

    @pytest.mark.asyncio
    async def test_reply_with_kwargs(self, mock_api):
        """测试回复时传递额外参数"""
        event = MockGroupMessageEvent()
        event.bind_api(mock_api)

        await event.reply("hello", at_sender=True)

        call = mock_api.get_last_call()
        assert call[3].get("at_sender") is True

    @pytest.mark.asyncio
    async def test_reply_raises_for_unknown_type(self, mock_api):
        """测试回复未知消息类型时抛出异常"""
        event = MockUnknownTypeEvent()
        event.bind_api(mock_api)

        with pytest.raises(ValueError, match="Cannot reply"):
            await event.reply("hello")

    @pytest.mark.asyncio
    async def test_delete_message(self, mock_api):
        """测试删除消息"""
        event = MockGroupMessageEvent()
        event.message_id = "999888"
        event.bind_api(mock_api)

        await event.delete()

        assert mock_api.get_last_call()[0] == "delete_msg"
        assert mock_api.get_last_call()[1] == "999888"


class TestGroupAdminMixin:
    """测试 GroupAdminMixin"""

    @pytest.mark.asyncio
    async def test_kick_user(self, mock_api):
        """测试踢出用户"""
        event = MockGroupAdminEvent()
        event.bind_api(mock_api)

        await event.kick()

        call = mock_api.get_last_call()
        assert call[0] == "set_group_kick"
        assert call[1] == "123456"  # group_id
        assert call[2] == "789012"  # user_id
        assert call[3] is False  # reject_add_request default

    @pytest.mark.asyncio
    async def test_kick_user_with_reject(self, mock_api):
        """测试踢出用户并拒绝再次加入"""
        event = MockGroupAdminEvent()
        event.bind_api(mock_api)

        await event.kick(reject_add_request=True)

        call = mock_api.get_last_call()
        assert call[3] is True  # reject_add_request

    @pytest.mark.asyncio
    async def test_ban_user_default_duration(self, mock_api):
        """测试禁言用户（默认时长）"""
        event = MockGroupAdminEvent()
        event.bind_api(mock_api)

        await event.ban()

        call = mock_api.get_last_call()
        assert call[0] == "set_group_ban"
        assert call[1] == "123456"  # group_id
        assert call[2] == "789012"  # user_id
        assert call[3] == 30 * 60  # duration default (30 minutes)

    @pytest.mark.asyncio
    async def test_ban_user_custom_duration(self, mock_api):
        """测试禁言用户（自定义时长）"""
        event = MockGroupAdminEvent()
        event.bind_api(mock_api)

        await event.ban(duration=3600)  # 1 hour

        call = mock_api.get_last_call()
        assert call[3] == 3600


class TestRequestActionMixin:
    """测试 RequestActionMixin"""

    @pytest.mark.asyncio
    async def test_approve_friend_request(self, mock_api):
        """测试同意好友请求"""
        event = MockFriendRequestEvent()
        event.bind_api(mock_api)

        await event.approve()

        call = mock_api.get_last_call()
        assert call[0] == "set_friend_add_request"
        assert call[1] == "friend_flag_123"  # flag
        assert call[2] is True  # approve

    @pytest.mark.asyncio
    async def test_approve_friend_request_with_remark(self, mock_api):
        """测试同意好友请求并添加备注"""
        event = MockFriendRequestEvent()
        event.bind_api(mock_api)

        await event.approve(remark="测试备注")

        call = mock_api.get_last_call()
        assert call[3] == "测试备注"  # remark

    @pytest.mark.asyncio
    async def test_approve_group_request(self, mock_api):
        """测试同意入群请求"""
        event = MockGroupRequestEvent()
        event.bind_api(mock_api)

        await event.approve()

        call = mock_api.get_last_call()
        assert call[0] == "set_group_add_request"
        assert call[1] == "group_flag_456"  # flag
        assert call[2] == "add"  # sub_type
        assert call[3] is True  # approve

    @pytest.mark.asyncio
    async def test_reject_friend_request(self, mock_api):
        """测试拒绝好友请求"""
        event = MockFriendRequestEvent()
        event.bind_api(mock_api)

        await event.reject()

        call = mock_api.get_last_call()
        assert call[0] == "set_friend_add_request"
        assert call[1] == "friend_flag_123"  # flag
        assert call[2] is False  # approve

    @pytest.mark.asyncio
    async def test_reject_group_request_with_reason(self, mock_api):
        """测试拒绝入群请求并附带原因"""
        event = MockGroupRequestEvent()
        event.bind_api(mock_api)

        await event.reject(reason="不符合入群条件")

        call = mock_api.get_last_call()
        assert call[0] == "set_group_add_request"
        assert call[1] == "group_flag_456"  # flag
        assert call[2] == "add"  # sub_type
        assert call[3] is False  # approve
        assert call[4] == "不符合入群条件"  # reason
