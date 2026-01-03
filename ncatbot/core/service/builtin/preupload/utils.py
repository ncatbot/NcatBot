"""
预上传工具函数
"""

import os
import re
import uuid
import base64 as b64
from pathlib import Path
from typing import Optional

# 可下载消息类型
DOWNLOADABLE_TYPES = frozenset({"image", "video", "record", "file"})

# Base64 前缀
BASE64_PREFIX = "base64://"

# HTTP(S) URL 模式
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

# File URL 前缀
FILE_PREFIX = "file://"


def is_local_file(file_value: str) -> bool:
    """
    判断是否为本地文件路径

    Args:
        file_value: file 字段值

    Returns:
        bool: 是否为本地文件
    """
    if not file_value or not isinstance(file_value, str):
        return False

    # file:// 协议
    if file_value.startswith(FILE_PREFIX):
        return True

    # 排除其他已知协议
    if file_value.startswith(BASE64_PREFIX):
        return False
    if URL_PATTERN.match(file_value):
        return False

    # 检查是否为有效路径
    # 绝对路径或相对路径形式
    if os.path.isabs(file_value):
        return True

    # 相对路径（包含路径分隔符）
    if os.sep in file_value or "/" in file_value:
        return True

    # 带扩展名的文件名（可能是相对路径）
    if "." in file_value and not file_value.startswith("."):
        return True

    return False


def is_base64_data(file_value: str) -> bool:
    """
    判断是否为 Base64 数据

    Args:
        file_value: file 字段值

    Returns:
        bool: 是否为 Base64 数据
    """
    if not file_value or not isinstance(file_value, str):
        return False
    return file_value.startswith(BASE64_PREFIX)


def is_remote_url(file_value: str) -> bool:
    """
    判断是否为远程 URL

    Args:
        file_value: file 字段值

    Returns:
        bool: 是否为远程 URL
    """
    if not file_value or not isinstance(file_value, str):
        return False
    return bool(URL_PATTERN.match(file_value))


def needs_upload(file_value: str) -> bool:
    """
    判断是否需要预上传

    本地文件和 Base64 数据需要上传，远程 URL 不需要。

    Args:
        file_value: file 字段值

    Returns:
        bool: 是否需要上传
    """
    return is_local_file(file_value) or is_base64_data(file_value)


def get_local_path(file_value: str) -> Optional[str]:
    """
    从 file 值提取本地文件路径

    Args:
        file_value: file 字段值

    Returns:
        Optional[str]: 本地文件路径，如果不是本地文件则返回 None
    """
    if not is_local_file(file_value):
        return None

    # 移除 file:// 前缀
    if file_value.startswith(FILE_PREFIX):
        return file_value[len(FILE_PREFIX) :]

    return file_value


def resolve_file_path(file_value: str, base_dir: Optional[str] = None) -> str:
    """
    解析文件路径为绝对路径

    Args:
        file_value: file 字段值
        base_dir: 基础目录（用于解析相对路径）

    Returns:
        str: 绝对路径
    """
    local_path = get_local_path(file_value)
    if not local_path:
        return file_value

    path = Path(local_path)

    if path.is_absolute():
        return str(path)

    if base_dir:
        return str(Path(base_dir) / path)

    return str(path.resolve())


def extract_base64_data(file_value: str) -> Optional[bytes]:
    """
    从 Base64 字符串提取字节数据

    Args:
        file_value: Base64 编码的文件数据

    Returns:
        Optional[bytes]: 解码后的字节数据
    """
    if not is_base64_data(file_value):
        return None

    try:
        b64_str = file_value[len(BASE64_PREFIX) :]
        return b64.b64decode(b64_str)
    except Exception:
        return None


def generate_filename_from_type(msg_type: str) -> str:
    """
    根据消息类型生成默认文件名

    Args:
        msg_type: 消息类型

    Returns:
        str: 默认文件名
    """
    extensions = {
        "image": ".jpg",
        "video": ".mp4",
        "record": ".mp3",
        "file": ".bin",
    }

    ext = extensions.get(msg_type, ".bin")
    return f"{uuid.uuid4().hex[:8]}{ext}"
