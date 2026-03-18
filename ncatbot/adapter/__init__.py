from .base import BaseAdapter
from .mock import MockAdapter, MockBotAPI, APICall
from .napcat import NapCatAdapter
from .bilibili import BilibiliAdapter
from .registry import AdapterRegistry, adapter_registry

# 注册内置适配器
adapter_registry.register("napcat", NapCatAdapter)
adapter_registry.register("mock", MockAdapter)
adapter_registry.register("bilibili", BilibiliAdapter)

__all__ = [
    "BaseAdapter",
    "MockAdapter",
    "MockBotAPI",
    "APICall",
    "NapCatAdapter",
    "BilibiliAdapter",
    "AdapterRegistry",
    "adapter_registry",
]
