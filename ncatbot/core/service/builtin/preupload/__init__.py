"""
预上传服务

提供消息和文件的预上传功能，包括流式上传。
使用 message_router 的连接。
"""

from .service import PreUploadService

__all__ = ["PreUploadService"]
