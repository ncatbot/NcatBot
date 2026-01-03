"""
预上传结果类型定义
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class PreUploadResult:
    """
    预上传结果

    Attributes:
        success: 是否成功
        file_path: 上传后的文件路径（服务器路径或原始路径）
        original_path: 原始文件路径
        error: 错误信息
    """

    success: bool
    file_path: Optional[str] = None
    original_path: Optional[str] = None
    error: Optional[str] = None

    @property
    def uploaded(self) -> bool:
        """是否执行了上传（路径发生了变化）"""
        return self.success and self.file_path != self.original_path
