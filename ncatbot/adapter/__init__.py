"""
平台适配层 (Layer 1)

提供与外部平台交互的适配器抽象和具体实现。
"""

from .base import BaseAdapter
from .napcat import NapCatAdapter

__all__ = ["BaseAdapter", "NapCatAdapter"]
