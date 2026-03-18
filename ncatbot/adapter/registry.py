"""适配器注册表 — 内置注册 + entry_point 第三方发现 + 工厂方法。"""

from __future__ import annotations

import importlib.metadata
from typing import Dict, Type, TYPE_CHECKING

from ncatbot.utils.logger import get_early_logger

if TYPE_CHECKING:
    from .base import BaseAdapter
    from ncatbot.utils.config.models import AdapterEntry

_log = get_early_logger("adapter.registry")

ENTRY_POINT_GROUP = "ncatbot.adapters"


class AdapterRegistry:
    """适配器注册表。

    - ``register(name, cls)`` 注册内置适配器
    - ``discover()`` 合并内置 + ``entry_point`` 第三方适配器
    - ``create(entry, **global_kwargs)`` 工厂方法
    """

    def __init__(self) -> None:
        self._builtin: Dict[str, Type[BaseAdapter]] = {}

    def register(self, name: str, cls: Type[BaseAdapter]) -> None:
        """注册内置适配器。"""
        self._builtin[name] = cls

    def discover(self) -> Dict[str, Type[BaseAdapter]]:
        """合并内置 + entry_point 发现，返回 {name: cls}。"""
        result = dict(self._builtin)

        try:
            eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
        except TypeError:
            # Python 3.9 兼容：entry_points() 返回 dict
            all_eps = importlib.metadata.entry_points()
            eps = all_eps.get(ENTRY_POINT_GROUP, [])  # type: ignore[union-attr]

        for ep in eps:
            if ep.name in result:
                _log.warning("第三方适配器 '%s' 与内置适配器同名，跳过", ep.name)
                continue
            try:
                cls = ep.load()
                result[ep.name] = cls
                _log.info("发现第三方适配器: %s (%s)", ep.name, ep.value)
            except Exception as e:
                _log.warning("加载第三方适配器 '%s' 失败: %s", ep.name, e)

        return result

    def list_available(self) -> list[str]:
        """列出所有可用的适配器类型名。"""
        return list(self.discover().keys())

    def create(
        self,
        entry: AdapterEntry,
        *,
        bot_uin: str = "",
        websocket_timeout: int = 15,
    ) -> BaseAdapter:
        """根据 AdapterEntry 创建适配器实例。

        Parameters
        ----------
        entry:
            配置文件中的适配器声明。
        bot_uin:
            全局 bot_uin，透传给适配器。
        websocket_timeout:
            全局超时设置，透传给适配器。
        """
        all_adapters = self.discover()
        if entry.type not in all_adapters:
            available = ", ".join(sorted(all_adapters.keys())) or "(无)"
            raise ValueError(f"未知的适配器类型 '{entry.type}'。可用: {available}")

        cls = all_adapters[entry.type]
        adapter = cls(
            config=entry.config,
            bot_uin=bot_uin,
            websocket_timeout=websocket_timeout,
        )

        # 如果 entry 指定了 platform，覆盖适配器默认值
        if entry.platform:
            adapter.platform = entry.platform

        return adapter


# 模块级单例
adapter_registry = AdapterRegistry()
