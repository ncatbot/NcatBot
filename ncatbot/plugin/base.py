"""
插件基类

定义插件的元数据声明、生命周期接口和 Mixin 钩子编排。
每个 Mixin 可通过 ``_mixin_load`` / ``_mixin_unload`` 方法声明自己的 load/unload 行为，
BasePlugin 按 MRO 顺序自动发现并执行。
"""

import asyncio
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.api import BotAPIClient
    from ncatbot.core import AsyncEventDispatcher
    from .manifest import PluginManifest
    from ncatbot.service import ServiceManager
    from .loader.core import PluginLoader

LOG = get_log("BasePlugin")


class BasePlugin:
    """
    插件基类

    每个插件必须继承此类并定义 name / version 属性。
    框架在加载插件时会自动注入运行时属性并调用生命周期钩子。

    Mixin 钩子协议:
        - ``_mixin_load(self)``:  __onload__ 时按 MRO 顺序调用（支持 sync/async）
        - ``_mixin_unload(self)``: __unload__ 时按 MRO 顺序调用（支持 sync/async）

    NcatBotPlugin 的继承顺序决定钩子执行顺序。
    """

    # -------- 插件元数据（子类必须定义） --------
    name: str
    version: str
    author: str = "Unknown"
    description: str = ""
    dependencies: Dict[str, str] = {}

    # -------- 运行时属性（框架注入） --------
    workspace: Path
    services: "ServiceManager"
    api: "BotAPIClient"
    _dispatcher: "AsyncEventDispatcher"
    _plugin_loader: "PluginLoader"
    _manifest: Optional["PluginManifest"] = None
    _debug: bool = False

    # ------------------------------------------------------------------
    # 生命周期钩子（子类可重写）
    # ------------------------------------------------------------------

    def _init_(self) -> None:
        """同步初始化钩子（在 on_load 之前调用）"""

    async def on_load(self) -> None:
        """异步初始化钩子（主要初始化逻辑）"""

    async def on_close(self) -> None:
        """异步清理钩子"""

    def _close_(self) -> None:
        """同步清理钩子"""

    # ------------------------------------------------------------------
    # 框架专用方法（由 PluginLoader 调用）
    # ------------------------------------------------------------------

    async def __onload__(self) -> None:
        """框架加载插件时调用（子类不应重写）。

        流程: 创建 workspace → Mixin _mixin_load 链 → _init_() → on_load()
        """
        self.workspace.mkdir(exist_ok=True, parents=True)
        await self._run_mixin_hooks("_mixin_load")
        self._init_()
        await self.on_load()

    async def __startup__(self) -> None:
        """执行被 @registrar.on_startup() 标记的异步实例方法。"""
        for name, func in inspect.getmembers(type(self), inspect.iscoroutinefunction):
            if not getattr(func, "__plugin_startup__", False):
                continue
            try:
                await getattr(self, name)()
            except Exception:
                LOG.exception("插件 %s 启动回调 %s 执行失败", self.name, name)

    async def __unload__(self) -> None:
        """框架卸载插件时调用（子类不应重写）。

        流程: _close_() → on_close() → Mixin _mixin_unload 链
        """
        try:
            self._close_()
            await self.on_close()
        except Exception as e:
            LOG.exception("插件 %s 生命周期清理异常: %s", self.name, e)

        await self._run_mixin_hooks("_mixin_unload")

    # ------------------------------------------------------------------
    # Mixin 钩子编排
    # ------------------------------------------------------------------

    async def _run_mixin_hooks(self, hook_name: str) -> None:
        """按 MRO 顺序收集并执行 Mixin 钩子。

        每个钩子独立 try/except，确保单个失败不影响其余钩子。
        支持 sync 和 async 钩子。
        """
        for cls in type(self).__mro__:
            hook = cls.__dict__.get(hook_name)
            if hook is None:
                continue
            try:
                result = hook(self)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                LOG.exception(
                    "Mixin 钩子 %s.%s 执行异常: %s", cls.__name__, hook_name, e
                )

    # ------------------------------------------------------------------
    # 属性访问器
    # ------------------------------------------------------------------

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def logger(self):
        """返回以插件名为标签的 logger。"""
        return get_log(self.name)

    @property
    def meta_data(self) -> Dict[str, Any]:
        if self._manifest is not None:
            return self._manifest.as_dict()
        return {
            "name": getattr(self, "name", "Unknown"),
            "version": getattr(self, "version", "0.0.0"),
            "author": getattr(self, "author", "Unknown"),
            "description": getattr(self, "description", ""),
            "dependencies": getattr(self, "dependencies", {}),
        }

    # ------------------------------------------------------------------
    # 插件访问接口
    # ------------------------------------------------------------------

    def list_plugins(self) -> List[str]:
        """获取所有已加载插件的名称列表。"""
        return self._plugin_loader.list_plugins()

    def get_plugin(self, name: str) -> Optional["BasePlugin"]:
        """根据名称获取已加载的插件实例。"""
        return self._plugin_loader.get_plugin(name)
