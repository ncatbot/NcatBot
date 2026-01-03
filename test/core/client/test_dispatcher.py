"""
EventDispatcher 测试
"""

import pytest
from unittest.mock import MagicMock, patch

from ncatbot.core.client.dispatcher import EventDispatcher, parse_event_type
from ncatbot.core import EventType, PostType


class TestParseEventType:
    """测试 parse_event_type 函数"""

    def test_parse_message_type(self):
        """post_type=message → EventType.MESSAGE"""
        data = {"post_type": "message"}

        result = parse_event_type(data)

        assert result == EventType.MESSAGE

    def test_parse_message_type_with_post_type_enum(self):
        """使用 PostType 枚举"""
        data = {"post_type": PostType.MESSAGE}

        result = parse_event_type(data)

        assert result == EventType.MESSAGE

    def test_parse_message_sent_type(self):
        """post_type=message_sent → EventType.MESSAGE_SENT"""
        data = {"post_type": "message_sent"}

        result = parse_event_type(data)

        assert result == EventType.MESSAGE_SENT

    def test_parse_notice_type(self):
        """post_type=notice → EventType.NOTICE"""
        data = {"post_type": "notice"}

        result = parse_event_type(data)

        assert result == EventType.NOTICE

    def test_parse_notice_type_with_enum(self):
        """使用 PostType.NOTICE 枚举"""
        data = {"post_type": PostType.NOTICE}

        result = parse_event_type(data)

        assert result == EventType.NOTICE

    def test_parse_request_type(self):
        """post_type=request → EventType.REQUEST"""
        data = {"post_type": "request"}

        result = parse_event_type(data)

        assert result == EventType.REQUEST

    def test_parse_request_type_with_enum(self):
        """使用 PostType.REQUEST 枚举"""
        data = {"post_type": PostType.REQUEST}

        result = parse_event_type(data)

        assert result == EventType.REQUEST

    def test_parse_meta_event_type(self):
        """post_type=meta_event → EventType.META"""
        data = {"post_type": "meta_event"}

        result = parse_event_type(data)

        assert result == EventType.META

    def test_parse_meta_event_type_with_enum(self):
        """使用 PostType.META_EVENT 枚举"""
        data = {"post_type": PostType.META_EVENT}

        result = parse_event_type(data)

        assert result == EventType.META

    def test_parse_unknown_type(self):
        """未知类型返回 None"""
        data = {"post_type": "unknown_type"}

        result = parse_event_type(data)

        assert result is None

    def test_parse_missing_post_type(self):
        """缺少 post_type 返回 None"""
        data = {"other_field": "value"}

        result = parse_event_type(data)

        assert result is None

    def test_parse_empty_data(self):
        """空数据返回 None"""
        data = {}

        result = parse_event_type(data)

        assert result is None


class TestEventDispatcherInit:
    """测试 EventDispatcher 初始化"""

    def test_dispatcher_init(self, event_bus, mock_api):
        """测试初始化"""
        dispatcher = EventDispatcher(event_bus, mock_api)

        assert dispatcher.event_bus is event_bus
        assert dispatcher.api is mock_api


