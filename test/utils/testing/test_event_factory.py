"""EventFactory 测试

测试 EventFactory 的各种事件创建方法。
"""

from ncatbot.utils.testing import EventFactory


class TestGroupMessage:
    """群消息事件创建测试"""

    def test_create_basic_group_message(self):
        """测试创建基础群消息"""
        event = EventFactory.create_group_message("Hello")

        assert event is not None
        assert event.message is not None
        assert event.message_type == "group"

    def test_create_group_message_with_custom_ids(self):
        """测试创建自定义 ID 的群消息"""
        event = EventFactory.create_group_message(
            message="测试消息",
            group_id="123456",
            user_id="789012",
        )

        assert event.group_id == "123456"
        assert event.user_id == "789012"

    def test_create_group_message_with_sender_info(self):
        """测试创建带发送者信息的群消息"""
        event = EventFactory.create_group_message(
            message="测试消息",
            nickname="测试用户",
            role="admin",
        )

        assert event.sender.nickname == "测试用户"
        assert event.sender.role == "admin"


class TestPrivateMessage:
    """私聊消息事件创建测试"""

    def test_create_basic_private_message(self):
        """测试创建基础私聊消息"""
        event = EventFactory.create_private_message("私聊消息")

        assert event is not None
        assert event.message_type == "private"

    def test_create_private_message_with_custom_info(self):
        """测试创建自定义信息的私聊消息"""
        event = EventFactory.create_private_message(
            message="私聊消息",
            user_id="123456",
            nickname="测试用户",
            sub_type="friend",
        )

        assert event.user_id == "123456"
        assert event.sender.nickname == "测试用户"
        assert event.sub_type == "friend"


class TestNoticeEvent:
    """通知事件创建测试"""

    def test_create_group_increase_notice(self):
        """测试创建群成员增加通知"""
        event = EventFactory.create_notice_event(
            notice_type="group_increase",
            user_id="123456",
            group_id="789012",
        )

        assert event is not None
        assert event.notice_type == "group_increase"
        assert event.user_id == "123456"
        assert event.group_id == "789012"

    def test_create_group_decrease_notice(self):
        """测试创建群成员减少通知"""
        event = EventFactory.create_notice_event(
            notice_type="group_decrease",
            user_id="123456",
            group_id="789012",
        )

        assert event.notice_type == "group_decrease"
        assert event.user_id == "123456"


class TestRequestEvent:
    """请求事件创建测试"""

    def test_create_friend_request(self):
        """测试创建好友请求"""
        event = EventFactory.create_request_event(
            request_type="friend",
            user_id="123456",
            flag="test_flag",
            comment="请加我为好友",
        )

        assert event is not None
        assert event.request_type == "friend"
        assert event.user_id == "123456"
        assert event.flag == "test_flag"
        assert event.comment == "请加我为好友"

    def test_create_group_request(self):
        """测试创建加群请求"""
        event = EventFactory.create_request_event(
            request_type="group",
            user_id="123456",
            flag="group_flag",
        )

        assert event.request_type == "group"
        assert event.user_id == "123456"
        assert event.flag == "group_flag"
