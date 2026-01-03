"""
流式上传客户端测试
"""

import pytest
import hashlib
import base64
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

from ncatbot.core.service.builtin.preupload.client import (
    StreamUploadClient,
)


@pytest.fixture
def mock_message_router():
    """创建模拟的 MessageRouter"""
    router = MagicMock()
    router.send = AsyncMock()
    return router


@pytest.fixture
def upload_client(mock_message_router):
    """创建上传客户端"""
    return StreamUploadClient(mock_message_router, chunk_size=1024)


@pytest.fixture
def temp_file():
    """创建临时测试文件"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        content = b"Hello World! " * 100
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


class TestFileAnalysis:
    """测试文件分析功能"""

    def test_analyze_small_file(self, upload_client, temp_file):
        """测试分析小文件"""
        analysis = upload_client.analyze_file(temp_file)

        assert analysis.total_size > 0
        assert len(analysis.chunks) > 0
        assert analysis.sha256_hash
        assert analysis.filename

    def test_analyze_bytes(self, upload_client):
        """测试分析字节数据"""
        data = b"Test data for upload"
        analysis = upload_client.analyze_bytes(data, "test.bin")

        assert analysis.total_size == len(data)
        assert len(analysis.chunks) >= 1
        assert analysis.filename == "test.bin"

        # 验证 SHA256
        expected_hash = hashlib.sha256(data).hexdigest()
        assert analysis.sha256_hash == expected_hash

    def test_analyze_bytes_chunks(self, upload_client):
        """测试字节数据分片"""
        # 创建大于 chunk_size 的数据
        data = b"X" * 3000  # 3KB, chunk_size=1KB
        analysis = upload_client.analyze_bytes(data, "large.bin")

        assert len(analysis.chunks) == 3
        assert analysis.chunks[0].index == 0
        assert analysis.chunks[1].index == 1
        assert analysis.chunks[2].index == 2

    def test_chunk_base64_encoding(self, upload_client):
        """测试分片 Base64 编码"""
        data = b"Hello"
        analysis = upload_client.analyze_bytes(data, "test.txt")

        chunk = analysis.chunks[0]
        decoded = base64.b64decode(chunk.base64_data)
        assert decoded == data

    def test_analyze_nonexistent_file(self, upload_client):
        """测试分析不存在的文件"""
        with pytest.raises(FileNotFoundError):
            upload_client.analyze_file("/nonexistent/file.txt")


class TestUploadFile:
    """测试文件上传"""

    @pytest.mark.asyncio
    async def test_upload_success(self, upload_client, mock_message_router, temp_file):
        """测试成功上传"""
        # 模拟分片上传响应
        mock_message_router.send.side_effect = [
            {"status": "ok", "data": {"received_chunks": 1}},
            {"status": "ok", "data": {"received_chunks": 2}},
            # 完成响应
            {
                "status": "ok",
                "data": {
                    "status": "file_complete",
                    "file_path": "/server/uploaded.txt",
                    "file_size": 1300,
                    "sha256": "abc123",
                },
            },
        ]

        result = await upload_client.upload_file(temp_file)

        assert result.success
        assert result.file_path == "/server/uploaded.txt"

    @pytest.mark.asyncio
    async def test_upload_chunk_failure(
        self, upload_client, mock_message_router, temp_file
    ):
        """测试分片上传失败"""
        mock_message_router.send.return_value = {
            "status": "failed",
            "message": "Chunk upload failed",
        }

        result = await upload_client.upload_file(temp_file)

        assert not result.success
        assert result.error

    @pytest.mark.asyncio
    async def test_upload_bytes_success(self, upload_client, mock_message_router):
        """测试成功上传字节数据"""
        mock_message_router.send.side_effect = [
            {"status": "ok", "data": {"received_chunks": 1}},
            {
                "status": "ok",
                "data": {
                    "status": "file_complete",
                    "file_path": "/server/bytes.bin",
                    "file_size": 100,
                    "sha256": "def456",
                },
            },
        ]

        result = await upload_client.upload_bytes(b"Test data", "test.bin")

        assert result.success
        assert result.file_path == "/server/bytes.bin"


class TestUploadParameters:
    """测试上传参数"""

    @pytest.mark.asyncio
    async def test_upload_sends_correct_params(
        self, upload_client, mock_message_router
    ):
        """测试上传发送正确的参数"""
        mock_message_router.send.side_effect = [
            {"status": "ok", "data": {}},
            {"status": "ok", "data": {"status": "file_complete", "file_path": "/test"}},
        ]

        await upload_client.upload_bytes(b"Test", "test.txt")

        # 检查第一次调用（分片上传）
        first_call = mock_message_router.send.call_args_list[0]
        assert first_call[0][0] == "upload_file_stream"
        params = first_call[0][1]

        assert "stream_id" in params
        assert "chunk_data" in params
        assert params["chunk_index"] == 0
        assert params["total_chunks"] >= 1
        assert params["filename"] == "test.txt"
        assert "file_retention" in params

    @pytest.mark.asyncio
    async def test_upload_complete_signal(self, upload_client, mock_message_router):
        """测试发送完成信号"""
        mock_message_router.send.side_effect = [
            {"status": "ok", "data": {}},
            {"status": "ok", "data": {"status": "file_complete", "file_path": "/test"}},
        ]

        await upload_client.upload_bytes(b"Test", "test.txt")

        # 检查最后一次调用（完成信号）
        last_call = mock_message_router.send.call_args_list[-1]
        params = last_call[0][1]

        assert params.get("is_complete") is True
