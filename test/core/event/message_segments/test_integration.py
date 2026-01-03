"""
集成测试 - 测试完整消息事件的解析流程
"""

import pytest
from typing import Dict, Any, List

from ncatbot.core import (
    MessageArrayDTO,
    parse_message_segment,
    MessageSegment,
    TYPE_MAP,
)
from ncatbot.core import PlainText, Face, At, Reply
from ncatbot.core import Image
from ncatbot.core import Forward


class TestCompleteMessageParsing:
    """测试完整消息解析流程"""

    def test_parse_simple_text_message(self):
        """测试解析简单文本消息"""
        message_data = [{"type": "text", "data": {"text": "Hello, World!"}}]

        dto = MessageArrayDTO.from_list(message_data)

        assert len(dto.message) == 1
        assert isinstance(dto.message[0], PlainText)
        assert dto.message[0].text == "Hello, World!"

    def test_parse_mixed_message(self):
        """测试解析混合类型消息"""
        message_data = [
            {"type": "text", "data": {"text": "测试、"}},
            {
                "type": "image",
                "data": {
                    "file": "test.jpeg",
                    "sub_type": 0,
                    "url": "https://example.com/test.jpeg",
                },
            },
            {"type": "text", "data": {"text": "混合"}},
            {"type": "face", "data": {"id": "317"}},
        ]

        dto = MessageArrayDTO.from_list(message_data)

        assert len(dto.message) == 4
        assert isinstance(dto.message[0], PlainText)
        assert isinstance(dto.message[1], Image)
        assert isinstance(dto.message[2], PlainText)
        assert isinstance(dto.message[3], Face)

    def test_parse_reply_message(self):
        """测试解析引用回复消息"""
        message_data = [
            {"type": "reply", "data": {"id": "1970753808"}},
            {"type": "text", "data": {"text": "引用"}},
        ]

        dto = MessageArrayDTO.from_list(message_data)

        assert len(dto.message) == 2
        assert isinstance(dto.message[0], Reply)
        assert dto.message[0].id == "1970753808"
        assert isinstance(dto.message[1], PlainText)

    def test_parse_at_message(self):
        """测试解析 @ 消息"""
        message_data = [
            {"type": "at", "data": {"qq": "2644616336"}},
            {"type": "text", "data": {"text": " "}},
            {"type": "at", "data": {"qq": "all"}},
            {"type": "text", "data": {"text": " @测试"}},
        ]

        dto = MessageArrayDTO.from_list(message_data)

        assert len(dto.message) == 4
        assert isinstance(dto.message[0], At)
        assert dto.message[0].qq == "2644616336"
        assert isinstance(dto.message[2], At)
        assert dto.message[2].qq == "all"

    def test_parse_forward_message(self):
        """测试解析转发消息"""
        message_data = [{"type": "forward", "data": {"id": "7589518469182843880"}}]

        dto = MessageArrayDTO.from_list(message_data)

        assert len(dto.message) == 1
        assert isinstance(dto.message[0], Forward)
        assert dto.message[0].id == "7589518469182843880"


class TestMessageSerialization:
    """测试消息序列化"""

    def test_serialize_simple_message(self):
        """测试序列化简单消息"""
        dto = MessageArrayDTO(
            message=[
                PlainText(text="Hello"),
                PlainText(text=" World"),
            ]
        )

        result = dto.to_list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["type"] == "text"
        assert result[0]["data"]["text"] == "Hello"
        assert result[1]["type"] == "text"
        assert result[1]["data"]["text"] == " World"

    def test_serialize_mixed_message(self):
        """测试序列化混合消息"""
        dto = MessageArrayDTO(
            message=[
                PlainText(text="Hi "),
                At(qq="12345678"),
                PlainText(text=" how are you?"),
            ]
        )

        result = dto.to_list()

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0]["type"] == "text"
        assert result[1]["type"] == "at"
        assert result[1]["data"]["qq"] == "12345678"
        assert result[2]["type"] == "text"


