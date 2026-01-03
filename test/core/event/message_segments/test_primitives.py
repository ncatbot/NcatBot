"""
primitives.py 模块测试 - 测试基础消息类型 (PlainText, Face, At, Reply)
"""

import pytest
from typing import Dict, Any, List

from ncatbot.core import PlainText, Face, At, Reply
from ncatbot.core import parse_message_segment


class TestPlainText:
    """测试 PlainText 类"""

    def test_create_plaintext(self):
        """测试创建 PlainText 实例"""
        text = PlainText(text="hello world")
        assert text.text == "hello world"
        assert text.type == "text"

    def test_plaintext_empty_string(self):
        """测试空字符串"""
        text = PlainText(text="")
        assert text.text == ""

    def test_plaintext_unicode(self):
        """测试 Unicode 文本"""
        text = PlainText(text="你好世界 🌍 emoji")
        assert text.text == "你好世界 🌍 emoji"

    def test_plaintext_multiline(self):
        """测试多行文本"""
        content = "第一行\n第二行\n第三行"
        text = PlainText(text=content)
        assert text.text == content

    def test_plaintext_special_chars(self):
        """测试特殊字符"""
        content = '<script>alert("xss")</script>'
        text = PlainText(text=content)
        assert text.text == content

    def test_plaintext_to_dict(self):
        """测试序列化"""
        text = PlainText(text="hello")
        result = text.to_dict()

        assert result["type"] == "text"
        assert result["data"]["text"] == "hello"

    def test_plaintext_from_dict(self):
        """测试反序列化"""
        data = {"type": "text", "data": {"text": "hello world"}}
        text = PlainText.from_dict(data)

        assert text.text == "hello world"


class TestFace:
    """测试 Face 类"""

    def test_create_face_with_string_id(self):
        """测试使用字符串 ID 创建 Face"""
        face = Face(id="317")
        assert face.id == "317"
        assert face.type == "face"

    def test_create_face_with_int_id(self):
        """测试使用整数 ID 创建 Face"""
        face = Face(id=317)
        assert face.id == "317"  # 应该转换为字符串

    def test_face_to_dict(self):
        """测试序列化"""
        face = Face(id="123")
        result = face.to_dict()

        assert result["type"] == "face"
        assert result["data"]["id"] == "123"

    def test_face_from_dict(self):
        """测试反序列化"""
        data = {"type": "face", "data": {"id": "317"}}
        face = Face.from_dict(data)

        assert face.id == "317"

    def test_face_roundtrip(self):
        """测试序列化往返"""
        original = Face(id="999")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Face)
        assert restored.id == original.id


class TestAt:
    """测试 At 类"""

    def test_create_at_with_qq_number(self):
        """测试使用 QQ 号创建 At"""
        at = At(qq="12345678")
        assert at.qq == "12345678"
        assert at.type == "at"

    def test_create_at_with_int_qq(self):
        """测试使用整数 QQ 号创建 At"""
        at = At(qq=12345678)
        assert at.qq == "12345678"

    def test_create_at_all(self):
        """测试 @全体成员"""
        at = At(qq="all")
        assert at.qq == "all"

    def test_at_invalid_qq_raises_error(self):
        """测试无效的 QQ 号抛出异常"""
        with pytest.raises(ValueError, match="必须为纯数字或字符串 'all'"):
            At(qq="invalid_qq")

    def test_at_invalid_mixed_raises_error(self):
        """测试混合字符的 QQ 号抛出异常"""
        with pytest.raises(ValueError, match="必须为纯数字或字符串 'all'"):
            At(qq="123abc")

    def test_at_to_dict(self):
        """测试序列化"""
        at = At(qq="12345678")
        result = at.to_dict()

        assert result["type"] == "at"
        assert result["data"]["qq"] == "12345678"

    def test_at_from_dict(self):
        """测试反序列化"""
        data = {"type": "at", "data": {"qq": "2644616336"}}
        at = At.from_dict(data)

        assert at.qq == "2644616336"

    def test_at_from_dict_with_all(self):
        """测试反序列化 @全体成员"""
        data = {"type": "at", "data": {"qq": "all"}}
        at = At.from_dict(data)

        assert at.qq == "all"

    def test_at_roundtrip(self):
        """测试序列化往返"""
        original = At(qq="99999999")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, At)
        assert restored.qq == original.qq


class TestReply:
    """测试 Reply 类"""

    def test_create_reply_with_string_id(self):
        """测试使用字符串 ID 创建 Reply"""
        reply = Reply(id="1970753808")
        assert reply.id == "1970753808"
        assert reply.type == "reply"

    def test_create_reply_with_int_id(self):
        """测试使用整数 ID 创建 Reply"""
        reply = Reply(id=1970753808)
        assert reply.id == "1970753808"

    def test_reply_to_dict(self):
        """测试序列化"""
        reply = Reply(id="123456")
        result = reply.to_dict()

        assert result["type"] == "reply"
        assert result["data"]["id"] == "123456"

    def test_reply_from_dict(self):
        """测试反序列化"""
        data = {"type": "reply", "data": {"id": "1970753808"}}
        reply = Reply.from_dict(data)

        assert reply.id == "1970753808"

    def test_reply_roundtrip(self):
        """测试序列化往返"""
        original = Reply(id="987654321")
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Reply)
        assert restored.id == original.id


class TestPrimitivesWithRealData:
    """使用真实测试数据测试基础类型"""

    def test_real_text_segments(self, text_segments: List[Dict[str, Any]]):
        """测试真实的文本消息段"""
        if not text_segments:
            pytest.skip("No text segments in test data")

        for seg_data in text_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, PlainText)

            # 验证序列化往返
            serialized = seg.to_dict()
            assert serialized["type"] == "text"
            assert "text" in serialized["data"]

    def test_real_face_segments(self, face_segments: List[Dict[str, Any]]):
        """测试真实的表情消息段"""
        if not face_segments:
            pytest.skip("No face segments in test data")

        for seg_data in face_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, Face)
            assert seg.id is not None

    def test_real_at_segments(self, at_segments: List[Dict[str, Any]]):
        """测试真实的 @ 消息段"""
        if not at_segments:
            pytest.skip("No at segments in test data")

        for seg_data in at_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, At)
            # 验证 qq 是有效的值
            assert seg.qq.isdigit() or seg.qq == "all"

    def test_real_reply_segments(self, reply_segments: List[Dict[str, Any]]):
        """测试真实的回复消息段"""
        if not reply_segments:
            pytest.skip("No reply segments in test data")

        for seg_data in reply_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, Reply)
            assert seg.id is not None
