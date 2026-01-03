"""
EventBus 订阅和取消订阅测试
"""

import uuid
from unittest.mock import MagicMock

import pytest

from ncatbot.core.client.event_bus import _compile_regex


class TestEventBusSubscription:
    """测试 EventBus 订阅管理"""

    def test_subscribe_exact_match(self, event_bus):
        """精确匹配订阅"""

        async def handler(event):
            pass

        handler_id = event_bus.subscribe("test.event", handler)

        assert isinstance(handler_id, uuid.UUID)
        assert "test.event" in event_bus._exact
        assert len(event_bus._exact["test.event"]) == 1

    def test_subscribe_regex_match(self, event_bus):
        """正则匹配订阅"""

        async def handler(event):
            pass

        handler_id = event_bus.subscribe("re:test\\..*", handler)

        assert isinstance(handler_id, uuid.UUID)
        assert len(event_bus._regex) == 1

    def test_subscribe_returns_unique_uuid(self, event_bus):
        """订阅返回唯一 UUID"""

        async def handler1(event):
            pass

        async def handler2(event):
            pass

        id1 = event_bus.subscribe("test.event", handler1)
        id2 = event_bus.subscribe("test.event", handler2)

        assert id1 != id2

    def test_subscribe_with_priority(self, event_bus):
        """带优先级的订阅"""

        async def handler1(event):
            pass

        async def handler2(event):
            pass

        event_bus.subscribe("test.event", handler1, priority=1)
        event_bus.subscribe("test.event", handler2, priority=10)

        handlers = event_bus._exact["test.event"]
        assert handlers[0][1] == 10
        assert handlers[1][1] == 1

    def test_subscribe_with_custom_timeout(self, event_bus):
        """自定义超时时间"""

        async def handler(event):
            pass

        event_bus.subscribe("test.event", handler, timeout=30.0)
        assert event_bus._exact["test.event"][0][4] == 30.0

    def test_subscribe_with_plugin_metadata(self, event_bus):
        """带插件元数据的订阅"""

        async def handler(event):
            pass

        plugin = MagicMock()
        plugin.meta_data = {"name": "TestPlugin", "version": "1.0"}

        handler_id = event_bus.subscribe("test.event", handler, plugin=plugin)

        assert handler_id in event_bus._handler_meta
        assert event_bus._handler_meta[handler_id]["name"] == "TestPlugin"


class TestEventBusUnsubscribe:
    """测试 EventBus 取消订阅"""

    def test_unsubscribe_by_uuid(self, event_bus):
        """通过 UUID 取消订阅"""

        async def handler(event):
            pass

        handler_id = event_bus.subscribe("test.event", handler)
        result = event_bus.unsubscribe(handler_id)

        assert result is True
        assert "test.event" not in event_bus._exact

    def test_unsubscribe_nonexistent(self, event_bus):
        """取消不存在的订阅返回 False"""
        fake_id = uuid.uuid4()
        result = event_bus.unsubscribe(fake_id)
        assert result is False

    def test_unsubscribe_regex_handler(self, event_bus):
        """取消正则订阅"""

        async def handler(event):
            pass

        handler_id = event_bus.subscribe("re:test\\..*", handler)
        assert len(event_bus._regex) == 1

        result = event_bus.unsubscribe(handler_id)

        assert result is True
        assert len(event_bus._regex) == 0

    def test_unsubscribe_cleans_metadata(self, event_bus):
        """取消订阅时清理元数据"""

        async def handler(event):
            pass

        plugin = MagicMock()
        plugin.meta_data = {"name": "TestPlugin"}
        handler_id = event_bus.subscribe("test.event", handler, plugin=plugin)

        assert handler_id in event_bus._handler_meta

        event_bus.unsubscribe(handler_id)

        assert handler_id not in event_bus._handler_meta


class TestCompileRegex:
    """测试正则表达式编译"""

    def test_compile_valid_regex(self):
        """编译有效正则"""
        pattern = _compile_regex(r"test\..*")

        assert pattern.match("test.event")
        assert pattern.match("test.another")
        assert not pattern.match("other.event")

    def test_compile_invalid_regex(self):
        """编译无效正则抛出异常"""
        with pytest.raises(ValueError, match="无效正则表达式"):
            _compile_regex(r"[invalid")

    def test_compile_regex_cached(self):
        """正则编译被缓存"""
        pattern1 = _compile_regex(r"test\..*")
        pattern2 = _compile_regex(r"test\..*")
        assert pattern1 is pattern2


class TestEventBusCollectHandlers:
    """测试处理器收集"""

    def test_collect_exact_handlers(self, event_bus):
        """收集精确匹配处理器"""

        async def handler(event):
            pass

        event_bus.subscribe("test.event", handler)
        handlers = event_bus._collect_handlers("test.event")
        assert len(handlers) == 1

    def test_collect_prefix_handlers(self, event_bus):
        """收集前缀匹配处理器"""

        async def handler1(event):
            pass

        async def handler2(event):
            pass

        event_bus.subscribe("ncatbot", handler1)
        event_bus.subscribe("ncatbot.notice", handler2)

        handlers = event_bus._collect_handlers("ncatbot.notice.group")
        assert len(handlers) == 2

    def test_collect_regex_handlers(self, event_bus):
        """收集正则匹配处理器"""

        async def handler(event):
            pass

        event_bus.subscribe("re:ncatbot\\.notice\\..*", handler)
        handlers = event_bus._collect_handlers("ncatbot.notice.group_increase")
        assert len(handlers) == 1

    def test_collect_handlers_sorted_by_priority(self, event_bus):
        """收集的处理器按优先级排序"""

        async def handler_low(event):
            pass

        async def handler_high(event):
            pass

        event_bus.subscribe("test.event", handler_low, priority=1)
        event_bus.subscribe("test.event", handler_high, priority=100)

        handlers = event_bus._collect_handlers("test.event")
        assert handlers[0][1] == 100
        assert handlers[1][1] == 1


class TestEventBusLifecycle:
    """测试 EventBus 生命周期"""

    def test_shutdown_clears_handlers(self, event_bus):
        """shutdown() 清理所有处理器"""

        async def handler(event):
            pass

        plugin = MagicMock()
        plugin.meta_data = {"name": "Test"}

        event_bus.subscribe("test.event", handler, plugin=plugin)
        event_bus.subscribe("re:test\\..*", handler)

        assert len(event_bus._exact) > 0
        assert len(event_bus._regex) > 0
        assert len(event_bus._handler_meta) > 0

        event_bus.shutdown()

        assert len(event_bus._exact) == 0
        assert len(event_bus._regex) == 0
        assert len(event_bus._handler_meta) == 0
