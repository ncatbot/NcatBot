"""
预上传常量定义
"""

from enum import Enum


# 默认分片大小 500KB
DEFAULT_CHUNK_SIZE = 500 * 1024

# 默认文件保留时间 600秒（毫秒）
DEFAULT_FILE_RETENTION = 600 * 1000


class StreamStatus(str, Enum):
    """流传输状态"""

    NORMAL_ACTION = "normal-action"
    STREAM_ACTION = "stream-action"


class StreamResponseType(str, Enum):
    """流响应类型"""

    STREAM = "stream"  # 传输中
    RESPONSE = "response"  # 传输完成
    ERROR = "error"  # 传输失败
