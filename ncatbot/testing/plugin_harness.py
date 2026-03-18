"""
PluginTestHarness — 离线插件测试编排器

在 TestHarness 基础上增加插件选择性加载、插件状态查询等能力。
支持只加载指定插件及其传递依赖，无需连接 NapCat。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from ncatbot.adapter import MockAdapter
from ncatbot.app import BotClient

from .harness import TestHarness

if TYPE_CHECKING:
    from ncatbot.plugin import BasePlugin


class PluginTestHarness(TestHarness):
    """插件测试编排器 — 选择性加载指定插件并提供完整测试能力。

    用法::

        async with PluginTestHarness(
            plugin_names=["hello_world"],
            plugin_dir=Path("examples/01_hello_world"),
        ) as harness:
            await harness.inject(group_message("hello"))
            await harness.settle()
            assert harness.api_called("post_group_msg")
    """

    __test__ = False

    def __init__(
        self,
        plugin_names: List[str],
        plugin_dir: Path,
        *,
        skip_builtin: bool = True,
        skip_pip: bool = True,
    ) -> None:
        # 不调用 super().__init__()，自行构建 bot
        self._adapter = MockAdapter(platform="qq")
        self._bot = BotClient(adapter=self._adapter)
        self._plugin_names = plugin_names
        self._plugin_dir = Path(plugin_dir)
        self._skip_builtin = skip_builtin
        self._skip_pip = skip_pip

    async def start(self) -> None:
        """启动核心基础设施 + 选择性加载插件"""
        # 只启动 adapter/api/dispatcher/services，不加载插件
        await self._bot._startup_core()

        # 配置 PluginLoader 的 HandlerDispatcher 和依赖注入
        loader = self._bot._plugin_loader
        loader.set_handler_dispatcher(self._bot.handler_dispatcher)

        def _inject_plugin_deps(plugin, manifest):
            plugin.services = self._bot._service_manager
            plugin.api = self._bot._api
            plugin._dispatcher = self._bot._dispatcher
            plugin._plugin_loader = loader

        loader._on_plugin_init = _inject_plugin_deps

        # 可选：加载内置插件
        if not self._skip_builtin:
            await loader.load_builtin_plugins()

        # 选择性加载目标插件及其传递依赖
        await loader.load_selected(
            self._plugin_dir,
            self._plugin_names,
            skip_pip=self._skip_pip,
        )

        # 启动后台监听
        self._bot._running = True
        self._bot._listen_task = asyncio.create_task(self._bot._listen_forever())

    # ---- 插件状态查询 ----

    @property
    def loaded_plugins(self) -> List[str]:
        """当前已加载的插件名列表"""
        return self._bot._plugin_loader.list_plugins()

    def get_plugin(self, name: str) -> Optional["BasePlugin"]:
        """获取已加载的插件实例"""
        return self._bot._plugin_loader.get_plugin(name)

    def plugin_config(self, name: str) -> dict:
        """获取插件的 config 字典"""
        plugin = self.get_plugin(name)
        if plugin is None:
            raise KeyError(f"插件 {name} 未加载")
        return dict(plugin.config)

    def plugin_data(self, name: str) -> dict:
        """获取插件的 data 字典"""
        plugin = self.get_plugin(name)
        if plugin is None:
            raise KeyError(f"插件 {name} 未加载")
        return dict(plugin.data)

    async def reload_plugin(self, name: str) -> bool:
        """热重载某个插件"""
        return await self._bot._plugin_loader.reload_plugin(name)
