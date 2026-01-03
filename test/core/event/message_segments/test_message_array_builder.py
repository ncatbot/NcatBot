"""
MessageArray 构造和构建器测试 - 测试初始化和链式构建方法
"""

from ncatbot.core import MessageArray
from ncatbot.core import PlainText, At, Face, Reply


class TestMessageArrayConstruction:
    """测试 MessageArray 构造"""

    def test_init_empty(self):
        """测试空初始化"""
        arr = MessageArray()
        assert len(arr) == 0

    def test_init_with_string(self):
        """测试字符串初始化"""
        arr = MessageArray("hello world")
        assert len(arr) == 1
        assert isinstance(arr.message[0], PlainText)

    def test_init_with_cq_code(self):
        """测试 CQ 码初始化"""
        arr = MessageArray("[CQ:at,qq=123]hello")
        assert len(arr) == 2
        assert isinstance(arr.message[0], At)
        assert isinstance(arr.message[1], PlainText)

    def test_init_with_segment(self):
        """测试 MessageSegment 初始化"""
        segment = PlainText(text="hello")
        arr = MessageArray(segment)
        assert len(arr) == 1
        assert arr.message[0] is segment

    def test_init_with_multiple_args(self):
        """测试多参数初始化"""
        arr = MessageArray("hello", PlainText(text="world"))
        assert len(arr) == 2

    def test_init_with_message_kwarg(self):
        """测试 message 关键字参数初始化"""
        segments = [PlainText(text="hello")]
        arr = MessageArray(message=segments)
        assert len(arr) == 1


class TestMessageArrayBuilder:
    """测试 MessageArray 链式构建方法"""

    def test_add_text(self):
        """测试添加文本"""
        arr = MessageArray().add_text("hello")
        assert len(arr) == 1
        assert isinstance(arr.message[0], PlainText)
        assert arr.message[0].text == "hello"

    def test_add_text_with_cq_code(self):
        """测试添加带 CQ 码的文本"""
        arr = MessageArray().add_text("[CQ:face,id=1]hello")
        assert len(arr) == 2
        assert isinstance(arr.message[0], Face)
        assert isinstance(arr.message[1], PlainText)

    def test_add_at(self):
        """测试添加 @"""
        arr = MessageArray().add_at(123456)
        assert len(arr) == 1
        assert isinstance(arr.message[0], At)
        assert arr.message[0].qq == "123456"

    def test_add_at_string_id(self):
        """测试添加 @ (字符串 ID)"""
        arr = MessageArray().add_at("123456")
        assert len(arr) == 1
        assert arr.message[0].qq == "123456"

    def test_add_at_all(self):
        """测试添加 @全体"""
        arr = MessageArray().add_at_all()
        assert len(arr) == 1
        assert isinstance(arr.message[0], At)
        assert arr.message[0].qq == "all"

    def test_add_reply(self):
        """测试添加回复"""
        arr = MessageArray().add_reply(12345)
        assert len(arr) == 1
        assert isinstance(arr.message[0], Reply)
        assert arr.message[0].id == "12345"

    def test_add_by_segment(self):
        """测试添加消息段"""
        segment = Face(id="1")
        arr = MessageArray().add_by_segment(segment)
        assert len(arr) == 1
        assert arr.message[0] is segment

    def test_add_by_dict(self):
        """测试通过字典添加"""
        arr = MessageArray().add_by_dict({"type": "text", "data": {"text": "hello"}})
        assert len(arr) == 1
        assert isinstance(arr.message[0], PlainText)

    def test_add_by_list(self):
        """测试通过列表添加"""
        data = [
            {"type": "text", "data": {"text": "hello"}},
            {"type": "at", "data": {"qq": "123"}},
        ]
        arr = MessageArray().add_by_list(data)
        assert len(arr) == 2

    def test_chained_add(self):
        """测试链式添加"""
        arr = MessageArray().add_text("hello ").add_at(123).add_text(" world")
        assert len(arr) == 3

    def test_add_returns_self(self):
        """测试添加方法返回自身"""
        arr = MessageArray()
        result = arr.add_text("hello")
        assert result is arr


class TestMessageArrayOperators:
    """测试 MessageArray 运算符"""

    def test_add_operator_with_string(self):
        """测试 + 运算符（字符串）"""
        arr = MessageArray("hello")
        result = arr + " world"
        assert len(result) == 2
        assert result.concatenate_text() == "hello world"

    def test_add_operator_with_segment(self):
        """测试 + 运算符（消息段）"""
        arr = MessageArray("hello")
        result = arr + PlainText(text=" world")
        assert len(result) == 2

    def test_add_operator_with_list(self):
        """测试 + 运算符（列表）"""
        arr = MessageArray("hello")
        result = arr + [PlainText(text=" "), At(qq="123")]
        assert len(result) == 3

    def test_radd_operator(self):
        """测试右加运算符"""
        arr = MessageArray("world")
        result = "hello " + arr
        # 注意: __radd__ 实现为 self.__add__(other)，所以顺序是 arr + other
        assert len(result) == 2
        assert result.concatenate_text() == "worldhello "

    def test_len(self):
        """测试长度"""
        arr = MessageArray("hello", "world")
        assert len(arr) == 2

    def test_iter(self):
        """测试迭代"""
        arr = MessageArray("hello", "world")
        segments = list(arr)
        assert len(segments) == 2