class TestEventDispatcherDispatch:
    """测试 EventDispatcher 分发功能"""

    @pytest.mark.asyncio
    async def test_dispatch_valid_message_event(
        self, event_dispatcher, sample_message_event_data
    ):
        """分发有效消息事件"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        # 使用正确的事件类型 key: ncatbot.message_event
        event_dispatcher.event_bus.subscribe("ncatbot.message_event", capture_event)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            await event_dispatcher.dispatch(sample_message_event_data)

        assert len(published_events) == 1
        assert published_events[0].type == "ncatbot.message_event"

    @pytest.mark.asyncio
    async def test_dispatch_valid_notice_event(
        self, event_dispatcher, sample_notice_event_data
    ):
        """分发有效通知事件"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        event_dispatcher.event_bus.subscribe("ncatbot.notice_event", capture_event)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            await event_dispatcher.dispatch(sample_notice_event_data)

        assert len(published_events) == 1
        assert published_events[0].type == "ncatbot.notice_event"

    @pytest.mark.asyncio
    async def test_dispatch_valid_request_event(
        self, event_dispatcher, sample_request_event_data
    ):
        """分发有效请求事件"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        event_dispatcher.event_bus.subscribe("ncatbot.request_event", capture_event)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            await event_dispatcher.dispatch(sample_request_event_data)

        assert len(published_events) == 1
        assert published_events[0].type == "ncatbot.request_event"

    @pytest.mark.asyncio
    async def test_dispatch_valid_meta_event(
        self, event_dispatcher, sample_meta_event_data
    ):
        """分发有效元事件"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        event_dispatcher.event_bus.subscribe("ncatbot.meta_event", capture_event)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            await event_dispatcher.dispatch(sample_meta_event_data)

        assert len(published_events) == 1
        assert published_events[0].type == "ncatbot.meta_event"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_event(self, event_dispatcher):
        """未知事件类型不触发分发"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        # 订阅所有可能的事件类型
        for event_type in [
            "ncatbot.message_event",
            "ncatbot.notice_event",
            "ncatbot.request_event",
            "ncatbot.meta_event",
        ]:
            event_dispatcher.event_bus.subscribe(event_type, capture_event)

        data = {"post_type": "unknown"}
        await event_dispatcher.dispatch(data)

        # 没有事件被发布
        assert len(published_events) == 0

    @pytest.mark.asyncio
    async def test_dispatch_parse_error(
        self, event_dispatcher, sample_message_event_data
    ):
        """解析失败时记录警告"""
        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_parser.parse.side_effect = ValueError("Parse error")

            # 不应抛出异常
            await event_dispatcher.dispatch(sample_message_event_data)

    @pytest.mark.asyncio
    async def test_dispatch_general_exception(
        self, event_dispatcher, sample_message_event_data
    ):
        """一般异常处理"""
        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_parser.parse.side_effect = RuntimeError("Unexpected error")

            # 不应抛出异常
            await event_dispatcher.dispatch(sample_message_event_data)


class TestEventDispatcherCallable:
    """测试 EventDispatcher 可调用接口"""

    @pytest.mark.asyncio
    async def test_callable_interface(
        self, event_dispatcher, sample_message_event_data
    ):
        """__call__ 方法可作为回调"""
        published_events = []

        async def capture_event(event):
            published_events.append(event)

        event_dispatcher.event_bus.subscribe("ncatbot.message_event", capture_event)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            # 使用 __call__ 方式调用
            await event_dispatcher(sample_message_event_data)

        assert len(published_events) == 1

    @pytest.mark.asyncio
    async def test_callable_equals_dispatch(
        self, event_dispatcher, sample_message_event_data
    ):
        """__call__ 和 dispatch 行为一致"""
        events_via_call = []
        events_via_dispatch = []

        async def capture_call(event):
            events_via_call.append(event.type)

        async def capture_dispatch(event):
            events_via_dispatch.append(event.type)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_event = MagicMock()
            mock_parser.parse.return_value = mock_event

            # 使用 __call__
            event_dispatcher.event_bus.subscribe("ncatbot.message_event", capture_call)
            await event_dispatcher(sample_message_event_data)

            # 清除订阅
            event_dispatcher.event_bus.shutdown()

            # 使用 dispatch
            event_dispatcher.event_bus.subscribe(
                "ncatbot.message_event", capture_dispatch
            )
            await event_dispatcher.dispatch(sample_message_event_data)

        assert events_via_call == events_via_dispatch


class TestEventDispatcherIntegration:
    """EventDispatcher 集成测试"""

    @pytest.mark.asyncio
    async def test_dispatch_creates_ncatbot_event(
        self, event_dispatcher, sample_message_event_data
    ):
        """分发创建正确的 NcatBotEvent"""
        received_event = None

        async def handler(event):
            nonlocal received_event
            received_event = event

        event_dispatcher.event_bus.subscribe("ncatbot.message_event", handler)

        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_parsed_event = MagicMock()
            mock_parsed_event.user_id = 12345
            mock_parser.parse.return_value = mock_parsed_event

            await event_dispatcher.dispatch(sample_message_event_data)

        assert received_event is not None
        assert received_event.type == "ncatbot.message_event"
        # data 应该是解析后的事件对象
        assert received_event.data.user_id == 12345

    @pytest.mark.asyncio
    async def test_dispatch_passes_api_to_parser(
        self, event_dispatcher, sample_message_event_data, mock_api
    ):
        """分发时将 API 传递给解析器"""
        with patch("ncatbot.core.client.dispatcher.EventParser") as mock_parser:
            mock_parser.parse.return_value = MagicMock()

            await event_dispatcher.dispatch(sample_message_event_data)

            # 验证 parse 被调用时传入了 api
            mock_parser.parse.assert_called_once_with(
                sample_message_event_data, event_dispatcher.api
            )
