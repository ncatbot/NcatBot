"""
请求事件和元事件测试
"""

from ncatbot.core import (
    FriendRequestEvent,
    GroupRequestEvent,
    LifecycleMetaEvent,
    HeartbeatMetaEvent,
)
from ncatbot.core import RequestType, MetaEventType
from ncatbot.core import Status


class TestFriendRequestEvent:
    """测试好友请求事件"""

    def test_create_from_dict(self):
        """测试从字典创建好友请求事件"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "friend",
            "user_id": "456",
            "comment": "请加我为好友",
            "flag": "friend_flag_123",
        }

        event = FriendRequestEvent(**data)

        assert event.request_type == RequestType.FRIEND
        assert event.comment == "请加我为好友"
        assert event.flag == "friend_flag_123"
        assert event.sub_type is None  # 好友请求无 sub_type

    def test_user_id_converts_to_str(self):
        """测试 user_id 自动转为字符串"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "friend",
            "user_id": 456789,  # 整数
            "comment": "",
            "flag": "flag123",
        }

        event = FriendRequestEvent(**data)

        assert event.user_id == "456789"
        assert isinstance(event.user_id, str)

    def test_empty_comment(self):
        """测试空验证消息"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "friend",
            "user_id": "456",
            "comment": None,
            "flag": "flag123",
        }

        event = FriendRequestEvent(**data)

        assert event.comment is None


class TestGroupRequestEvent:
    """测试入群请求事件"""

    def test_add_request(self):
        """测试主动申请入群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "group",
            "sub_type": "add",
            "user_id": "456",
            "group_id": "789",
            "comment": "请让我加入",
            "flag": "group_flag_456",
        }

        event = GroupRequestEvent(**data)

        assert event.request_type == RequestType.GROUP
        assert event.sub_type == "add"
        assert event.group_id == "789"

    def test_invite_request(self):
        """测试邀请入群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "group",
            "sub_type": "invite",
            "user_id": "456",
            "group_id": "789",
            "comment": "",
            "flag": "group_flag_789",
        }

        event = GroupRequestEvent(**data)

        assert event.sub_type == "invite"

    def test_group_id_converts_to_str(self):
        """测试 group_id 自动转为字符串"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "request",
            "request_type": "group",
            "sub_type": "add",
            "user_id": "456",
            "group_id": 789012,  # 整数
            "comment": "",
            "flag": "flag",
        }

        event = GroupRequestEvent(**data)

        assert event.group_id == "789012"
        assert isinstance(event.group_id, str)


class TestLifecycleMetaEvent:
    """测试生命周期元事件"""

    def test_connect(self):
        """测试连接事件"""
        data = {
            "time": 1767072412,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "connect",
        }

        event = LifecycleMetaEvent(**data)

        assert event.meta_event_type == MetaEventType.LIFECYCLE
        assert event.sub_type == "connect"

    def test_enable(self):
        """测试启用事件"""
        data = {
            "time": 1767072412,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "enable",
        }

        event = LifecycleMetaEvent(**data)

        assert event.sub_type == "enable"

    def test_disable(self):
        """测试禁用事件"""
        data = {
            "time": 1767072412,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "disable",
        }

        event = LifecycleMetaEvent(**data)

        assert event.sub_type == "disable"


class TestHeartbeatMetaEvent:
    """测试心跳元事件"""

    def test_create_from_dict(self):
        """测试从字典创建心跳事件"""
        data = {
            "time": 1767072414,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 30000,
        }

        event = HeartbeatMetaEvent(**data)

        assert event.meta_event_type == MetaEventType.HEARTBEAT
        assert event.interval == 30000
        assert isinstance(event.status, Status)
        assert event.status.online is True
        assert event.status.good is True

    def test_interval_value(self):
        """测试不同的心跳间隔"""
        data = {
            "time": 1767072414,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 5000,  # 5秒间隔
        }

        event = HeartbeatMetaEvent(**data)

        assert event.interval == 5000


class TestMetaEventsWithRealData:
    """使用真实日志数据测试元事件"""

    def test_parse_heartbeat_events(self, heartbeat_events):
        """测试解析真实心跳事件"""
        for event_data in heartbeat_events[:3]:
            event = HeartbeatMetaEvent(**event_data)

            assert event.meta_event_type == MetaEventType.HEARTBEAT
            assert event.interval > 0
            assert event.status.online is True

    def test_parse_lifecycle_events(self, lifecycle_events):
        """测试解析真实生命周期事件"""
        for event_data in lifecycle_events[:3]:
            event = LifecycleMetaEvent(**event_data)

            assert event.meta_event_type == MetaEventType.LIFECYCLE
            assert event.sub_type in ["connect", "enable", "disable"]
