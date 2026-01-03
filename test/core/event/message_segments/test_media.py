"""
media.py 模块测试 - 测试媒体消息类型 (Image, Record, Video, File)
"""

import pytest
from typing import Dict, Any, List

from ncatbot.core import (
    Image,
    Record,
    Video,
    File,
)
from ncatbot.core import parse_message_segment


class TestDownloadableMessageSegment:
    """测试 DownloadableMessageSegment 基类"""

    def test_image_has_downloadable_fields(self):
        """测试 Image 继承了可下载字段"""
        img = Image(file="test.jpg")

        # 验证基类字段存在
        assert hasattr(img, "file")
        assert hasattr(img, "url")
        assert hasattr(img, "file_id")
        assert hasattr(img, "file_size")
        assert hasattr(img, "file_name")

    def test_downloadable_optional_fields(self):
        """测试可选字段默认为 None"""
        img = Image(file="test.jpg")

        assert img.url is None
        assert img.file_id is None
        assert img.file_size is None
        assert img.file_name is None


class TestImage:
    """测试 Image 类"""

    def test_create_image_basic(self):
        """测试创建基本 Image 实例"""
        img = Image(file="test.jpg")

        assert img.file == "test.jpg"
        assert img.type == "image"
        assert img.sub_type == 0  # 默认值

    def test_create_image_with_all_fields(self):
        """测试创建完整 Image 实例"""
        img = Image(
            file="test.jpg",
            url="https://example.com/test.jpg",
            file_id="abc123",
            file_size=1024,
            file_name="test.jpg",
            sub_type=1,
            image_type="normal",
        )

        assert img.file == "test.jpg"
        assert img.url == "https://example.com/test.jpg"
        assert img.file_id == "abc123"
        assert img.file_size == 1024
        assert img.file_name == "test.jpg"
        assert img.sub_type == 1
        assert img.image_type == "normal"

    def test_image_flash_type(self):
        """测试闪照类型"""
        img = Image(file="test.jpg", image_type="flash")
        assert img.image_type == "flash"

    def test_image_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "image",
            "data": {
                "file": "32C97673A346FE9E1335EACE6C062355.jpeg",
                "sub_type": 0,
                "url": "https://example.com/image.jpg",
                "file_size": "134105",
            },
        }
        img = Image.from_dict(data)

        assert img.file == "32C97673A346FE9E1335EACE6C062355.jpeg"
        assert img.sub_type == 0
        assert img.url == "https://example.com/image.jpg"

    def test_image_to_dict(self):
        """测试序列化到字典"""
        img = Image(file="test.jpg", sub_type=0)
        result = img.to_dict()

        assert result["type"] == "image"
        assert result["data"]["file"] == "test.jpg"
        assert result["data"]["sub_type"] == 0

    def test_image_roundtrip(self):
        """测试序列化往返"""
        original = Image(
            file="test.jpg", url="https://example.com/test.jpg", sub_type=0
        )
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Image)
        assert restored.file == original.file
        assert restored.sub_type == original.sub_type


class TestRecord:
    """测试 Record 类"""

    def test_create_record_basic(self):
        """测试创建基本 Record 实例"""
        record = Record(file="test.amr")

        assert record.file == "test.amr"
        assert record.type == "record"

    def test_create_record_with_magic(self):
        """测试创建带变声的 Record"""
        record = Record(file="test.amr", magic=1)

        assert record.file == "test.amr"
        assert record.magic == 1

    def test_record_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "record",
            "data": {"file": "voice.amr", "url": "https://example.com/voice.amr"},
        }
        record = Record.from_dict(data)

        assert record.file == "voice.amr"
        assert record.url == "https://example.com/voice.amr"

    def test_record_to_dict(self):
        """测试序列化"""
        record = Record(file="test.amr", magic=1)
        result = record.to_dict()

        assert result["type"] == "record"
        assert result["data"]["file"] == "test.amr"
        assert result["data"]["magic"] == 1

    def test_record_roundtrip(self):
        """测试序列化往返"""
        original = Record(file="test.amr", magic=0)
        serialized = original.to_dict()
        restored = parse_message_segment(serialized)

        assert isinstance(restored, Record)
        assert restored.file == original.file


class TestVideo:
    """测试 Video 类"""

    def test_create_video_basic(self):
        """测试创建基本 Video 实例"""
        video = Video(file="test.mp4")

        assert video.file == "test.mp4"
        assert video.type == "video"

    def test_create_video_with_url(self):
        """测试创建带 URL 的 Video"""
        video = Video(
            file="test.mp4", url="https://example.com/test.mp4", file_size=10240
        )

        assert video.url == "https://example.com/test.mp4"
        assert video.file_size == 10240

    def test_video_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "video",
            "data": {"file": "video.mp4", "url": "https://example.com/video.mp4"},
        }
        video = Video.from_dict(data)

        assert video.file == "video.mp4"

    def test_video_to_dict(self):
        """测试序列化"""
        video = Video(file="test.mp4")
        result = video.to_dict()

        assert result["type"] == "video"
        assert result["data"]["file"] == "test.mp4"


class TestFile:
    """测试 File 类"""

    def test_create_file_basic(self):
        """测试创建基本 File 实例"""
        file = File(file="document.pdf")

        assert file.file == "document.pdf"
        assert file.type == "file"

    def test_create_file_with_all_fields(self):
        """测试创建完整 File 实例"""
        file = File(
            file="document.pdf",
            url="https://example.com/document.pdf",
            file_id="file123",
            file_size=2048,
            file_name="document.pdf",
        )

        assert file.file_name == "document.pdf"
        assert file.file_size == 2048

    def test_file_from_dict(self):
        """测试从字典创建"""
        data = {
            "type": "file",
            "data": {"file": "doc.pdf", "file_name": "document.pdf"},
        }
        file = File.from_dict(data)

        assert file.file == "doc.pdf"
        assert file.file_name == "document.pdf"

    def test_file_to_dict(self):
        """测试序列化"""
        file = File(file="test.txt", file_name="test.txt")
        result = file.to_dict()

        assert result["type"] == "file"
        assert result["data"]["file"] == "test.txt"


class TestMediaWithRealData:
    """使用真实测试数据测试媒体类型"""

    def test_real_image_segments(self, image_segments: List[Dict[str, Any]]):
        """测试真实的图片消息段"""
        if not image_segments:
            pytest.skip("No image segments in test data")

        for seg_data in image_segments:
            seg = parse_message_segment(seg_data)
            assert isinstance(seg, Image)

            # 验证必需字段
            assert seg.file is not None

            # 验证可选字段的类型
            if seg.url is not None:
                assert isinstance(seg.url, str)
            if seg.file_size is not None:
                assert isinstance(seg.file_size, (int, str))

    def test_real_image_urls_are_valid(self, image_segments: List[Dict[str, Any]]):
        """测试真实图片的 URL 格式有效"""
        if not image_segments:
            pytest.skip("No image segments in test data")

        for seg_data in image_segments:
            seg = parse_message_segment(seg_data)
            if seg.url:
                # URL 应该以 http:// 或 https:// 开头
                assert seg.url.startswith(("http://", "https://"))

    def test_real_image_serialization(self, image_segments: List[Dict[str, Any]]):
        """测试真实图片消息段的序列化"""
        if not image_segments:
            pytest.skip("No image segments in test data")

        for seg_data in image_segments:
            seg = parse_message_segment(seg_data)
            serialized = seg.to_dict()

            # 验证序列化后的结构
            assert "type" in serialized
            assert "data" in serialized
            assert serialized["type"] == "image"
            assert "file" in serialized["data"]
