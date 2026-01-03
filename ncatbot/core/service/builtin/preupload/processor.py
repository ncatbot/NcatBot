"""
消息预上传处理器

遍历消息结构，对需要上传的文件进行预上传处理。
"""

import copy
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from ncatbot.utils import get_log
from .utils import (
    DOWNLOADABLE_TYPES,
    needs_upload,
    is_local_file,
    is_base64_data,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
)

if TYPE_CHECKING:
    from .client import StreamUploadClient

LOG = get_log("MessagePreUploadProcessor")


@dataclass
class ProcessResult:
    """处理结果"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    uploaded_count: int = 0


class MessagePreUploadProcessor:
    """
    消息预上传处理器

    遍历消息字典结构，识别需要上传的文件，执行上传后替换路径。
    支持：
    - 单条消息段
    - 消息数组
    - 嵌套的 Forward/Node 结构
    """

    def __init__(self, upload_client: "StreamUploadClient"):
        """
        Args:
            upload_client: 流式上传客户端实例
        """
        self._client = upload_client

    async def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        处理消息数据，上传所有需要预上传的文件

        Args:
            data: 序列化后的消息字典（单个消息段或消息数组）

        Returns:
            ProcessResult: 处理结果
        """
        errors: List[str] = []
        uploaded_count = 0

        # 深拷贝避免修改原数据
        result_data = copy.deepcopy(data)

        try:
            uploaded_count = await self._process_node(result_data, errors)
            return ProcessResult(
                success=len(errors) == 0,
                data=result_data,
                errors=errors,
                uploaded_count=uploaded_count,
            )
        except Exception as e:
            LOG.error(f"消息预处理失败: {e}")
            errors.append(str(e))
            return ProcessResult(
                success=False,
                data=result_data,
                errors=errors,
                uploaded_count=uploaded_count,
            )

    async def process_message_array(
        self, messages: List[Dict[str, Any]]
    ) -> ProcessResult:
        """
        处理消息数组

        Args:
            messages: 消息段列表

        Returns:
            ProcessResult: 处理结果
        """
        errors: List[str] = []
        total_uploaded = 0
        result = copy.deepcopy(messages)

        for i, msg in enumerate(result):
            try:
                count = await self._process_node(msg, errors)
                total_uploaded += count
            except Exception as e:
                LOG.error(f"处理消息段 {i} 失败: {e}")
                errors.append(f"消息段 {i}: {e}")

        return ProcessResult(
            success=len(errors) == 0,
            data={"message": result},
            errors=errors,
            uploaded_count=total_uploaded,
        )

    async def _process_node(self, node: Any, errors: List[str]) -> int:
        """
        递归处理节点

        Args:
            node: 当前节点（可能是 dict、list 或其他）
            errors: 错误收集列表

        Returns:
            int: 上传的文件数量
        """
        uploaded_count = 0

        if isinstance(node, dict):
            uploaded_count += await self._process_dict(node, errors)
        elif isinstance(node, list):
            for item in node:
                uploaded_count += await self._process_node(item, errors)

        return uploaded_count

    async def _process_dict(self, node: Dict[str, Any], errors: List[str]) -> int:
        """
        处理字典节点

        Args:
            node: 字典节点
            errors: 错误收集列表

        Returns:
            int: 上传的文件数量
        """
        uploaded_count = 0
        msg_type = node.get("type")

        # 检查是否是可下载消息类型
        if msg_type in DOWNLOADABLE_TYPES:
            count = await self._process_downloadable(node, errors)
            uploaded_count += count

        # 处理 Forward 的 content
        if msg_type == "forward":
            content = node.get("data", {}).get("content")
            if content:
                uploaded_count += await self._process_node(content, errors)

        # 处理 Node 的 content（可能在 data 中）
        if msg_type == "node":
            data = node.get("data", {})
            # Node content 可能是消息数组
            content = data.get("content")
            if content:
                uploaded_count += await self._process_node(content, errors)
            # 也可能是 message 字段
            message = data.get("message")
            if message:
                uploaded_count += await self._process_node(message, errors)

        # 递归处理所有字典值
        for key, value in node.items():
            if key in ("type", "data"):
                continue
            uploaded_count += await self._process_node(value, errors)

        return uploaded_count

    async def _process_downloadable(
        self, node: Dict[str, Any], errors: List[str]
    ) -> int:
        """
        处理可下载消息段

        Args:
            node: 消息段字典
            errors: 错误收集列表

        Returns:
            int: 上传的文件数量（0 或 1）
        """
        data = node.get("data", {})
        file_value = data.get("file")

        if not file_value or not needs_upload(file_value):
            return 0

        msg_type = node.get("type", "file")

        try:
            if is_local_file(file_value):
                result = await self._upload_local_file(file_value)
            elif is_base64_data(file_value):
                result = await self._upload_base64(file_value, msg_type)
            else:
                return 0

            if result:
                data["file"] = result
                LOG.debug(f"文件已上传: {file_value[:50]}... -> {result}")
                return 1
            else:
                errors.append(f"上传失败: {file_value[:50]}...")
                return 0

        except Exception as e:
            LOG.error(f"处理文件失败: {e}")
            errors.append(f"文件处理错误: {e}")
            return 0

    async def _upload_local_file(self, file_value: str) -> Optional[str]:
        """
        上传本地文件

        Args:
            file_value: file 字段值

        Returns:
            Optional[str]: 上传后的文件路径
        """
        local_path = get_local_path(file_value)
        if not local_path:
            return None

        result = await self._client.upload_file(local_path)
        return result.file_path if result.success else None

    async def _upload_base64(self, file_value: str, msg_type: str) -> Optional[str]:
        """
        上传 Base64 数据

        Args:
            file_value: Base64 编码的数据
            msg_type: 消息类型

        Returns:
            Optional[str]: 上传后的文件路径
        """
        data = extract_base64_data(file_value)
        if not data:
            return None

        filename = generate_filename_from_type(msg_type)
        result = await self._client.upload_bytes(data, filename)
        return result.file_path if result.success else None
