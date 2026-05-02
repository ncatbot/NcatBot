"""
EventParser 规范测试

来源: test_legacy/core/event/events/test_parser.py (适配新架构)

规范:
  P-01: 注册表包含全部 17 种内置事件类型
  P-02: _get_key() 正确推导 message/notice/request/meta_event
  P-03: parse() 解析 6 种典型 OB11 JSON 为对应 BaseEventData 子类
  P-04: parse() 对缺失/未知 post_type 抛 ValueError
  P-05: NapCatEventParser 包装器：缺 post_type → None, 未知类型 → None
  P-06: message_sent 映射到 MESSAGE + message_type
  P-07: notify 子类型通过 sub_type 推导
"""

import pytest

from ncatbot.adapter.napcat.parser import EventParser, NapCatEventParser
from ncatbot.types.qq import (
    FriendRequestEventData,
    GroupMessageEventData,
    GroupMsgEmojiLikeNoticeEventData,
    HeartbeatMetaEventData,
    LifecycleMetaEventData,
    PostType,
    MessageType,
    MetaEventType,
    NoticeType,
    NoticeNotifySubType,
    RequestType,
    PrivateMessageEventData,
    GroupBanNoticeEventData,
    GroupIncreaseNoticeEventData,
    GroupRecallNoticeEventData,
)
from ncatbot.types.qq.notice import NotifyEventData


# ===========================================================================
# P-01: 注册表完整性
# ===========================================================================


class TestEventParserRegistry:
    """P-01: 注册表应包含全部 17 种内置事件类型"""

    def test_message_events_registered(self):
        assert (PostType.MESSAGE, MessageType.PRIVATE) in EventParser._registry
        assert (PostType.MESSAGE, MessageType.GROUP) in EventParser._registry

    def test_meta_events_registered(self):
        assert (PostType.META_EVENT, MetaEventType.LIFECYCLE) in EventParser._registry
        assert (PostType.META_EVENT, MetaEventType.HEARTBEAT) in EventParser._registry

    def test_request_events_registered(self):
        assert (PostType.REQUEST, RequestType.FRIEND) in EventParser._registry
        assert (PostType.REQUEST, RequestType.GROUP) in EventParser._registry

    def test_notice_events_registered(self):
        assert (PostType.NOTICE, NoticeType.GROUP_UPLOAD) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.GROUP_ADMIN) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.GROUP_DECREASE) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.GROUP_INCREASE) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.GROUP_BAN) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.FRIEND_ADD) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.GROUP_RECALL) in EventParser._registry
        assert (PostType.NOTICE, NoticeType.FRIEND_RECALL) in EventParser._registry
        assert (
            PostType.NOTICE,
            NoticeType.GROUP_MSG_EMOJI_LIKE,
        ) in EventParser._registry

    def test_notify_events_registered(self):
        assert (PostType.NOTICE, NoticeType.NOTIFY) in EventParser._registry

    def test_total_registered_count(self):
        # 2 message + 2 request + 2 meta + 10 notice (9 + 1 notify) = 16
        assert len(EventParser._registry) == 16


# ===========================================================================
# P-02: _get_key() 推导
# ===========================================================================


class TestGetKey:
    """P-02: _get_key() 对各 post_type 返回正确的 (post_type, secondary) 元组"""

    def test_message_key(self):
        data = {"post_type": "message", "message_type": "private"}
        assert EventParser._get_key(data) == (PostType.MESSAGE, "private")

    def test_group_message_key(self):
        data = {"post_type": "message", "message_type": "group"}
        assert EventParser._get_key(data) == (PostType.MESSAGE, "group")

    def test_message_sent_maps_to_message(self):
        """P-06: message_sent 也映射到 MESSAGE + message_type"""
        data = {"post_type": "message_sent", "message_type": "group"}
        assert EventParser._get_key(data) == (PostType.MESSAGE, "group")

    def test_notice_key(self):
        data = {"post_type": "notice", "notice_type": "group_recall"}
        assert EventParser._get_key(data) == (PostType.NOTICE, "group_recall")

    def test_notify_uses_notice_type(self):
        """P-07: notify 通过 notice_type 推导，与其他 notice 一致"""
        data = {"post_type": "notice", "notice_type": "notify", "sub_type": "poke"}
        assert EventParser._get_key(data) == (PostType.NOTICE, "notify")

    def test_request_key(self):
        data = {"post_type": "request", "request_type": "friend"}
        assert EventParser._get_key(data) == (PostType.REQUEST, "friend")

    def test_meta_event_key(self):
        data = {"post_type": "meta_event", "meta_event_type": "heartbeat"}
        assert EventParser._get_key(data) == (PostType.META_EVENT, "heartbeat")

    def test_unknown_post_type_returns_none(self):
        data = {"post_type": "unknown_type"}
        assert EventParser._get_key(data) is None

    def test_missing_post_type_returns_none(self):
        data = {"time": 123}
        assert EventParser._get_key(data) is None


# ===========================================================================
# P-03: parse() 解析真实 OB11 JSON
# ===========================================================================


