"""
CQ 码解析测试 - 测试 parse_cq_code_to_onebot11 和 parse_message_segments 函数
"""

from ncatbot.core import (
    AtAll,
    parse_cq_code_to_onebot11,
    parse_message_segments,
)
from ncatbot.core import PlainText, At, Face


class TestParseCQCodeToOneBot11:
    """测试 CQ 码解析函数"""

    def test_parse_simple_text(self):
        """测试纯文本"""
        result = parse_cq_code_to_onebot11("hello world")
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["data"]["text"] == "hello world"

    def test_parse_single_cq_code(self):
        """测试单个 CQ 码"""
        result = parse_cq_code_to_onebot11("[CQ:face,id=123]")
        assert len(result) == 1
        assert result[0]["type"] == "face"
        assert result[0]["data"]["id"] == "123"

    def test_parse_cq_code_with_text(self):
        """测试 CQ 码和文本混合"""
        result = parse_cq_code_to_onebot11("你好[CQ:face,id=123]世界")
        assert len(result) == 3
        assert result[0]["type"] == "text"
        assert result[0]["data"]["text"] == "你好"
        assert result[1]["type"] == "face"
        assert result[1]["data"]["id"] == "123"
        assert result[2]["type"] == "text"
        assert result[2]["data"]["text"] == "世界"

    def test_parse_image_cq_code(self):
        """测试图片 CQ 码"""
        result = parse_cq_code_to_onebot11("[CQ:image,file=123.jpg]")
        assert len(result) == 1
        assert result[0]["type"] == "image"
        assert result[0]["data"]["file"] == "123.jpg"

    def test_parse_at_cq_code(self):
        """测试 @ CQ 码"""
        result = parse_cq_code_to_onebot11("[CQ:at,qq=123456]")
        assert len(result) == 1
        assert result[0]["type"] == "at"
        assert result[0]["data"]["qq"] == "123456"

    def test_parse_multiple_params(self):
        """测试多参数 CQ 码"""
        result = parse_cq_code_to_onebot11(
            "[CQ:image,file=123.jpg,url=http://example.com]"
        )
        assert len(result) == 1
        assert result[0]["type"] == "image"
        assert result[0]["data"]["file"] == "123.jpg"
        assert result[0]["data"]["url"] == "http://example.com"

    def test_parse_escaped_chars(self):
        """测试转义字符"""
        result = parse_cq_code_to_onebot11("&amp;测试&#91;&#93;&#44;")
        assert len(result) == 1
        assert result[0]["data"]["text"] == "&测试[],"

    def test_parse_cq_code_no_params(self):
        """测试无参数 CQ 码"""
        result = parse_cq_code_to_onebot11("[CQ:shake]")
        assert len(result) == 1
        assert result[0]["type"] == "shake"
        assert result[0]["data"] == {}

    def test_parse_complex_message(self):
        """测试复杂消息"""
        msg = "[CQ:reply,id=12345]@某人 [CQ:image,file=abc.jpg]你好[CQ:face,id=1]"
        result = parse_cq_code_to_onebot11(msg)
        assert len(result) == 5
        assert result[0]["type"] == "reply"
        assert result[1]["type"] == "text"
        assert result[2]["type"] == "image"
        assert result[3]["type"] == "text"
        assert result[4]["type"] == "face"


class TestParseMessageSegments:
    """测试消息段解析函数"""

    def test_parse_dict(self):
        """测试解析字典"""
        data = {"type": "text", "data": {"text": "hello"}}
        result = parse_message_segments(data)
        assert len(result) == 1
        assert isinstance(result[0], PlainText)
        assert result[0].text == "hello"

    def test_parse_message_segment(self):
        """测试解析 MessageSegment 实例"""
        segment = PlainText(text="hello")
        result = parse_message_segments(segment)
        assert len(result) == 1
        assert result[0] is segment

    def test_parse_string_plain(self):
        """测试解析纯字符串"""
        result = parse_message_segments("hello world")
        assert len(result) == 1
        assert isinstance(result[0], PlainText)
        assert result[0].text == "hello world"

    def test_parse_string_cq_code(self):
        """测试解析 CQ 码字符串"""
        result = parse_message_segments("[CQ:at,qq=123]你好")
        assert len(result) == 2
        assert isinstance(result[0], At)
        assert result[0].qq == "123"
        assert isinstance(result[1], PlainText)
        assert result[1].text == "你好"

    def test_parse_atall(self):
        """测试解析 AtAll 实例"""
        atall = AtAll()
        result = parse_message_segments(atall)
        assert len(result) == 1
        assert isinstance(result[0], At)
        assert result[0].qq == "all"

    def test_parse_list(self):
        """测试解析列表"""
        data = [
            {"type": "text", "data": {"text": "hello"}},
            {"type": "at", "data": {"qq": "123"}},
        ]
        result = parse_message_segments(data)
        assert len(result) == 2
        assert isinstance(result[0], PlainText)
        assert isinstance(result[1], At)

    def test_parse_mixed_list(self):
        """测试解析混合列表"""
        text_segment = PlainText(text="world")
        data = [
            {"type": "text", "data": {"text": "hello"}},
            text_segment,
            "[CQ:face,id=1]",
        ]
        result = parse_message_segments(data)
        assert len(result) == 3
        assert result[1] is text_segment
        assert isinstance(result[2], Face)