class TestRealDataIntegration:
    """使用真实数据进行集成测试"""

    def test_parse_all_message_events(self, message_events: List[Dict[str, Any]]):
        """测试解析所有消息事件"""
        if not message_events:
            pytest.skip("No message events in test data")

        for event in message_events:
            message_list = event.get("message", [])
            if not message_list:
                continue

            # 解析消息
            dto = MessageArrayDTO.from_list(message_list)

            # 验证解析成功
            assert len(dto.message) == len(message_list)

            # 验证每个段都是有效的 MessageSegment
            for i, seg in enumerate(dto.message):
                assert isinstance(seg, MessageSegment)

                # 验证类型正确
                original_type = message_list[i]["type"]
                assert seg.type == original_type

    def test_roundtrip_all_segments(self, data_provider):
        """测试所有消息段的序列化往返"""
        all_segments = data_provider.get_all_segments()

        if not all_segments:
            pytest.skip("No segments in test data")

        for seg_data in all_segments:
            seg_type = seg_data.get("type")

            # 跳过未知类型
            if seg_type not in TYPE_MAP:
                continue

            # 解析
            seg = parse_message_segment(seg_data)

            # 序列化
            serialized = seg.to_dict()

            # 验证结构
            assert "type" in serialized
            assert "data" in serialized
            assert serialized["type"] == seg_type

    def test_private_message_parsing(self, message_events: List[Dict[str, Any]]):
        """测试私聊消息解析"""
        private_messages = [
            e for e in message_events if e.get("message_type") == "private"
        ]

        if not private_messages:
            pytest.skip("No private messages in test data")

        for event in private_messages:
            message_list = event.get("message", [])
            if message_list:
                dto = MessageArrayDTO.from_list(message_list)
                assert len(dto.message) > 0

    def test_group_message_parsing(self, message_events: List[Dict[str, Any]]):
        """测试群聊消息解析"""
        group_messages = [e for e in message_events if e.get("message_type") == "group"]

        if not group_messages:
            pytest.skip("No group messages in test data")

        for event in group_messages:
            message_list = event.get("message", [])
            if message_list:
                dto = MessageArrayDTO.from_list(message_list)
                assert len(dto.message) > 0


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_message_array(self):
        """测试空消息数组"""
        dto = MessageArrayDTO.from_list([])
        assert len(dto.message) == 0

    def test_segment_with_extra_fields(self):
        """测试带有额外字段的消息段"""
        data = {
            "type": "text",
            "data": {"text": "hello", "extra_field": "should be preserved"},
        }
        seg = parse_message_segment(data)

        assert isinstance(seg, PlainText)
        assert seg.text == "hello"
        # 额外字段应该被保留 (因为 model_config 中设置了 extra="allow")

    def test_segment_with_empty_data(self):
        """测试数据字段为空的情况"""
        # 注意: 这可能会根据具体类型失败，因为某些字段是必需的
        pass

    def test_unicode_handling(self):
        """测试 Unicode 处理"""
        data = {"type": "text", "data": {"text": "你好世界 🌍 emoji 表情 👋"}}
        seg = parse_message_segment(data)

        assert seg.text == "你好世界 🌍 emoji 表情 👋"

    def test_special_characters_in_text(self):
        """测试文本中的特殊字符"""
        special_text = "测试、[CQ:image,file=test.jpeg]混合<>&\"'"
        data = {"type": "text", "data": {"text": special_text}}
        seg = parse_message_segment(data)

        assert seg.text == special_text


class TestTypeMapCompleteness:
    """测试 TYPE_MAP 完整性"""

    def test_all_types_registered(self):
        """测试所有类型都已注册"""
        expected_types = [
            "text",
            "face",
            "at",
            "reply",  # primitives
            "image",
            "record",
            "video",
            "file",  # media
            "share",
            "location",
            "music",
            "json",
            "markdown",  # misc
            "forward",  # forward
        ]

        for t in expected_types:
            assert t in TYPE_MAP, f"Type '{t}' is not registered in TYPE_MAP"

    def test_type_map_classes_are_message_segments(self):
        """测试 TYPE_MAP 中的所有类都是 MessageSegment 的子类"""
        for type_name, cls in TYPE_MAP.items():
            assert issubclass(cls, MessageSegment), (
                f"{cls.__name__} (type={type_name}) is not a subclass of MessageSegment"
            )
