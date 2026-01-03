"""
流式上传客户端

提供基于 WebSocket 的文件流式上传功能，使用 MessageRouter 发送请求。
"""

import base64
import hashlib
import uuid
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from ncatbot.utils import get_log
from .constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_FILE_RETENTION,
)

if TYPE_CHECKING:
    from ncatbot.core.service.builtin.message_router import MessageRouter

LOG = get_log("StreamUploadClient")


@dataclass
class ChunkInfo:
    """分片信息"""

    data: bytes
    index: int
    base64_data: str


@dataclass
class FileAnalysis:
    """文件分析结果"""

    chunks: List[ChunkInfo]
    sha256_hash: str
    total_size: int
    filename: str


@dataclass
class UploadResult:
    """上传结果"""

    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    sha256: Optional[str] = None
    error: Optional[str] = None


class StreamUploadClient:
    """
    流式上传客户端

    负责将本地文件通过 NapCat Stream API 上传到服务器。
    使用 MessageRouter 发送请求。
    """

    def __init__(
        self,
        message_router: "MessageRouter",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        file_retention: int = DEFAULT_FILE_RETENTION,
    ):
        """
        Args:
            message_router: 消息路由服务（用于发送请求）
            chunk_size: 分片大小（字节）
            file_retention: 文件保留时间（毫秒）
        """
        self._router = message_router
        self._chunk_size = chunk_size
        self._file_retention = file_retention

    def analyze_file(self, file_path: str) -> FileAnalysis:
        """
        分析文件，计算分片和哈希

        Args:
            file_path: 文件路径

        Returns:
            FileAnalysis: 包含分片、哈希和元信息
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        chunks: List[ChunkInfo] = []
        hasher = hashlib.sha256()
        total_size = 0
        chunk_index = 0

        with open(path, "rb") as f:
            while True:
                chunk = f.read(self._chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
                total_size += len(chunk)
                base64_data = base64.b64encode(chunk).decode("utf-8")
                chunks.append(
                    ChunkInfo(data=chunk, index=chunk_index, base64_data=base64_data)
                )
                chunk_index += 1

        return FileAnalysis(
            chunks=chunks,
            sha256_hash=hasher.hexdigest(),
            total_size=total_size,
            filename=path.name,
        )

    def analyze_bytes(self, data: bytes, filename: str) -> FileAnalysis:
        """
        分析字节数据

        Args:
            data: 字节数据
            filename: 文件名

        Returns:
            FileAnalysis: 包含分片、哈希和元信息
        """
        chunks: List[ChunkInfo] = []
        hasher = hashlib.sha256()
        hasher.update(data)

        offset = 0
        chunk_index = 0
        while offset < len(data):
            chunk = data[offset : offset + self._chunk_size]
            base64_data = base64.b64encode(chunk).decode("utf-8")
            chunks.append(
                ChunkInfo(data=chunk, index=chunk_index, base64_data=base64_data)
            )
            offset += self._chunk_size
            chunk_index += 1

        return FileAnalysis(
            chunks=chunks,
            sha256_hash=hasher.hexdigest(),
            total_size=len(data),
            filename=filename,
        )

    async def upload_file(self, file_path: str) -> UploadResult:
        """
        上传本地文件

        Args:
            file_path: 文件路径

        Returns:
            UploadResult: 上传结果
        """
        try:
            analysis = self.analyze_file(file_path)
            return await self._upload_chunks(analysis)
        except Exception as e:
            LOG.error(f"上传文件失败: {e}")
            return UploadResult(success=False, error=str(e))

    async def upload_bytes(self, data: bytes, filename: str) -> UploadResult:
        """
        上传字节数据

        Args:
            data: 字节数据
            filename: 文件名

        Returns:
            UploadResult: 上传结果
        """
        try:
            analysis = self.analyze_bytes(data, filename)
            return await self._upload_chunks(analysis)
        except Exception as e:
            LOG.error(f"上传字节数据失败: {e}")
            return UploadResult(success=False, error=str(e))

    async def _upload_chunks(self, analysis: FileAnalysis) -> UploadResult:
        """
        上传所有分片

        Args:
            analysis: 文件分析结果

        Returns:
            UploadResult: 上传结果
        """
        stream_id = str(uuid.uuid4())
        total_chunks = len(analysis.chunks)

        LOG.debug(
            f"开始上传: {analysis.filename}, "
            f"大小: {analysis.total_size}, 分片数: {total_chunks}"
        )

        # 上传所有分片
        for chunk in analysis.chunks:
            params = {
                "stream_id": stream_id,
                "chunk_data": chunk.base64_data,
                "chunk_index": chunk.index,
                "total_chunks": total_chunks,
                "file_size": analysis.total_size,
                "expected_sha256": analysis.sha256_hash,
                "filename": analysis.filename,
                "file_retention": self._file_retention,
            }

            response = await self._router.send("upload_file_stream", params)

            if response.get("status") != "ok":
                error_msg = response.get("message", "Unknown error")
                LOG.error(f"上传分片 {chunk.index} 失败: {error_msg}")
                return UploadResult(success=False, error=error_msg)

        # 发送完成信号
        complete_params = {
            "stream_id": stream_id,
            "is_complete": True,
        }

        response = await self._router.send("upload_file_stream", complete_params)

        if response.get("status") != "ok":
            error_msg = response.get("message", "Unknown error")
            return UploadResult(success=False, error=error_msg)

        result_data = response.get("data", {})

        if result_data.get("status") == "file_complete":
            LOG.info(f"文件上传成功: {result_data.get('file_path')}")
            return UploadResult(
                success=True,
                file_path=result_data.get("file_path"),
                file_size=result_data.get("file_size"),
                sha256=result_data.get("sha256"),
            )

        return UploadResult(
            success=False, error=f"意外的响应状态: {result_data.get('status')}"
        )
