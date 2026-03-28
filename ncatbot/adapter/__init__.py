from .base import BaseAdapter
from .mock import (
    MockAdapter,
    MockBotAPI,
    MockBiliAPI,
    MockGitHubAPI,
    MockAPIBase,
    APICall,
)
from .napcat import NapCatAdapter
from .bilibili import BilibiliAdapter
from .github import GitHubAdapter
from .ai import AIAdapter
from .lark import LarkAdapter
from .registry import AdapterRegistry, adapter_registry

# 注册内置适配器
adapter_registry.register("napcat", NapCatAdapter)
adapter_registry.register("mock", MockAdapter)
adapter_registry.register("bilibili", BilibiliAdapter)
adapter_registry.register("github", GitHubAdapter)
adapter_registry.register("ai", AIAdapter)
adapter_registry.register("lark", LarkAdapter)

__all__ = [
    "BaseAdapter",
    "MockAdapter",
    "MockBotAPI",
    "MockBiliAPI",
    "MockGitHubAPI",
    "MockAPIBase",
    "APICall",
    "NapCatAdapter",
    "BilibiliAdapter",
    "GitHubAdapter",
    "AIAdapter",
    "LarkAdapter",
    "AdapterRegistry",
    "adapter_registry",
]
