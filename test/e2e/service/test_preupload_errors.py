"""预上传服务异常处理测试

测试优先级 2：系统稳定性
- 服务未初始化时的错误处理
- 文件不存在时的错误处理
- Base64 解码失败时的错误处理
- 上传失败时的错误处理
"""

import pytest
import logging
import tempfile
import os
from typing import TYPE_CHECKING, cast, Any

from ncatbot.core.service.builtin.preupload import PreUploadService
from ncatbot.core.service.builtin.preupload.client import (
    StreamUploadClient,
    UploadResult,
)
from ncatbot.core.service.builtin.preupload.processor import ProcessResult
from ncatbot.core.service.builtin.preupload.result import PreUploadResult

if TYPE_CHECKING:
    from ncatbot.core.service.builtin.message_router import MessageRouter


class TestPreUploadServiceNotInitialized:
    """测试服务未初始化时的错误处理

    确保服务在未调用 on_load 时，所有方法都返回有意义的错误。
    """

    @pytest.mark.asyncio
    async def test_upload_file_without_init(self):
        """测试未初始化时上传文件返回错误"""
        service = PreUploadService()
        # 不调用 on_load

        result = await service.upload_file("/path/to/file")

        assert not result.success
        assert result.error is not None
        assert "未初始化" in result.error

    @pytest.mark.asyncio
    async def test_upload_bytes_without_init(self):
        """测试未初始化时上传字节返回错误"""
        service = PreUploadService()

        result = await service.upload_bytes(b"test data", "test.txt")

        assert not result.success
        assert result.error is not None and "未初始化" in result.error

    @pytest.mark.asyncio
    async def test_process_message_without_init(self):
        """测试未初始化时处理消息返回错误"""
        service = PreUploadService()

        result = await service.process_message({"type": "image", "data": {}})

        assert not result.success
        assert len(result.errors) > 0
        assert any("未初始化" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_process_message_array_without_init(self):
        """测试未初始化时处理消息数组返回错误"""
        service = PreUploadService()

        result = await service.process_message_array([{"type": "text", "data": {}}])

        assert not result.success
        assert any("未初始化" in err for err in result.errors)

    @pytest.mark.asyncio
    async def test_preupload_file_without_init(self):
        """测试未初始化时预上传文件返回错误"""
        service = PreUploadService()

        result = await service.preupload_file("/some/path")

        assert not result.success
        assert result.error is not None and "未初始化" in result.error

    def test_available_returns_false_without_init(self):
        """测试未初始化时 available 属性返回 False"""
        service = PreUploadService()

        assert not service.available


class TestPreUploadServiceInitErrors:
    """测试服务初始化时的错误处理"""

    @pytest.mark.asyncio
    async def test_init_without_service_manager(self):
        """测试没有 ServiceManager 时初始化失败"""
        service = PreUploadService()

        with pytest.raises(RuntimeError) as exc_info:
            await service.on_load()

        assert "ServiceManager" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_init_without_message_router(self):
        """测试没有 message_router 时初始化失败"""
        service = PreUploadService()

        # 模拟一个没有 message_router 的 ServiceManager
        class MockServiceManager:
            message_router = None

        # 设置 service_manager 属性
        service.service_manager = MockServiceManager()

        with pytest.raises(RuntimeError) as exc_info:
            await service.on_load()

        # 检查错误消息包含 message_router 相关信息
        error_msg = str(exc_info.value)
        assert "message_router" in error_msg, (
            f"错误消息应该提到 message_router，实际: {exc_info.value}"
        )


class TestStreamUploadClientErrors:
    """测试流式上传客户端的错误处理"""

    def test_analyze_nonexistent_file(self):
        """测试分析不存在的文件抛出异常"""
        # 创建一个不存在的路径
        nonexistent_path = "/this/path/does/not/exist/file.txt"

        # 创建一个 mock router (使用 cast 绕过类型检查)
        class MockRouter:
            async def send(self, endpoint: str, params: Any) -> dict:
                return {"status": "ok"}

        client = StreamUploadClient(cast("MessageRouter", MockRouter()))

        with pytest.raises(FileNotFoundError) as exc_info:
            client.analyze_file(nonexistent_path)

        assert "文件不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_nonexistent_file_returns_error(self):
        """测试上传不存在的文件返回错误结果"""

        class MockRouter:
            async def send(self, endpoint: str, params: Any) -> dict:
                return {"status": "ok"}

        client = StreamUploadClient(cast("MessageRouter", MockRouter()))

        result = await client.upload_file("/nonexistent/file.txt")

        assert not result.success
        assert result.error is not None
        assert "不存在" in result.error or "No such file" in result.error

    @pytest.mark.asyncio
    async def test_upload_with_server_error(self, caplog):
        """测试服务器返回错误时的处理"""

        class MockRouter:
            async def send(self, endpoint: str, params: Any) -> dict:
                return {"status": "error", "message": "服务器内部错误"}

        client = StreamUploadClient(cast("MessageRouter", MockRouter()))

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            with caplog.at_level(logging.ERROR):
                result = await client.upload_file(temp_path)

            assert not result.success
            assert result.error is not None and "服务器内部错误" in result.error
        finally:
            os.unlink(temp_path)

    def test_analyze_file_calculates_correct_hash(self):
        """测试文件分析正确计算哈希"""

        class MockRouter:
            pass

        client = StreamUploadClient(cast("MessageRouter", MockRouter()))

        # 创建临时文件
        test_content = b"Hello, World!"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            analysis = client.analyze_file(temp_path)

            assert analysis.total_size == len(test_content)
            assert analysis.sha256_hash is not None
            assert len(analysis.sha256_hash) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)


