"""
消息预上传处理器测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ncatbot.core.service.builtin.preupload.processor import (
    MessagePreUploadProcessor,
)
from ncatbot.core.service.builtin.preupload.client import UploadResult


@pytest.fixture
def mock_upload_service():
    """创建模拟的上传服务"""
    service = MagicMock()
    service.upload_file = AsyncMock(
        return_value=UploadResult(
            success=True,
            file_path="/uploaded/path/file.jpg",
            file_size=1024,
            sha256="abc123",
        )
    )
    service.upload_bytes = AsyncMock(
        return_value=UploadResult(
            success=True,
            file_path="/uploaded/path/base64_file.jpg",
            file_size=512,
            sha256="def456",
        )
    )
    return service


@pytest.fixture
def processor(mock_upload_service):
    """创建处理器实例"""
    return MessagePreUploadProcessor(mock_upload_service)


class TestMessagePreUploadProcessor:
    """测试 MessagePreUploadProcessor"""

    @pytest.mark.asyncio
    async def test_process_simple_image(self, processor, mock_upload_service):
        """测试处理简单图片消息"""
        data = {"type": "image", "data": {"file": "/path/to/image.jpg"}}

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1
        assert result.data["data"]["file"] == "/uploaded/path/file.jpg"
        mock_upload_service.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_remote_url_no_upload(self, processor, mock_upload_service):
        """测试远程 URL 不上传"""
        data = {
            "type": "image",
            "data": {
                "file": "http://example.com/image.jpg",
                "url": "http://example.com/image.jpg",
            },
        }

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 0
        # 文件路径应保持不变
        assert result.data["data"]["file"] == "http://example.com/image.jpg"
        mock_upload_service.upload_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_base64_image(self, processor, mock_upload_service):
        """测试处理 Base64 图片"""
        data = {"type": "image", "data": {"file": "base64://SGVsbG8gV29ybGQ="}}

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1
        assert result.data["data"]["file"] == "/uploaded/path/base64_file.jpg"
        mock_upload_service.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_text_message_no_upload(self, processor, mock_upload_service):
        """测试文本消息不触发上传"""
        data = {"type": "text", "data": {"text": "Hello World"}}

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 0
        mock_upload_service.upload_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_video(self, processor, mock_upload_service):
        """测试处理视频消息"""
        data = {"type": "video", "data": {"file": "/path/to/video.mp4"}}

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1

    @pytest.mark.asyncio
    async def test_process_record(self, processor, mock_upload_service):
        """测试处理语音消息"""
        data = {"type": "record", "data": {"file": "/path/to/audio.mp3"}}

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1


class TestProcessMessageArray:
    """测试消息数组处理"""

    @pytest.mark.asyncio
    async def test_process_mixed_array(self, processor, mock_upload_service):
        """测试处理混合消息数组"""
        messages = [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "/path/to/image.jpg"}},
            {"type": "at", "data": {"qq": "123456"}},
            {"type": "image", "data": {"file": "http://example.com/img.jpg"}},
        ]

        result = await processor.process_message_array(messages)

        assert result.success
        # 只有本地图片需要上传
        assert result.uploaded_count == 1

    @pytest.mark.asyncio
    async def test_process_empty_array(self, processor, mock_upload_service):
        """测试处理空数组"""
        result = await processor.process_message_array([])

        assert result.success
        assert result.uploaded_count == 0


class TestForwardMessageProcessing:
    """测试转发消息处理"""

    @pytest.mark.asyncio
    async def test_process_forward_with_nested_image(
        self, processor, mock_upload_service
    ):
        """测试处理嵌套图片的转发消息"""
        data = {
            "type": "forward",
            "data": {
                "id": "12345",
                "content": [
                    {
                        "type": "node",
                        "data": {
                            "user_id": "111",
                            "nickname": "User1",
                            "content": [
                                {
                                    "type": "image",
                                    "data": {"file": "/path/to/nested.jpg"},
                                }
                            ],
                        },
                    }
                ],
            },
        }

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1

    @pytest.mark.asyncio
    async def test_process_deeply_nested_forward(self, processor, mock_upload_service):
        """测试处理深度嵌套的转发消息"""
        data = {
            "type": "forward",
            "data": {
                "content": [
                    {
                        "type": "node",
                        "data": {
                            "user_id": "111",
                            "nickname": "User1",
                            "content": [
                                {
                                    "type": "forward",
                                    "data": {
                                        "content": [
                                            {
                                                "type": "node",
                                                "data": {
                                                    "user_id": "222",
                                                    "nickname": "User2",
                                                    "content": [
                                                        {
                                                            "type": "image",
                                                            "data": {
                                                                "file": "/deep/nested.jpg"
                                                            },
                                                        }
                                                    ],
                                                },
                                            }
                                        ]
                                    },
                                }
                            ],
                        },
                    }
                ]
            },
        }

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 1

    @pytest.mark.asyncio
    async def test_process_forward_with_multiple_nodes(
        self, processor, mock_upload_service
    ):
        """测试处理多节点转发消息"""
        data = {
            "type": "forward",
            "data": {
                "content": [
                    {
                        "type": "node",
                        "data": {
                            "user_id": "111",
                            "nickname": "User1",
                            "content": [
                                {"type": "image", "data": {"file": "/img1.jpg"}}
                            ],
                        },
                    },
                    {
                        "type": "node",
                        "data": {
                            "user_id": "222",
                            "nickname": "User2",
                            "content": [
                                {"type": "image", "data": {"file": "/img2.jpg"}}
                            ],
                        },
                    },
                ]
            },
        }

        result = await processor.process(data)

        assert result.success
        assert result.uploaded_count == 2
