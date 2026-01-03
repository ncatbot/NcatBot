"""
预上传服务 - 提供统一的预上传功能入口，使用 message_router 的连接。
"""

from typing import Any, Dict, List, Optional

from ncatbot.utils import get_log
from ...base import BaseService
from .client import StreamUploadClient, UploadResult
from .processor import MessagePreUploadProcessor, ProcessResult
from .result import PreUploadResult
from .constants import DEFAULT_CHUNK_SIZE, DEFAULT_FILE_RETENTION
from .utils import (
    is_local_file,
    is_base64_data,
    is_remote_url,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
)

LOG = get_log("PreUploadService")


class PreUploadService(BaseService):
    """预上传服务 - 消息预上传 + 文件预上传，使用 message_router 的连接。"""

    name = "preupload"
    description = "消息和文件预上传服务"

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        file_retention: int = DEFAULT_FILE_RETENTION,
        **config,
    ):
        super().__init__(**config)
        self._chunk_size = chunk_size
        self._file_retention = file_retention
        self._client: Optional[StreamUploadClient] = None
        self._message_processor: Optional[MessagePreUploadProcessor] = None

    async def on_load(self) -> None:
        """服务加载 - 使用 message_router 的连接"""
        if not self.service_manager:
            raise RuntimeError("PreUploadService 需要 ServiceManager 注入")

        # 获取 message_router 服务
        message_router = self.service_manager.message_router
        if not message_router:
            raise RuntimeError(
                "PreUploadService 依赖 message_router 服务，请先注册并加载"
            )

        # 使用 message_router 创建客户端
        self._client = StreamUploadClient(
            message_router, self._chunk_size, self._file_retention
        )
        self._message_processor = MessagePreUploadProcessor(self._client)
        LOG.info("预上传服务已加载（使用 message_router 连接）")

    async def on_close(self) -> None:
        """服务关闭"""
        self._message_processor = None
        self._client = None
        LOG.info("预上传服务已关闭")

    # -------------------------------------------------------------------------
    # 底层上传接口
    # -------------------------------------------------------------------------

    async def upload_file(self, file_path: str) -> UploadResult:
        """上传本地文件"""
        if not self._client:
            return UploadResult(success=False, error="预上传服务未初始化")
        return await self._client.upload_file(file_path)

    async def upload_bytes(self, data: bytes, filename: str) -> UploadResult:
        """上传字节数据"""
        if not self._client:
            return UploadResult(success=False, error="预上传服务未初始化")
        return await self._client.upload_bytes(data, filename)

    # -------------------------------------------------------------------------
    # 消息预上传接口
    # -------------------------------------------------------------------------

    async def process_message(self, data: Dict[str, Any]) -> ProcessResult:
        """处理消息数据，上传所有需要预上传的文件"""
        if not self._message_processor:
            return ProcessResult(success=False, errors=["预上传服务未初始化"])
        return await self._message_processor.process(data)

    async def process_message_array(
        self, messages: List[Dict[str, Any]]
    ) -> ProcessResult:
        """处理消息数组"""
        if not self._message_processor:
            return ProcessResult(success=False, errors=["预上传服务未初始化"])
        return await self._message_processor.process_message_array(messages)

    # -------------------------------------------------------------------------
    # 文件预上传接口
    # -------------------------------------------------------------------------

    async def preupload_file(
        self, file_value: str, file_type: str = "file"
    ) -> PreUploadResult:
        """预上传单个文件（本地路径、Base64 或 URL）"""
        if not self._client:
            return PreUploadResult(success=False, error="预上传服务未初始化")
        if not file_value:
            return PreUploadResult(success=False, error="文件路径为空")

        # 远程 URL 不需要上传
        if is_remote_url(file_value):
            return PreUploadResult(
                success=True, file_path=file_value, original_path=file_value
            )
        # 本地文件上传
        if is_local_file(file_value):
            return await self._upload_local(file_value)
        # Base64 数据上传
        if is_base64_data(file_value):
            return await self._upload_base64(file_value, file_type)
        # 未知格式，直接返回
        return PreUploadResult(
            success=True, file_path=file_value, original_path=file_value
        )

    async def preupload_file_if_needed(
        self, file_value: str, file_type: str = "file"
    ) -> str:
        """如果需要则预上传文件，返回最终路径。失败抛出 RuntimeError。"""
        result = await self.preupload_file(file_value, file_type)
        if not result.success:
            raise RuntimeError(f"文件预上传失败: {result.error}")
        return result.file_path

    async def _upload_local(self, file_value: str) -> PreUploadResult:
        """上传本地文件"""
        local_path = get_local_path(file_value)
        if not local_path:
            return PreUploadResult(
                success=False, original_path=file_value, error="无法解析本地文件路径"
            )

        result = await self._client.upload_file(local_path)
        if result.success:
            LOG.debug(f"文件预上传成功: {local_path} -> {result.file_path}")
            return PreUploadResult(
                success=True, file_path=result.file_path, original_path=file_value
            )
        return PreUploadResult(
            success=False, original_path=file_value, error=result.error
        )

    async def _upload_base64(self, file_value: str, file_type: str) -> PreUploadResult:
        """上传 Base64 数据"""
        data = extract_base64_data(file_value)
        if not data:
            return PreUploadResult(
                success=False, original_path=file_value, error="Base64 解码失败"
            )

        filename = generate_filename_from_type(file_type)
        result = await self._client.upload_bytes(data, filename)
        if result.success:
            LOG.debug(f"Base64 预上传成功: {file_value[:30]}... -> {result.file_path}")
            return PreUploadResult(
                success=True, file_path=result.file_path, original_path=file_value
            )
        return PreUploadResult(
            success=False, original_path=file_value, error=result.error
        )

    # -------------------------------------------------------------------------
    # 属性访问
    # -------------------------------------------------------------------------

    @property
    def client(self) -> Optional[StreamUploadClient]:
        """获取上传客户端"""
        return self._client

    @property
    def message_processor(self) -> Optional[MessagePreUploadProcessor]:
        """获取消息处理器"""
        return self._message_processor

    @property
    def available(self) -> bool:
        """服务是否可用"""
        return self._loaded and self._client is not None
