"""
事件工厂测试 — 验证 factory 函数产出合法的数据模型
"""

from ncatbot.testing import factory
from ncatbot.types import (
    GroupMessageEventData,
    PrivateMessageEventData,
    FriendRequestEventData,
    GroupRequestEventData,
    GroupIncreaseNoticeEventData,
    GroupDecreaseNoticeEventData,
    GroupBanNoticeEventData,
    PokeNotifyEventData,
)


def test_group_message_factory():
    msg = factory.group_message("你好世界", group_id="12345", user_id="67890")
    assert isinstance(msg, GroupMessageEventData)
    assert msg.group_id == "12345"
    assert msg.user_id == "67890"
    assert msg.raw_message == "你好世界"
    assert msg.post_type.value == "message"
    assert msg.message_type.value == "group"


def test_private_message_factory():
    msg = factory.private_message("hello", user_id="11111")
    assert isinstance(msg, PrivateMessageEventData)
    assert msg.user_id == "11111"
    assert msg.raw_message == "hello"


def test_friend_request_factory():
    req = factory.friend_request(user_id="22222", comment="加我")
    assert isinstance(req, FriendRequestEventData)
    assert req.user_id == "22222"
    assert req.comment == "加我"


def test_group_request_factory():
    req = factory.group_request(user_id="33333", group_id="44444")
    assert isinstance(req, GroupRequestEventData)
    assert req.user_id == "33333"
    assert req.group_id == "44444"


def test_group_increase_factory():
    notice = factory.group_increase(user_id="55555", group_id="12345")
    assert isinstance(notice, GroupIncreaseNoticeEventData)
    assert notice.user_id == "55555"


def test_group_decrease_factory():
    notice = factory.group_decrease(user_id="66666", sub_type="kick")
    assert isinstance(notice, GroupDecreaseNoticeEventData)
    assert notice.sub_type == "kick"


def test_group_ban_factory():
    notice = factory.group_ban(user_id="77777", duration=300)
    assert isinstance(notice, GroupBanNoticeEventData)
    assert notice.duration == 300


def test_poke_factory():
    notice = factory.poke(user_id="88888", target_id="99999")
    assert isinstance(notice, PokeNotifyEventData)
    assert notice.user_id == "88888"
    assert notice.target_id == "99999"


def test_unique_message_ids():
    """每次调用 factory 产出不同的 message_id"""
    msg1 = factory.group_message("a")
    msg2 = factory.group_message("b")
    assert msg1.message_id != msg2.message_id
