"""
预上传相关 API 处理器
"""
# pyright: reportAttributeAccessIssue=false

import hashlib
from typing import Dict


class UploadHandlerMixin:
    """预上传 API 处理器 Mixin"""

    def _register_upload_handlers(self) -> None:
        """注册预上传相关 API 处理器"""
        # 流式上传存储（stream_id -> {chunks, metadata}）
        self._upload_streams: Dict[str, dict] = {}

        upload_handlers = {
            "upload_file_stream": self._handle_upload_file_stream,
        }
        self._handlers.update(upload_handlers)

    def _handle_upload_file_stream(self, params: dict) -> dict:
        """
        处理流式文件上传

        支持分片上传，每次上传一个分片，最后完成时返回文件路径。
        """
        stream_id = params.get("stream_id")
        if not stream_id:
            return self._error_response("缺少 stream_id 参数")

        # 检查是否是完成信号
        if params.get("is_complete"):
            return self._complete_upload(stream_id)

        # 处理分片上传
        chunk_data = params.get("chunk_data")
        chunk_index = params.get("chunk_index", 0)
        total_chunks = params.get("total_chunks", 1)
        file_size = params.get("file_size", 0)
        filename = params.get("filename", "unknown")
        expected_sha256 = params.get("expected_sha256", "")

        if not chunk_data:
            return self._error_response("缺少 chunk_data 参数")

        # 初始化或获取上传流
        if stream_id not in self._upload_streams:
            self._upload_streams[stream_id] = {
                "chunks": {},
                "total_chunks": total_chunks,
                "file_size": file_size,
                "filename": filename,
                "expected_sha256": expected_sha256,
            }

        stream = self._upload_streams[stream_id]
        stream["chunks"][chunk_index] = chunk_data

        return self._success_response(
            {
                "status": "chunk_received",
                "chunk_index": chunk_index,
                "received_chunks": len(stream["chunks"]),
                "total_chunks": total_chunks,
            }
        )

    def _complete_upload(self, stream_id: str) -> dict:
        """完成文件上传"""
        if stream_id not in self._upload_streams:
            return self._error_response(f"未找到上传流: {stream_id}")

        stream = self._upload_streams[stream_id]
        filename = stream["filename"]
        file_size = stream["file_size"]

        # 生成模拟的文件路径
        file_hash = hashlib.md5(stream_id.encode()).hexdigest()[:8]
        file_path = f"/mock/uploads/{file_hash}_{filename}"

        # 计算 SHA256（模拟）
        sha256 = (
            stream.get("expected_sha256")
            or hashlib.sha256(stream_id.encode()).hexdigest()
        )

        # 清理上传流
        del self._upload_streams[stream_id]

        return self._success_response(
            {
                "status": "file_complete",
                "file_path": file_path,
                "file_size": file_size,
                "sha256": sha256,
            }
        )
