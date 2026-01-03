# -------------------------
# @Author       : Fish-LP fish.zh@outlook.com
# @Date         : 2025-02-15 20:08:02
# @LastEditors  : Fish-LP fish.zh@outlook.com
# @LastEditTime : 2025-08-08 11:30:52
# @Description  : 插件系统基础类（纯声明）
# @Copyright (c) 2025 by Fish-LP, Fcatbot使用许可协议
# -------------------------
from uuid import UUID
from pathlib import Path
from typing import Any, Dict, List, Set, Union, TYPE_CHECKING, Optional, Callable

from ncatbot.utils import get_log
from ncatbot.core import EventBus, NcatBotEvent
from ncatbot.core.service import ServiceManager

if TYPE_CHECKING:
    from .builtin_mixin.ncatbot_plugin import NcatBotPlugin
    from .loader import PluginLoader
    from ncatbot.core.service.builtin import (
        RBACService,
        PluginConfigService,
        PluginConfig,
    )

LOG = get_log("BasePlugin")


class BasePlugin:
    """
    插件系统基础类（纯声明）

    此类仅声明插件的属性和生命周期方法接口。
    实际初始化逻辑在 NcatBotPlugin 中实现。
    """

    # -------- 插件元数据 --------
    name: str
    version: str
    author: str = "Unknown"
    description: str = "这个作者很懒且神秘，没有写一点点描述，真是一个神秘的插件"
    dependencies: Dict[str, str] = {}
    config: "PluginConfig"

    # -------- 运行时属性 --------
    first_load: bool = True
    main_file: Path
    source_dir: Path
    workspace: Path
    services: ServiceManager

    # -------- 内部属性 --------
    _debug: bool
    _event_bus: EventBus
    _handlers_id: Set[UUID]
    _loader: "PluginLoader"
    _legacy_data_file: Path

    # ------------------------------------------------------------------
    # 生命周期方法（子类重写）
    # ------------------------------------------------------------------
    async def on_load(self) -> None:
        """插件加载时异步初始化钩子。"""

    async def on_reload(self) -> None:
        """插件重新加载时异步处理钩子。"""

    async def on_close(self, *args: Any, **kw: Any) -> None:
        """插件卸载时异步清理钩子。"""

    def _init_(self) -> None:
        """插件加载时同步初始化钩子。"""

    def _reinit_(self) -> None:
        """插件重新加载时同步处理钩子。"""

    def _close_(self, *args: Any, **kw: Any) -> None:
        """插件卸载时同步清理钩子。"""

    # ------------------------------------------------------------------
    # 框架专用方法（由 NcatBotPlugin 实现）
    # ------------------------------------------------------------------
    async def __onload__(self) -> None:
        """由框架在加载插件时调用。"""

    async def __unload__(self, *a: Any, **kw: Any) -> None:
        """由框架在卸载插件时调用。"""

    # ------------------------------------------------------------------
    # 属性访问器
    # ------------------------------------------------------------------
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def meta_data(self) -> Dict[str, Any]:
        if hasattr(self, "_meta_data") and isinstance(self._meta_data, dict):  # type: ignore
            md = dict(self._meta_data)  # type: ignore
            md.setdefault("name", getattr(self, "name", "Unknown"))
            md.setdefault("version", getattr(self, "version", "0.0.0"))
            md.setdefault("author", getattr(self, "author", "Unknown"))
            md.setdefault("description", getattr(self, "description", ""))
            md.setdefault("dependencies", getattr(self, "dependencies", {}))
            md.setdefault("config", getattr(self, "config", {}))
            return md
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "config": self.config,
        }.copy()

    @property
    def rbac(self) -> "RBACService":
        return self.services.rbac  # type: ignore

    @property
    def config_service(self) -> "PluginConfigService":
        return self.services.plugin_config

    # ------------------------------------------------------------------
    # 事件系统接口
    # ------------------------------------------------------------------
    def register_handler(
        self,
        event_type: str,
        handler: Callable,
        priority: int = 0,
        timeout: Optional[float] = None,
    ) -> UUID:
        """注册事件处理器。"""
        if event_type in ["group_message", "private_message"]:
            LOG.warning(
                f"使用了 deprecated 事件类型: {event_type}, 请使用 ncatbot.message_event 代替"
            )
        handler_id = self._event_bus.subscribe(
            event_type, handler, priority, timeout, plugin=self
        )
        self._handlers_id.add(handler_id)
        return handler_id

    def unregister_handler(self, handler_id: UUID) -> bool:
        """注销事件处理器。"""
        if handler_id in self._handlers_id:
            self._handlers_id.remove(handler_id)
            return self._event_bus.unsubscribe(handler_id)
        return False

    def unregister_all_handler(self) -> None:
        """注销本插件所有事件处理器。"""
        for handler_id in tuple(self._handlers_id):
            self.unregister_handler(handler_id)

    async def publish(self, event_type: str, data: Any) -> List[Any]:
        """发布事件。"""
        return await self._event_bus.publish(NcatBotEvent(event_type, data))

    def get_plugin(self, name: str) -> Optional["NcatBotPlugin"]:
        """根据插件名称获取插件实例。"""
        return self._loader.get_plugin(name)  # type: ignore

    def list_plugins(self, *, obj: bool = False) -> List[Union[str, "BasePlugin"]]:
        """插件列表。"""
        return self._loader.list_plugins(obj=obj)
