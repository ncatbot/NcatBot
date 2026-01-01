"""
enums.py 模块测试 - 测试事件类型枚举
"""
import pytest
import json
from enum import Enum

from ncatbot.core import (
    PostType,
    MessageType,
    NoticeType,
    NotifySubType,
    RequestType,
    MetaEventType,
)


class TestPostType:
    """测试 PostType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        assert PostType.MESSAGE == "message"
        assert PostType.MESSAGE_SENT == "message_sent"
        assert PostType.NOTICE == "notice"
        assert PostType.REQUEST == "request"
        assert PostType.META_EVENT == "meta_event"
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(PostType.MESSAGE, str)
        assert isinstance(PostType.MESSAGE, Enum)
    
    def test_json_serializable(self):
        """验证枚举值可序列化为 JSON"""
        data = {"post_type": PostType.MESSAGE}
        result = json.dumps(data)
        assert '"message"' in result
    
    def test_comparison_with_string(self):
        """验证枚举值可与字符串直接比较"""
        assert PostType.MESSAGE == "message"
        assert "message" == PostType.MESSAGE
        assert PostType.MESSAGE_SENT == "message_sent"
        assert "message_sent" == PostType.MESSAGE_SENT


class TestMessageType:
    """测试 MessageType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        assert MessageType.PRIVATE == "private"
        assert MessageType.GROUP == "group"
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(MessageType.PRIVATE, str)


class TestNoticeType:
    """测试 NoticeType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        expected = [
            ("GROUP_UPLOAD", "group_upload"),
            ("GROUP_ADMIN", "group_admin"),
            ("GROUP_DECREASE", "group_decrease"),
            ("GROUP_INCREASE", "group_increase"),
            ("GROUP_BAN", "group_ban"),
            ("FRIEND_ADD", "friend_add"),
            ("GROUP_RECALL", "group_recall"),
            ("FRIEND_RECALL", "friend_recall"),
            ("NOTIFY", "notify"),
        ]
        for name, value in expected:
            assert getattr(NoticeType, name) == value
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(NoticeType.NOTIFY, str)


class TestNotifySubType:
    """测试 NotifySubType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        assert NotifySubType.POKE == "poke"
        assert NotifySubType.LUCKY_KING == "lucky_king"
        assert NotifySubType.HONOR == "honor"
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(NotifySubType.POKE, str)


class TestRequestType:
    """测试 RequestType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        assert RequestType.FRIEND == "friend"
        assert RequestType.GROUP == "group"
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(RequestType.FRIEND, str)


class TestMetaEventType:
    """测试 MetaEventType 枚举"""
    
    def test_all_values_exist(self):
        """验证所有预期的枚举值存在"""
        assert MetaEventType.LIFECYCLE == "lifecycle"
        assert MetaEventType.HEARTBEAT == "heartbeat"
    
    def test_is_str_enum(self):
        """验证枚举继承自 str"""
        assert isinstance(MetaEventType.LIFECYCLE, str)
