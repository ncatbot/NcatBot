"""
服务层

提供可动态加载/卸载的内部服务，完全不依赖其他 ncatbot 模块（除 utils）。
"""

from .base import BaseService
from .manager import ServiceManager

__all__ = [
    "BaseService",
    "ServiceManager",
]
