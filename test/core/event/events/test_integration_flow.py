"""
事件处理流程集成测试
"""

import pytest

from ncatbot.core import EventParser
from ncatbot.core import (
    PrivateMessageEvent,
    GroupMessageEvent,
)


class TestMessageEventReplyFlow:
    """测试消息事件的回复流程"""

    @pytest.mark.asyncio
    async def test_group_message_reply(self, mock_api):
        """测试群消息回复"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "2009890763",
            "user_id": "3051561876",
            "group_id": "701784439",
            "message": [{"type": "text", "data": {"text": "/hello"}}],
            "raw_message": "/hello",
            "font": 14,
            "sender": {"user_id": "3051561876", "nickname": "测试", "role": "owner"},
        }

        event = EventParser.parse(data, mock_api)
        assert isinstance(event, GroupMessageEvent)

        await event.reply("Hello World!")

        call = mock_api.get_last_call()
        assert call[0] == "post_group_msg"
        assert call[1] == "701784439"  # group_id
        assert call[2] == "Hello World!"  # text

    @pytest.mark.asyncio
    async def test_private_message_reply(self, mock_api):
        """测试私聊消息回复"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "400060831",
            "user_id": "3051561876",
            "message": [{"type": "text", "data": {"text": "hi"}}],
            "raw_message": "hi",
            "font": 14,
            "sender": {"user_id": "3051561876", "nickname": "测试"},
        }

        event = EventParser.parse(data, mock_api)
        assert isinstance(event, PrivateMessageEvent)

        await event.reply("Hi there!")

        call = mock_api.get_last_call()
        assert call[0] == "post_private_msg"
        assert call[1] == "3051561876"  # user_id
        assert call[2] == "Hi there!"

    @pytest.mark.asyncio
    async def test_reply_with_extra_kwargs(self, mock_api):
        """测试带额外参数的回复"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "123",
            "user_id": "456",
            "group_id": "789",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        await event.reply("Hello", at_sender=True)

        call = mock_api.get_last_call()
        assert call[3].get("at_sender") is True


class TestGroupAdminOperationsFlow:
    """测试群管理操作流程"""

    @pytest.mark.asyncio
    async def test_delete_message(self, mock_api):
        """测试删除消息"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "msg_to_delete",
            "user_id": "违规用户123",
            "group_id": "701784439",
            "message": [],
            "raw_message": "违规内容",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        await event.delete()

        call = mock_api.get_last_call()
        assert call[0] == "delete_msg"
        assert call[1] == "msg_to_delete"

    @pytest.mark.asyncio
    async def test_ban_user(self, mock_api):
        """测试禁言用户"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "123",
            "user_id": "违规用户123",
            "group_id": "701784439",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        await event.ban(duration=600)

        call = mock_api.get_last_call()
        assert call[0] == "set_group_ban"
        assert call[1] == "701784439"  # group_id
        assert call[2] == "违规用户123"  # user_id
        assert call[3] == 600  # duration

    @pytest.mark.asyncio
    async def test_kick_user(self, mock_api):
        """测试踢出用户"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "123",
            "user_id": "违规用户123",
            "group_id": "701784439",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        await event.kick(reject_add_request=True)

        call = mock_api.get_last_call()
        assert call[0] == "set_group_kick"
        assert call[1] == "701784439"  # group_id
        assert call[2] == "违规用户123"  # user_id
        assert call[3] is True  # reject_add_request

    @pytest.mark.asyncio
    async def test_full_moderation_flow(self, mock_api):
        """测试完整的违规处理流程"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "msg123",
            "user_id": "违规用户",
            "group_id": "群ID",
            "message": [{"type": "text", "data": {"text": "违规内容"}}],
            "raw_message": "违规内容",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        # 1. 删除违规消息
        await event.delete()
        # 2. 禁言用户 10 分钟
        await event.ban(duration=600)
        # 3. 发送警告
        await event.reply("请遵守群规！")

        # 验证所有操作都已执行
        assert len(mock_api.calls) == 3
        assert mock_api.calls[0][0] == "delete_msg"
        assert mock_api.calls[1][0] == "set_group_ban"
        assert mock_api.calls[2][0] == "post_group_msg"
