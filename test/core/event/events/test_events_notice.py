"""
通知事件测试 - 测试 NoticeEvent 及其子类
"""

from ncatbot.core import (
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupBanNoticeEvent,
    GroupRecallNoticeEvent,
    PokeNotifyEvent,
)
from ncatbot.core import NoticeType


class TestGroupRecallNotice:
    """测试群撤回通知"""

    def test_create_from_dict(self):
        """测试从字典创建群撤回通知"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",
            "message_id": "222",
        }

        event = GroupRecallNoticeEvent(**data)

        assert event.notice_type == NoticeType.GROUP_RECALL
        assert event.operator_id == "111"
        assert event.message_id == "222"

    def test_ids_convert_to_str(self):
        """测试 ID 字段自动转为字符串"""
        data = {
            "time": 1234567890,
            "self_id": 123,  # 整数
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": 456,  # 整数
            "user_id": 789,  # 整数
            "operator_id": 111,  # 整数
            "message_id": 222,  # 整数
        }

        event = GroupRecallNoticeEvent(**data)

        assert isinstance(event.self_id, str)
        assert isinstance(event.group_id, str)
        assert isinstance(event.user_id, str)
        assert isinstance(event.operator_id, str)
        assert isinstance(event.message_id, str)


class TestGroupBanNotice:
    """测试群禁言通知"""

    def test_create_from_dict(self):
        """测试从字典创建群禁言通知"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_ban",
            "sub_type": "ban",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",
            "duration": 3600,
        }

        event = GroupBanNoticeEvent(**data)

        assert event.notice_type == NoticeType.GROUP_BAN
        assert event.sub_type == "ban"
        assert event.duration == 3600

    def test_lift_ban(self):
        """测试解除禁言"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_ban",
            "sub_type": "lift_ban",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",
            "duration": 0,  # 解禁时 duration 为 0
        }

        event = GroupBanNoticeEvent(**data)

        assert event.sub_type == "lift_ban"
        assert event.duration == 0


class TestPokeNotifyEvent:
    """测试戳一戳通知"""

    def test_create_from_dict(self):
        """测试从字典创建戳一戳通知"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "group_id": "456",
            "user_id": "789",
            "target_id": "111",
        }

        event = PokeNotifyEvent(**data)

        assert event.notice_type == NoticeType.NOTIFY
        assert event.sub_type == "poke"
        assert event.target_id == "111"

    def test_target_id_converts_to_str(self):
        """测试 target_id 自动转为字符串"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "group_id": "456",
            "user_id": "789",
            "target_id": 111,  # 整数
        }

        event = PokeNotifyEvent(**data)

        assert event.target_id == "111"
        assert isinstance(event.target_id, str)


class TestGroupIncreaseNotice:
    """测试群成员增加通知"""

    def test_approve_join(self):
        """测试管理员同意入群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_increase",
            "sub_type": "approve",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",
        }

        event = GroupIncreaseNoticeEvent(**data)

        assert event.notice_type == NoticeType.GROUP_INCREASE
        assert event.sub_type == "approve"
        assert event.operator_id == "111"

    def test_invite_join(self):
        """测试邀请入群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_increase",
            "sub_type": "invite",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",
        }

        event = GroupIncreaseNoticeEvent(**data)

        assert event.sub_type == "invite"


class TestGroupDecreaseNotice:
    """测试群成员减少通知"""

    def test_leave(self):
        """测试主动退群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_decrease",
            "sub_type": "leave",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "789",  # 主动退群时 operator_id = user_id
        }

        event = GroupDecreaseNoticeEvent(**data)

        assert event.notice_type == NoticeType.GROUP_DECREASE
        assert event.sub_type == "leave"

    def test_kick(self):
        """测试被踢出群"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "notice",
            "notice_type": "group_decrease",
            "sub_type": "kick",
            "group_id": "456",
            "user_id": "789",
            "operator_id": "111",  # 踢人的管理员
        }

        event = GroupDecreaseNoticeEvent(**data)

        assert event.sub_type == "kick"
        assert event.operator_id == "111"


class TestNoticeEventsWithRealData:
    """使用真实日志数据测试通知事件"""

    def test_parse_poke_events(self, poke_events, mock_api):
        """测试解析真实戳一戳事件"""
        for event_data in poke_events[:3]:
            event = PokeNotifyEvent(**event_data)
            event.bind_api(mock_api)

            assert event.notice_type == NoticeType.NOTIFY
            assert event.sub_type == "poke"
            assert event.target_id is not None