class TestEventParserParse:
    """P-03: parse() 将真实 OB11 JSON 解析为正确的 BaseEventData 子类"""

    def test_parse_private_message(self):
        data = {
            "time": 1767072441,
            "self_id": "1115557735",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "400060831",
            "user_id": "3333355556",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "raw_message": "hello",
            "font": 14,
            "sender": {"user_id": "3333355556", "nickname": "测试"},
        }
        result = EventParser.parse(data)
        assert isinstance(result, PrivateMessageEventData)
        assert result.message_type == MessageType.PRIVATE
        assert result.user_id == "3333355556"

    def test_parse_group_message(self):
        data = {
            "time": 1767072511,
            "self_id": "1115557735",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "2009890763",
            "user_id": "3333355556",
            "group_id": "701784439",
            "group_name": "测试群",
            "message": [{"type": "text", "data": {"text": "你好"}}],
            "raw_message": "你好",
            "font": 14,
            "sender": {"user_id": "3333355556", "role": "member"},
        }
        result = EventParser.parse(data)
        assert isinstance(result, GroupMessageEventData)
        assert result.group_id == "701784439"
        assert result.group_name == "测试群"

    def test_parse_lifecycle_event(self):
        data = {
            "time": 1767072412,
            "self_id": "1115557735",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "connect",
        }
        result = EventParser.parse(data)
        assert isinstance(result, LifecycleMetaEventData)
        assert result.sub_type == "connect"

    def test_parse_heartbeat_event(self):
        data = {
            "time": 1767072414,
            "self_id": "1115557735",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 30000,
        }
        result = EventParser.parse(data)
        assert isinstance(result, HeartbeatMetaEventData)
        assert result.interval == 30000
        assert result.status.online is True

    def test_parse_poke_notify(self):
        data = {
            "time": 1764677819,
            "self_id": "1558718963",
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "target_id": "2324488671",
            "user_id": "1105395138",
            "group_id": "589962002",
        }
        result = EventParser.parse(data)
        assert isinstance(result, NotifyEventData)
        assert result.sub_type == NoticeNotifySubType.POKE

    def test_parse_friend_request(self):
        data = {
            "time": 1767072500,
            "self_id": "1115557735",
            "post_type": "request",
            "request_type": "friend",
            "user_id": "9999999",
            "comment": "请加我好友",
            "flag": "abc123",
        }
        result = EventParser.parse(data)
        assert isinstance(result, FriendRequestEventData)
        assert result.flag == "abc123"
        assert result.comment == "请加我好友"

    def test_parse_group_recall_notice(self):
        data = {
            "time": 1767072600,
            "self_id": "1115557735",
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": "701784439",
            "user_id": "3333355556",
            "operator_id": "3333355556",
            "message_id": "2009890763",
        }
        result = EventParser.parse(data)
        assert isinstance(result, GroupRecallNoticeEventData)
        assert result.operator_id == "3333355556"

    def test_parse_group_ban_notice(self):
        data = {
            "time": 1767072700,
            "self_id": "1115557735",
            "post_type": "notice",
            "notice_type": "group_ban",
            "sub_type": "ban",
            "group_id": "701784439",
            "operator_id": "1115557735",
            "user_id": "3333355556",
            "duration": 600,
        }
        result = EventParser.parse(data)
        assert isinstance(result, GroupBanNoticeEventData)
        assert result.duration == 600

    def test_parse_group_increase_notice(self):
        data = {
            "time": 1767072800,
            "self_id": "1115557735",
            "post_type": "notice",
            "notice_type": "group_increase",
            "sub_type": "approve",
            "group_id": "701784439",
            "operator_id": "1115557735",
            "user_id": "9999999",
        }
        result = EventParser.parse(data)
        assert isinstance(result, GroupIncreaseNoticeEventData)
        assert result.sub_type == "approve"

    def test_parse_group_msg_emoji_like_notice(self):
        data = {
            "time": 1767072900,
            "self_id": "1115557735",
            "post_type": "notice",
            "notice_type": "group_msg_emoji_like",
            "group_id": "701784439",
            "user_id": "3333355556",
            "message_id": "2009890764",
            "likes": [{"emoji_id": "128077", "count": 2}],
            "is_add": True,
            "message_seq": 12345,
        }
        result = EventParser.parse(data)
        assert isinstance(result, GroupMsgEmojiLikeNoticeEventData)
        assert result.message_id == "2009890764"
        assert len(result.likes) == 1
        assert result.likes[0].emoji_id == "128077"
        assert result.likes[0].count == 2
        assert result.is_add is True
        assert result.message_seq == 12345

    def test_parse_int_id_coerced_to_str(self):
        """int 类型的 ID 字段应自动转为 str"""
        data = {
            "time": 1767072441,
            "self_id": 1115557735,
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "400060831",
            "user_id": 3333355556,
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {"user_id": 3333355556, "nickname": "测试"},
        }
        result = EventParser.parse(data)
        assert result.self_id == "1115557735"
        assert result.user_id == "3333355556"


# ===========================================================================
# P-04: 错误处理
# ===========================================================================


class TestEventParserErrors:
    """P-04: parse() 在输入不合法时抛出 ValueError"""

    def test_missing_post_type(self):
        with pytest.raises(ValueError, match="Unknown event"):
            EventParser.parse({"time": 123, "self_id": "111"})

    def test_unknown_post_type(self):
        with pytest.raises(ValueError, match="Unknown event"):
            EventParser.parse({"time": 123, "self_id": "111", "post_type": "garbage"})

    def test_unknown_secondary_type(self):
        with pytest.raises(ValueError, match="No data class registered"):
            EventParser.parse(
                {
                    "time": 123,
                    "self_id": "111",
                    "post_type": "message",
                    "message_type": "nonexistent",
                }
            )


# ===========================================================================
# P-05: NapCatEventParser 包装器
# ===========================================================================


class TestNapCatEventParser:
    """P-05: 包装器不抛异常，对不可解析的事件返回 None"""

    def setup_method(self):
        self.parser = NapCatEventParser()

    def test_missing_post_type_returns_none(self):
        assert self.parser.parse({"time": 123}) is None

    def test_unknown_type_returns_none(self):
        assert self.parser.parse({"post_type": "garbage"}) is None

    def test_valid_event_returns_data_model(self):
        data = {
            "time": 1767072412,
            "self_id": "1115557735",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "connect",
        }
        result = self.parser.parse(data)
        assert isinstance(result, LifecycleMetaEventData)
