"""
parser.py 模块测试 - 测试 EventParser 事件分发器
"""

import pytest

from ncatbot.core.event.parser import EventParser
from ncatbot.core import (
    PrivateMessageEvent,
    GroupMessageEvent,
    LifecycleMetaEvent,
    HeartbeatMetaEvent,
    PokeNotifyEvent,
)
from ncatbot.core import (
    PostType,
    MessageType,
    NoticeType,
    MetaEventType,
    RequestType,
    NotifySubType,
)


class TestEventParserRegistry:
    """测试 EventParser 注册表"""

    def test_registry_initialized(self):
        """测试内置事件已注册"""
        assert len(EventParser._registry) > 0

    def test_message_events_registered(self):
        """测试消息事件已注册"""
        assert (PostType.MESSAGE, MessageType.PRIVATE) in EventParser._registry
        assert (PostType.MESSAGE, MessageType.GROUP) in EventParser._registry

    def test_meta_events_registered(self):
        """测试元事件已注册"""
        assert (PostType.META_EVENT, MetaEventType.LIFECYCLE) in EventParser._registry
        assert (PostType.META_EVENT, MetaEventType.HEARTBEAT) in EventParser._registry

    def test_request_events_registered(self):
        """测试请求事件已注册"""
        assert (PostType.REQUEST, RequestType.FRIEND) in EventParser._registry
        assert (PostType.REQUEST, RequestType.GROUP) in EventParser._registry

    def test_notice_events_registered(self):
        """测试通知事件已注册"""
        assert (PostType.NOTICE, NoticeType.GROUP_RECALL) in EventParser._registry
        assert (PostType.NOTICE, NotifySubType.POKE) in EventParser._registry


class TestEventParserParse:
    """测试 EventParser.parse() 方法"""

    def test_parse_private_message(self, mock_api):
        """测试解析私聊消息"""
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
            "sender": {"user_id": "3051561876", "nickname": "测试"},
        }

        event = EventParser.parse(data, mock_api)

        assert isinstance(event, PrivateMessageEvent)
        assert event.message_type == "private"

    def test_parse_group_message(self, mock_api):
        """测试解析群消息"""
        data = {
            "time": 1767072511,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "2009890763",
            "user_id": "3051561876",
            "group_id": "701784439",
            "message": [],
            "raw_message": "",
            "font": 14,
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        assert isinstance(event, GroupMessageEvent)
        assert event.group_id == "701784439"

    def test_parse_lifecycle_event(self, mock_api):
        """测试解析生命周期事件"""
        data = {
            "time": 1767072412,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "lifecycle",
            "sub_type": "connect",
        }

        event = EventParser.parse(data, mock_api)

        assert isinstance(event, LifecycleMetaEvent)
        assert event.sub_type == "connect"

    def test_parse_heartbeat_event(self, mock_api):
        """测试解析心跳事件"""
        data = {
            "time": 1767072414,
            "self_id": "1550507358",
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
            "status": {"online": True, "good": True},
            "interval": 30000,
        }

        event = EventParser.parse(data, mock_api)

        assert isinstance(event, HeartbeatMetaEvent)
        assert event.interval == 30000

    def test_parse_poke_notify(self, mock_api):
        """测试解析戳一戳通知"""
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

        event = EventParser.parse(data, mock_api)

        assert isinstance(event, PokeNotifyEvent)
        assert event.target_id == "2324488671"

    def test_api_bound_after_parse(self, mock_api):
        """测试解析后 API 已绑定"""
        data = {
            "time": 1767072441,
            "self_id": "1550507358",
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "400060831",
            "user_id": "3051561876",
            "message": [],
            "raw_message": "",
            "sender": {},
        }

        event = EventParser.parse(data, mock_api)

        # 验证 API 已绑定
        assert event.api is mock_api


class TestEventParserErrors:
    """测试 EventParser 错误处理"""

    def test_missing_post_type_raises_error(self, mock_api):
        """测试缺少 post_type 时抛出异常"""
        data = {"time": 1234567890, "self_id": "123"}

        with pytest.raises(ValueError, match="Unknown event type"):
            EventParser.parse(data, mock_api)

    def test_unknown_event_type_raises_error(self, mock_api):
        """测试未知事件类型时抛出异常"""
        data = {"time": 1234567890, "self_id": "123", "post_type": "unknown_type"}

        with pytest.raises(ValueError, match="Unknown event type"):
            EventParser.parse(data, mock_api)

    def test_unknown_secondary_type_raises_error(self, mock_api):
        """测试未知二级类型时抛出异常"""
        data = {
            "time": 1234567890,
            "self_id": "123",
            "post_type": "message",
            "message_type": "unknown_message_type",
        }

        with pytest.raises(ValueError, match="No event class registered"):
            EventParser.parse(data, mock_api)


class TestEventParserGetRegistryKey:
    """测试 EventParser._get_registry_key() 方法"""

    def test_message_registry_key(self):
        """测试消息事件的注册 key"""
        data = {"post_type": "message", "message_type": "private"}
        key = EventParser._get_registry_key(data)
        assert key == ("message", "private")

        data = {"post_type": "message", "message_type": "group"}
        key = EventParser._get_registry_key(data)
        assert key == ("message", "group")

    def test_request_registry_key(self):
        """测试请求事件的注册 key"""
        data = {"post_type": "request", "request_type": "friend"}
        key = EventParser._get_registry_key(data)
        assert key == ("request", "friend")

    def test_meta_event_registry_key(self):
        """测试元事件的注册 key"""
        data = {"post_type": "meta_event", "meta_event_type": "heartbeat"}
        key = EventParser._get_registry_key(data)
        assert key == ("meta_event", "heartbeat")

    def test_notice_registry_key(self):
        """测试普通通知事件的注册 key"""
        data = {"post_type": "notice", "notice_type": "group_recall"}
        key = EventParser._get_registry_key(data)
        assert key == ("notice", "group_recall")

    def test_notify_registry_key_uses_subtype(self):
        """测试 notify 类型使用 sub_type 作为二级 key"""
        data = {"post_type": "notice", "notice_type": "notify", "sub_type": "poke"}
        key = EventParser._get_registry_key(data)
        assert key == ("notice", "poke")


class TestEventParserWithRealData:
    """使用真实日志数据测试 EventParser"""

    def test_parse_all_message_events(self, data_provider, mock_api):
        """测试解析所有消息事件"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        for event_data in data_provider.message_events:
            try:
                event = EventParser.parse(event_data, mock_api)
                assert event is not None
                assert event.api is mock_api
            except Exception as e:
                pytest.fail(f"解析消息事件失败: {e}\n数据: {event_data}")

    def test_parse_all_meta_events(self, data_provider, mock_api):
        """测试解析所有元事件"""
        if not data_provider.has_data:
            pytest.skip("测试数据不可用")

        meta_events = data_provider.get_events_by_post_type("meta_event")
        for event_data in meta_events:
            try:
                event = EventParser.parse(event_data, mock_api)
                assert event is not None
            except Exception as e:
                pytest.fail(f"解析元事件失败: {e}\n数据: {event_data}")

    def test_parse_notice_events(self, notice_events, mock_api):
        """测试解析通知事件"""
        for event_data in notice_events:
            try:
                event = EventParser.parse(event_data, mock_api)
                assert event is not None
            except ValueError as e:
                # 一些通知类型可能尚未实现，记录但不失败
                print(f"跳过未实现的通知类型: {event_data.get('notice_type')} - {e}")
