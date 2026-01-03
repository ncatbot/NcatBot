"""
base.py 模块测试 - 测试 MessageSegment 基类和核心解析功能
"""

import pytest
from typing import Dict, Any, List

from ncatbot.core import (
    MessageSegment,
    MessageArrayDTO,
    parse_message_segment,
    TYPE_MAP,
)
from ncatbot.core import PlainText, Face, At, Reply


class TestMessageSegmentBase:
    """测试 MessageSegment 基类功能"""

    def test_type_map_registration(self):
        """测试子类自动注册到 TYPE_MAP"""
        # 验证内置类型已注册
        assert "text" in TYPE_MAP
        assert "face" in TYPE_MAP
        assert "at" in TYPE_MAP
        assert "reply" in TYPE_MAP
        assert "image" in TYPE_MAP

    def test_type_map_correct_class(self):
        """测试 TYPE_MAP 中的类型映射正确"""
        assert TYPE_MAP["text"] is PlainText
        assert TYPE_MAP["face"] is Face
        assert TYPE_MAP["at"] is At
        assert TYPE_MAP["reply"] is Reply


class TestParseMessageSegment:
    """测试 parse_message_segment 函数"""

    def test_parse_text_segment(self):
        """测试解析文本消息段"""
        data = {"type": "text", "data": {"text": "hello world"}}
        seg = parse_message_segment(data)

        assert isinstance(seg, PlainText)
        assert seg.text == "hello world"

    def test_parse_face_segment(self):
        """测试解析表情消息段"""
        data = {"type": "face", "data": {"id": "317"}}
        seg = parse_message_segment(data)

        assert isinstance(seg, Face)
        assert seg.id == "317"

    def test_parse_at_segment(self):
        """测试解析 @ 消息段"""
        data = {"type": "at", "data": {"qq": "12345678"}}
        seg = parse_message_segment(data)

        assert isinstance(seg, At)
        assert seg.qq == "12345678"

    def test_parse_missing_type_raises_error(self):
        """测试缺少 type 字段时抛出异常"""
        data = {"data": {"text": "hello"}}
        with pytest.raises(ValueError, match="Missing 'type' field"):
            parse_message_segment(data)

    def test_parse_unknown_type_raises_error(self):
        """测试未知类型时抛出异常"""
        data = {"type": "unknown_type_xyz", "data": {}}
        with pytest.raises(ValueError, match="Unknown message segment type"):
            parse_message_segment(data)


class TestMessageSegmentSerialization:
    """测试 MessageSegment 序列化和反序列化"""

    def test_plaintext_roundtrip(self):
        """测试 PlainText 序列化往返"""
        original = PlainText(text="测试文本")
        serialized = original.to_dict()

        assert serialized["type"] == "text"
        assert serialized["data"]["text"] == "测试文本"

        # 反序列化
        restored = parse_message_segment(serialized)
        assert isinstance(restored, PlainText)
        assert restored.text == original.text

    def test_face_roundtrip(self):
        """测试 Face 序列化往返"""
        original = Face(id="123")
        serialized = original.to_dict()

        assert serialized["type"] == "face"
        assert serialized["data"]["id"] == "123"

        restored = parse_message_segment(serialized)
        assert isinstance(restored, Face)
        assert restored.id == original.id

    def test_at_roundtrip(self):
        """测试 At 序列化往返"""
        original = At(qq="12345678")
        serialized = original.to_dict()

        assert serialized["type"] == "at"
        assert serialized["data"]["qq"] == "12345678"

        restored = parse_message_segment(serialized)
        assert isinstance(restored, At)
        assert restored.qq == original.qq


class TestMessageArrayDTO:
    """测试 MessageArrayDTO 类"""

    def test_from_list_simple(self):
        """测试从列表创建 MessageArrayDTO"""
        data = [
            {"type": "text", "data": {"text": "hello"}},
            {"type": "text", "data": {"text": " world"}},
        ]
        dto = MessageArrayDTO.from_list(data)

        assert len(dto.message) == 2
        assert all(isinstance(seg, PlainText) for seg in dto.message)
        assert dto.message[0].text == "hello"
        assert dto.message[1].text == " world"

    def test_from_list_mixed_types(self):
        """测试混合类型消息"""
        data = [
            {"type": "text", "data": {"text": "hello "}},
            {"type": "at", "data": {"qq": "12345678"}},
            {"type": "text", "data": {"text": " how are you?"}},
        ]
        dto = MessageArrayDTO.from_list(data)

        assert len(dto.message) == 3
        assert isinstance(dto.message[0], PlainText)
        assert isinstance(dto.message[1], At)
        assert isinstance(dto.message[2], PlainText)

    def test_from_list_empty(self):
        """测试空列表"""
        dto = MessageArrayDTO.from_list([])
        assert len(dto.message) == 0


class TestWithRealData:
    """使用真实测试数据进行测试"""

    def test_parse_real_text_segments(self, text_segments: List[Dict[str, Any]]):
        """测试解析真实的文本消息段"""
        if not text_segments:
            pytest.skip("No text segments in test data")

        for seg_data in text_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, PlainText)
            assert hasattr(seg, "text")
            assert isinstance(seg.text, str)

    def test_parse_real_face_segments(self, face_segments: List[Dict[str, Any]]):
        """测试解析真实的表情消息段"""
        if not face_segments:
            pytest.skip("No face segments in test data")

        for seg_data in face_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, Face)
            assert hasattr(seg, "id")

    def test_parse_real_at_segments(self, at_segments: List[Dict[str, Any]]):
        """测试解析真实的 @ 消息段"""
        if not at_segments:
            pytest.skip("No at segments in test data")

        for seg_data in at_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, At)
            assert hasattr(seg, "qq")

    def test_parse_complete_message_events(self, message_events: List[Dict[str, Any]]):
        """测试解析完整的消息事件中的所有消息段"""
        if not message_events:
            pytest.skip("No message events in test data")

        for event in message_events:
            message_list = event.get("message", [])
            if not message_list:
                continue

            dto = MessageArrayDTO.from_list(message_list)
            assert len(dto.message) == len(message_list)

            # 验证每个解析出的段都是 MessageSegment 的子类
            for seg in dto.message:
                assert isinstance(seg, MessageSegment)