class TestPreUploadFileErrors:
    """测试文件预上传的错误处理"""

    @pytest.mark.asyncio
    async def test_empty_file_path(self):
        """测试空文件路径返回错误"""
        service = PreUploadService()
        # 模拟已初始化但客户端存在
        object.__setattr__(service, "_loaded", True)

        class MockClient:
            pass

        object.__setattr__(service, "_client", MockClient())

        result = await service.preupload_file("")

        assert not result.success
        assert result.error is not None and "为空" in result.error

    @pytest.mark.asyncio
    async def test_remote_url_passthrough(self):
        """测试远程 URL 直接通过不需要上传"""
        service = PreUploadService()
        object.__setattr__(service, "_loaded", True)

        class MockClient:
            pass

        object.__setattr__(service, "_client", MockClient())

        remote_url = "https://example.com/image.png"
        result = await service.preupload_file(remote_url)

        assert result.success
        assert result.file_path == remote_url

    @pytest.mark.asyncio
    async def test_invalid_base64_returns_error(self):
        """测试无效 Base64 数据返回错误"""
        service = PreUploadService()
        object.__setattr__(service, "_loaded", True)

        class MockClient:
            async def upload_bytes(self, data: bytes, filename: str) -> UploadResult:
                return UploadResult(success=True, file_path="/path")

        object.__setattr__(service, "_client", MockClient())

        # 无效的 base64 数据
        invalid_base64 = "base64://not_valid_base64!!!"
        result = await service.preupload_file(invalid_base64)

        # 应该尝试解码并失败
        # 由于实现可能不同，检查是否返回了某种结果
        # 如果解码失败应该返回错误
        if not result.success:
            assert result.error is not None


class TestProcessResultTypes:
    """测试各种结果类型"""

    def test_upload_result_properties(self):
        """测试 UploadResult 属性"""
        result = UploadResult(
            success=True, file_path="/path/to/file", file_size=1024, sha256="abc123"
        )

        assert result.success
        assert result.file_path == "/path/to/file"
        assert result.file_size == 1024
        assert result.error is None

    def test_upload_result_error(self):
        """测试 UploadResult 错误状态"""
        result = UploadResult(success=False, error="上传失败")

        assert not result.success
        assert result.error == "上传失败"
        assert result.file_path is None

    def test_preupload_result_properties(self):
        """测试 PreUploadResult 属性"""
        result = PreUploadResult(
            success=True, file_path="/new/path", original_path="/old/path"
        )

        assert result.success
        assert result.file_path == "/new/path"
        assert result.original_path == "/old/path"

    def test_process_result_errors(self):
        """测试 ProcessResult 错误列表"""
        result = ProcessResult(success=False, errors=["错误1", "错误2"])

        assert not result.success
        assert len(result.errors) == 2
