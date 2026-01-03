"""
文件监视服务

监视插件目录中的文件变化，通过回调通知调用方进行插件热重载。
"""

from .service import FileWatcherService

__all__ = ["FileWatcherService"]
