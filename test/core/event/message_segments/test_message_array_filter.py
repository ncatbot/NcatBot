"""
MessageArray 过滤和解析测试 - 测试 filter、concatenate_text、is_user_at 等方法
"""

import pytest

from ncatbot.core import MessageArray, Text, AtAll
from ncatbot.core import PlainText, At


class TestMessageArrayFilter:
    """测试 MessageArray 过滤功能"""

    def test_filter_no_cls(self):
        """测试无参数过滤（返回所有）"""
        arr = MessageArray("hello", PlainText(text="world"))
        result = arr.filter()
        assert len(result) == 2

    def test_filter_plaintext(self):
        """测试过滤文本"""
        arr = MessageArray().add_text("hello").add_at(123).add_text("world")
        result = arr.filter(PlainText)
        assert len(result) == 2
        assert all(isinstance(seg, PlainText) for seg in result)

    def test_filter_at(self):
        """测试过滤 @"""
        arr = MessageArray().add_text("hello").add_at(123).add_at(456)
        result = arr.filter(At)
        assert len(result) == 2
        assert all(isinstance(seg, At) for seg in result)

    def test_filter_text_shorthand(self):
        """测试 filter_text 快捷方法"""
        arr = MessageArray().add_text("hello").add_at(123)
        result = arr.filter_text()
        assert len(result) == 1
        assert result[0].text == "hello"

    def test_filter_at_shorthand(self):
        """测试 filter_at 快捷方法"""
        arr = MessageArray().add_text("hello").add_at(123)
        result = arr.filter_at()
        assert len(result) == 1
        assert result[0].qq == "123"

    def test_filter_empty_result(self):
        """测试过滤空结果"""
        arr = MessageArray().add_text("hello")
        result = arr.filter(At)
        assert len(result) == 0

    def test_filter_invalid_type(self):
        """测试过滤无效类型"""
        arr = MessageArray().add_text("hello")
        with pytest.raises(ValueError, match="过滤的类型必须是 MessageSegment 的子类"):
            arr.filter(str)  # type: ignore


class TestMessageArrayParsing:
    """测试 MessageArray 解析功能"""

    def test_concatenate_text(self):
        """测试文本拼接"""
        arr = MessageArray().add_text("hello ").add_at(123).add_text("world")
        result = arr.concatenate_text()
        assert result == "hello world"

    def test_concatenate_text_empty(self):
        """测试空消息拼接"""
        arr = MessageArray().add_at(123)
        result = arr.concatenate_text()
        assert result == ""

    def test_is_user_at_direct(self):
        """测试直接 @"""
        arr = MessageArray().add_at(123456)
        assert arr.is_user_at(123456) is True
        assert arr.is_user_at("123456") is True
        assert arr.is_user_at(654321) is False

    def test_is_user_at_all(self):
        """测试 @全体"""
        arr = MessageArray().add_at_all()
        assert arr.is_user_at(123456) is True

    def test_is_user_at_all_except(self):
        """测试 @全体 排除模式"""
        arr = MessageArray().add_at_all()
        assert arr.is_user_at(123456, all_except=True) is False

    def test_is_user_at_direct_with_all_except(self):
        """测试直接 @ 在排除模式下"""
        arr = MessageArray().add_at(123456).add_at_all()
        assert arr.is_user_at(123456, all_except=True) is True

    def test_is_forward_msg(self):
        """测试是否是转发消息"""
        arr = MessageArray().add_text("hello")
        assert arr.is_forward_msg() == 0


class TestTextAndAtAllCompat:
    """测试 Text 和 AtAll 兼容类"""

    def test_text_type_attribute(self):
        """测试 Text 类型属性"""
        assert Text.type == "text"

    def test_atall_type_attribute(self):
        """测试 AtAll 类型属性"""
        assert AtAll.type == "at"

    def test_atall_default_qq(self):
        """测试 AtAll 默认 qq 值"""
        atall = AtAll()
        assert atall.qq == "all"
