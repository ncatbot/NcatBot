"""
事件序列化测试
"""

from ncatbot.core import (
    PrivateMessageEvent,
    GroupMessageEvent,
    HeartbeatMetaEvent,
)


class TestMessageEventSerialization:
    """测试消息事件序列化"""

    def test_private_message_event_serialization(self):
        """测试私聊消息事件序列化"""
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
                "nickname": "测试",
            },
        }

        event = PrivateMessageEvent(**data)
        serialized = event.model_dump()

        assert serialized["message_type"] == "private"
        assert serialized["message_id"] == "400060831"
        # 私有属性不应被序列化
        assert "_api" not in serialized

    def test_group_message_event_serialization(self):
        """测试群消息事件序列化"""
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
                "role": "owner",
            },
        }

        event = GroupMessageEvent(**data)
        serialized = event.model_dump()

        assert serialized["message_type"] == "group"
        assert serialized["group_id"] == "701784439"
        assert serialized["sender"]["card"] == "群名片"


class TestMetaEventSerialization:
    """测试元事件序列化"""

    def test_heartbeat_event_serialization(self):
        """测试心跳事件序列化"""
        data = {
            "time": 1767072414,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 30000,
        }

        event = HeartbeatMetaEvent(**data)
        serialized = event.model_dump()

        # 嵌套模型也应正确序列化
        assert serialized["status"]["online"] is True
        assert serialized["status"]["good"] is True
        assert serialized["interval"] == 30000


class TestSerializationRoundtrip:
    """测试序列化往返"""

    def test_private_message_roundtrip(self):
        """测试私聊消息事件往返"""
        original_data = {
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
            "sender": {"user_id": "3051561876", "nickname": "测试"},
        }

        # 创建 -> 序列化 -> 重新创建
        event = PrivateMessageEvent(**original_data)
        serialized = event.model_dump()
        restored = PrivateMessageEvent(**serialized)

        # 验证关键字段一致
        assert restored.message_id == event.message_id
        assert restored.user_id == event.user_id
        assert restored.raw_message == event.raw_message
        assert restored.message_type == event.message_type

    def test_heartbeat_roundtrip(self):
        """测试心跳事件往返"""
        original_data = {
            "time": 1767072414,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 30000,
        }

        event = HeartbeatMetaEvent(**original_data)
        serialized = event.model_dump()
        restored = HeartbeatMetaEvent(**serialized)

        assert restored.interval == event.interval
        assert restored.status.online == event.status.online
        assert restored.status.good == event.status.good
