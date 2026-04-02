"""
事件实体工厂规范测试

规范:
  E-01: GroupMessageEventData → GroupMessageEvent
  E-02: PrivateMessageEventData → PrivateMessageEvent
  E-03: 未知 post_type 降级到 BaseEvent
  E-04: __getattr__ (property) 代理底层数据字段
"""

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.event.common.factory import create_entity
from ncatbot.event.qq.message import GroupMessageEvent, PrivateMessageEvent
from ncatbot.event.qq.notice import (
    GroupUploadEvent,
    GroupAdminEvent,
    GroupDecreaseEvent,
    GroupIncreaseEvent,
    GroupBanEvent,
    FriendAddEvent,
    GroupRecallEvent,
    FriendRecallEvent,
    GroupMsgEmojiLikeEvent,
    PokeNotifyEvent,
    LuckyKingNotifyEvent,
    HonorNotifyEvent,
)
from ncatbot.event.qq.request import FriendRequestEvent, GroupRequestEvent
from ncatbot.testing.factories import qq as factory


# ---- E-01 / E-02: 精确映射 ----


def test_group_message_creates_group_event():
    """E-01: GroupMessageEventData → GroupMessageEvent"""
    data = factory.group_message("hi", group_id="111", user_id="222")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupMessageEvent)


def test_private_message_creates_private_event():
    """E-02: PrivateMessageEventData → PrivateMessageEvent"""
    data = factory.private_message("hi", user_id="333")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, PrivateMessageEvent)


def test_friend_request_creates_friend_request_event():
    """E-01 补充: FriendRequestEventData → FriendRequestEvent"""
    data = factory.friend_request(user_id="444")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, FriendRequestEvent)


def test_group_request_creates_group_request_event():
    """E-01 补充: GroupRequestEventData → GroupRequestEvent"""
    data = factory.group_request(user_id="555", group_id="666")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupRequestEvent)


def test_group_increase_creates_event():
    """E-01 补充: GroupIncreaseNoticeEventData → GroupIncreaseEvent"""
    data = factory.group_increase(user_id="777", group_id="888")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupIncreaseEvent)


def test_group_msg_emoji_like_creates_event():
    """E-01 补充: GroupMsgEmojiLikeNoticeEventData → GroupMsgEmojiLikeEvent"""
    data = factory.group_msg_emoji_like(user_id="999", group_id="888")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupMsgEmojiLikeEvent)
    assert entity.message_id == data.message_id
    assert len(entity.likes) == 1
    assert entity.is_add is True


def test_group_upload_creates_event():
    """E-01 补充: GroupUploadNoticeEventData → GroupUploadEvent"""
    data = factory.group_upload(user_id="111", group_id="222")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupUploadEvent)
    assert entity.file.name == "test.txt"


def test_group_admin_creates_event():
    """E-01 补充: GroupAdminNoticeEventData → GroupAdminEvent"""
    data = factory.group_admin(user_id="111", group_id="222", sub_type="set")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupAdminEvent)
    assert entity.sub_type == "set"


def test_group_decrease_creates_event():
    """E-01 补充: GroupDecreaseNoticeEventData → GroupDecreaseEvent"""
    data = factory.group_decrease(user_id="111", group_id="222", sub_type="kick")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupDecreaseEvent)
    assert entity.sub_type == "kick"
    assert entity.operator_id == "10001"


def test_group_ban_creates_event():
    """E-01 补充: GroupBanNoticeEventData → GroupBanEvent"""
    data = factory.group_ban(user_id="123", duration=600)
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupBanEvent)
    assert entity.sub_type == "ban"
    assert entity.duration == 600
    assert entity.operator_id == "10001"


def test_friend_add_creates_event():
    """E-01 补充: FriendAddNoticeEventData → FriendAddEvent"""
    data = factory.friend_add(user_id="111")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, FriendAddEvent)


def test_group_recall_creates_event():
    """E-01 补充: GroupRecallNoticeEventData → GroupRecallEvent"""
    data = factory.group_recall(user_id="111", group_id="222", operator_id="333")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupRecallEvent)
    assert entity.operator_id == "333"
    assert entity.message_id == data.message_id


def test_friend_recall_creates_event():
    """E-01 补充: FriendRecallNoticeEventData → FriendRecallEvent"""
    data = factory.friend_recall(user_id="111")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, FriendRecallEvent)
    assert entity.message_id == data.message_id


def test_poke_creates_event():
    """E-01 补充: PokeNotifyEventData → PokeNotifyEvent"""
    data = factory.poke(user_id="111", target_id="222", group_id="333")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, PokeNotifyEvent)
    assert entity.sub_type == "poke"
    assert entity.target_id == "222"


def test_lucky_king_creates_event():
    """E-01 补充: LuckyKingNotifyEventData → LuckyKingNotifyEvent"""
    data = factory.lucky_king(user_id="111", target_id="222", group_id="333")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, LuckyKingNotifyEvent)
    assert entity.sub_type == "lucky_king"
    assert entity.target_id == "222"


def test_honor_creates_event():
    """E-01 补充: HonorNotifyEventData → HonorNotifyEvent"""
    data = factory.honor(user_id="111", group_id="222", honor_type="talkative")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, HonorNotifyEvent)
    assert entity.sub_type == "honor"
    assert entity.honor_type == "talkative"


# ---- E-03: 降级映射 ----


def test_unknown_notice_falls_back():
    """E-03: 未精确映射的 Notice 降级到 NoticeEvent"""
    from ncatbot.event.qq.notice import NoticeEvent
    from ncatbot.types.qq import NoticeEventData

    data = NoticeEventData.model_validate(
        {
            "time": 0,
            "self_id": "10001",
            "platform": "qq",
            "post_type": "notice",
            "notice_type": "group_upload",
        }
    )
    # 手动把 type(data) 设为基类 NoticeEventData（不在精确映射中），
    # 只要 post_type 是 notice 就应降级到 NoticeEvent
    entity = create_entity(data, MockBotAPI())
    # NoticeEventData 基类本身不在精确映射表中（精确映射只有子类），
    # 但 post_type="notice" 会命中 fallback → NoticeEvent
    assert isinstance(entity, NoticeEvent)


# ---- E-04: property 代理 ----


def test_event_properties_proxy_data():
    """E-04: 事件实体 property 代理底层数据字段"""
    data = factory.group_message("test", group_id="111", user_id="222")
    entity = create_entity(data, MockBotAPI())

    assert entity.time == data.time
    assert entity.self_id == data.self_id
    assert isinstance(entity, GroupMessageEvent)
    assert entity.group_id == "111"
    assert entity.user_id == "222"
    assert entity.raw_message == "test"
