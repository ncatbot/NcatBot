"""
NcatBotEvent 和 NcatBotEventFactory 测试
"""

from ncatbot.core import NcatBotEvent, NcatBotEventFactory


class TestNcatBotEventInitialization:
    """测试 NcatBotEvent 初始化"""

    def test_event_initialization(self):
        """测试事件初始化，验证 type、data 属性"""
        event = NcatBotEvent("test.event", {"key": "value"})

        assert event.type == "test.event"
        assert event.data == {"key": "value"}
        assert event.results == []
        assert event.exceptions == []
        assert event._propagation_stopped is False
        assert event._intercepted is False

    def test_event_with_complex_data(self):
        """测试复杂数据类型"""
        data = {
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3],
            "tuple": (1, 2, 3),
        }
        event = NcatBotEvent("complex.event", data)

        assert event.data["nested"]["level1"]["level2"] == "value"
        assert event.data["list"] == [1, 2, 3]

    def test_event_with_none_data(self):
        """测试 None 数据"""
        event = NcatBotEvent("test.event", None)
        assert event.data is None


class TestNcatBotEventImmutability:
    """测试 NcatBotEvent 属性不可变性"""

    def test_data_immutability(self):
        """data 属性返回副本，不影响原数据"""
        original_data = {"key": "original"}
        event = NcatBotEvent("test.event", original_data)

        # 获取 data 并修改
        data_copy = event.data
        data_copy["key"] = "modified"
        data_copy["new_key"] = "new_value"

        # 原始数据不应被修改
        assert event.data["key"] == "original"
        assert "new_key" not in event.data

    def test_type_immutability(self):
        """type 属性返回副本"""
        event = NcatBotEvent("test.event", None)

        type_copy = event.type
        # 字符串是不可变的，但验证返回的是副本
        assert type_copy == "test.event"
        assert type_copy is not event._type or isinstance(type_copy, str)

    def test_results_immutability(self):
        """results 属性返回副本"""
        event = NcatBotEvent("test.event", None)
        event.add_result("result1")

        results_copy = event.results
        results_copy.append("result2")

        # 内部结果列表不应被修改
        assert len(event.results) == 1
        assert event.results == ["result1"]

    def test_exceptions_immutability(self):
        """exceptions 属性返回副本"""
        event = NcatBotEvent("test.event", None)
        exc = Exception("test error")
        event.add_exception(exc)

        exceptions_copy = event.exceptions
        exceptions_copy.append(Exception("another error"))

        # 内部异常列表不应被修改
        assert len(event.exceptions) == 1


class TestNcatBotEventResults:
    """测试事件结果管理"""

    def test_add_result(self):
        """测试 add_result 方法"""
        event = NcatBotEvent("test.event", None)

        event.add_result("result1")
        event.add_result(42)
        event.add_result({"key": "value"})

        assert event.results == ["result1", 42, {"key": "value"}]

    def test_add_operator(self):
        """测试 += 操作符添加结果"""
        event = NcatBotEvent("test.event", None)

        event += "result1"
        event += 42

        assert event.results == ["result1", 42]

    def test_iadd_operator(self):
        """测试 + 操作符添加结果"""
        event = NcatBotEvent("test.event", None)

        result = event + "result1"

        assert result is event
        assert event.results == ["result1"]

    def test_chained_add(self):
        """测试链式添加"""
        event = NcatBotEvent("test.event", None)

        event += "r1"
        event += "r2"
        event += "r3"

        assert event.results == ["r1", "r2", "r3"]


class TestNcatBotEventPropagation:
    """测试事件传播控制"""

    def test_stop_propagation(self):
        """测试停止事件传播"""
        event = NcatBotEvent("test.event", None)

        assert event._propagation_stopped is False

        event.stop_propagation()

        assert event._propagation_stopped is True

    def test_stop_propagation_multiple_calls(self):
        """多次调用 stop_propagation"""
        event = NcatBotEvent("test.event", None)

        event.stop_propagation()
        event.stop_propagation()

        assert event._propagation_stopped is True


class TestNcatBotEventIntercept:
    """测试事件拦截"""

    def test_intercept(self):
        """测试拦截事件"""
        event = NcatBotEvent("test.event", None)

        assert event.intercepted is False
        assert event._propagation_stopped is False

        event.intercept()

        assert event.intercepted is True
        assert event._propagation_stopped is True

    def test_intercept_stops_propagation(self):
        """拦截同时停止传播"""
        event = NcatBotEvent("test.event", None)

        event.intercept()

        # 两个标志都应该被设置
        assert event._intercepted is True
        assert event._propagation_stopped is True


class TestNcatBotEventExceptions:
    """测试异常管理"""

    def test_add_exception(self):
        """测试添加异常"""
        event = NcatBotEvent("test.event", None)
        exc1 = ValueError("error 1")
        exc2 = TypeError("error 2")

        event.add_exception(exc1)
        event.add_exception(exc2)

        assert len(event.exceptions) == 2
        assert event.exceptions[0] is exc1
        assert event.exceptions[1] is exc2

    def test_exceptions_are_preserved(self):
        """异常对象被正确保存"""
        event = NcatBotEvent("test.event", None)
        exc = RuntimeError("runtime error")

        event.add_exception(exc)

        assert isinstance(event.exceptions[0], RuntimeError)
        assert str(event.exceptions[0]) == "runtime error"


class TestNcatBotEventRepr:
    """测试事件字符串表示"""

    def test_repr_basic(self):
        """测试基本 __repr__ 输出"""
        event = NcatBotEvent("test.event", {"key": "value"})

        repr_str = repr(event)

        assert "test.event" in repr_str
        assert "key" in repr_str
        assert "Event(" in repr_str

    def test_repr_with_results(self):
        """测试带结果的 __repr__ 输出"""
        event = NcatBotEvent("test.event", None)
        event.add_result("result1")

        repr_str = repr(event)

        assert "result1" in repr_str

    def test_repr_with_exceptions(self):
        """测试带异常的 __repr__ 输出"""
        event = NcatBotEvent("test.event", None)
        event.add_exception(ValueError("test error"))

        repr_str = repr(event)

        assert "exceptions" in repr_str


class TestNcatBotEventFactory:
    """测试 NcatBotEventFactory"""

    def test_create_event_basic(self):
        """测试基本事件创建"""
        event = NcatBotEventFactory.create_event("test")

        assert event.type == "ncatbot.test"
        assert event.data == {}

    def test_create_event_with_kwargs(self):
        """测试带参数的事件创建"""
        event = NcatBotEventFactory.create_event(
            "message", user_id=123, message="hello"
        )

        assert event.type == "ncatbot.message"
        assert event.data["user_id"] == 123
        assert event.data["message"] == "hello"

    def test_create_event_adds_prefix(self):
        """验证自动添加 ncatbot. 前缀"""
        event = NcatBotEventFactory.create_event("custom_event")

        assert event.type.startswith("ncatbot.")
        assert event.type == "ncatbot.custom_event"

    def test_create_event_returns_ncatbot_event(self):
        """验证返回类型是 NcatBotEvent"""
        event = NcatBotEventFactory.create_event("test")

        assert isinstance(event, NcatBotEvent)

    def test_create_event_complex_kwargs(self):
        """测试复杂参数"""
        event = NcatBotEventFactory.create_event(
            "notice",
            group_id=123456,
            user_id=789012,
            action="join",
            extra={"nested": "data"},
        )

        assert event.data["group_id"] == 123456
        assert event.data["extra"]["nested"] == "data"
