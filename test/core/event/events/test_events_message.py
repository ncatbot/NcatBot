"""
消息事件测试 - 测试 MessageEvent 及其子类
"""
import pytest
from typing import Dict, Any

from ncatbot.core import (
    BaseEvent,
    MessageEvent,
    PrivateMessageEvent,
    GroupMessageEvent,
    LifecycleMetaEvent,
)
from ncatbot.core import PostType, MessageType, MetaEventType
from ncatbot.core import BaseSender, GroupSender


class TestBaseEvent:
    """测试 BaseEvent 基类"""
    
    def test_self_id_converts_to_str(self):
        """测试 self_id 自动转为字符串"""
        # BaseEvent 是抽象的，使用具体子类测试
        event = LifecycleMetaEvent(
            time=1234567890,
            self_id=12345678,  # 整数
            post_type=PostType.META_EVENT,
            meta_event_type=MetaEventType.LIFECYCLE,
            sub_type="connect"
        )
        assert event.self_id == "12345678"
        assert isinstance(event.self_id, str)


class TestPrivateMessageEvent:
    """测试 PrivateMessageEvent"""
    
    def test_create_from_dict(self):
        """测试从字典创建私聊消息事件"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "400060831",
            "user_id": "3051561876",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "raw_message": "hello",
            "font": 14,
            "sender": {
                "user_id": "3051561876",
                "nickname": "测试用户",
                "sex": "unknown",
                "age": 0
            }
        }
        
        event = PrivateMessageEvent(**data)
        
        assert event.message_type == MessageType.PRIVATE
        assert event.sub_type == "friend"
        assert event.message_id == "400060831"
        assert event.user_id == "3051561876"
        assert event.raw_message == "hello"
        assert isinstance(event.sender, BaseSender)
        assert event.sender.nickname == "测试用户"
    
    def test_message_id_converts_to_str(self):
        """测试 message_id 自动转为字符串"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": 400060831,  # 整数
            "user_id": 3051561876,  # 整数
            "message": [],
            "raw_message": "",
            "sender": {}
        }
        
        event = PrivateMessageEvent(**data)
        
        assert event.message_id == "400060831"
        assert event.user_id == "3051561876"
        assert isinstance(event.message_id, str)
        assert isinstance(event.user_id, str)
    
    def test_default_post_type(self):
        """测试默认 post_type 为 message"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "111",
            "user_id": "222",
            "message": [],
            "raw_message": "",
            "sender": {}
        }
        
        event = PrivateMessageEvent(**data)
        assert event.post_type == PostType.MESSAGE
    
    def test_group_id_optional(self):
        """测试私聊消息不需要 group_id"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "111",
            "user_id": "222",
            "message": [],
            "raw_message": "",
            "sender": {}
        }
        
        event = PrivateMessageEvent(**data)
        assert event.group_id is None


class TestGroupMessageEvent:
    """测试 GroupMessageEvent"""
    
    def test_create_from_dict(self):
        """测试从字典创建群消息事件"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "2009890763",
            "user_id": "3051561876",
            "group_id": "701784439",
            "message": [{"type": "text", "data": {"text": "test"}}],
            "raw_message": "test",
            "font": 14,
            "sender": {
                "user_id": "3051561876",
                "nickname": "测试",
                "card": "群名片",
                "role": "owner"
            }
        }
        
        event = GroupMessageEvent(**data)
        
        assert event.message_type == MessageType.GROUP
        assert event.group_id == "701784439"
        assert isinstance(event.sender, GroupSender)
        assert event.sender.card == "群名片"
        assert event.sender.role == "owner"
    
    def test_group_id_converts_to_str(self):
        """测试 group_id 自动转为字符串"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "123",
            "user_id": "456",
            "group_id": 701784439,  # 整数
            "message": [],
            "raw_message": "",
            "sender": {}
        }
        
        event = GroupMessageEvent(**data)
        
        assert event.group_id == "701784439"
        assert isinstance(event.group_id, str)
    
    def test_anonymous_field(self):
        """测试匿名消息字段"""
        data = {
            "time": 1767072511,
            "self_id": "123",
            "message_type": "group",
            "sub_type": "anonymous",
            "message_id": "111",
            "user_id": "222",
            "group_id": "333",
            "message": [],
            "raw_message": "",
            "sender": {},
            "anonymous": {
                "id": 123456,
                "name": "匿名用户",
                "flag": "anon_flag"
            }
        }
        
        event = GroupMessageEvent(**data)
        
        assert event.anonymous is not None
        assert event.anonymous.name == "匿名用户"

    def test_message_sent_post_type(self):
        """测试 post_type=message_sent 的消息事件（自己发送的消息）
        
        修复 Bug: get_group_msg_history 返回的消息可能包含 post_type="message_sent"，
        这是自己发送的消息，需要正确处理。
        """
        from ncatbot.core.event.enums import PostType
        
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message_sent",  # 自己发送的消息
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "2009890763",
            "user_id": "1550507358",  # 通常是自己的 ID
            "group_id": "701784439",
            "message": [{"type": "text", "data": {"text": "我发送的消息"}}],
            "raw_message": "我发送的消息",
            "font": 14,
            "sender": {
                "user_id": "1550507358",
                "nickname": "机器人",
                "card": "",
                "role": "member"
            }
        }
        
        event = GroupMessageEvent(**data)
        
        assert event.post_type == PostType.MESSAGE_SENT
        assert event.message_type == MessageType.GROUP
        assert event.group_id == "701784439"
        assert event.user_id == "1550507358"
        assert event.message.concatenate_text() == "我发送的消息"


class TestMessageEventWithRealData:
    """使用真实日志数据测试消息事件"""
    
    def test_parse_private_message_events(self, private_message_events, mock_api):
        """测试解析真实私聊消息事件"""
        for event_data in private_message_events[:5]:
            event = PrivateMessageEvent(**event_data)
            event.bind_api(mock_api)
            
            assert event.message_type == MessageType.PRIVATE
            assert event.message_id is not None
            assert event.user_id is not None
            # 验证 message 已转换为 MessageArray
            assert hasattr(event.message, 'message')
    
    def test_parse_group_message_events(self, group_message_events, mock_api):
        """测试解析真实群消息事件"""
        for event_data in group_message_events[:5]:
            event = GroupMessageEvent(**event_data)
            event.bind_api(mock_api)
            
            assert event.message_type == MessageType.GROUP
            assert event.group_id is not None
            # 验证 message 已转换为 MessageArray
            assert hasattr(event.message, 'message')
