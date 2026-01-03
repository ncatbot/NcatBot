import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Type, Union

from ncatbot.utils import get_log

from ..base_plugin import BasePlugin
from ncatbot.core import EventBus
from ncatbot.core.service import ServiceManager
from ..pluginsys_err import (
    PluginDependencyError,
    PluginVersionError,
)
from ..builtin_plugin import SystemManager
from packaging.specifiers import SpecifierSet
from packaging.version import parse as parse_version

from .importer import _ModuleImporter
from .resolver import _DependencyResolver
from .hooks import interactive_migrate_plugins

LOG = get_log("PluginLoader")


class PluginLoader:
    """插件加载器：负责插件的加载、卸载、重载、生命周期管理。"""

    def __init__(
        self,
        event_bus: EventBus,
        service_manager: ServiceManager,
        *,
        debug: bool = False,
    ) -> None:
        self.plugins: Dict[str, BasePlugin] = {}
        self.event_bus = event_bus or EventBus()
        self._debug = debug
        self._importer = _ModuleImporter()
        self._resolver = _DependencyResolver()

        # 服务管理器由外部注入
        self._service_manager = service_manager

        if debug:
            LOG.warning("插件系统已切换为调试模式")

    # -------------------- 对外 API --------------------
    def get_plugin_name_by_folder_name(self, folder_name: str) -> Optional[str]:
        return self._importer.get_plugin_name_by_folder(folder_name)

    async def _load_plugin_by_class(
        self, plugin_class: Type[BasePlugin], name: str, **kwargs
    ) -> BasePlugin:
        """
        Instantiate plugin_class and initialize it. kwargs may contain manifest-derived
        metadata and other extras; they will be forwarded to the plugin constructor.

        注入 service_manager，插件通过它获取各种服务。
        """
        plugin = plugin_class(
            event_bus=self.event_bus,
            debug=self._debug,
            plugin_loader=self,
            name=name,
            service_manager=self._service_manager,
            **kwargs,
        )
        # Ensure name is set (may be provided via manifest)

        self.plugins[name] = plugin
        await plugin.__onload__()
        return plugin

    async def load_builtin_plugins(self) -> None:
        """加载内置插件。"""
        plugins = {
            "system_manager": SystemManager,
        }
        for name, plg in plugins.items():
            await self._load_plugin_by_class(plg, name)
        LOG.info("已加载内置插件数 [%d]", len(self.plugins))

    async def load_external_plugins(self, path: Path, **kwargs) -> None:
        """从目录批量加载。"""
        if not path.exists():
            LOG.info("插件目录: %s 不存在……跳过加载插件", path)
            return

        self._service_manager.file_watcher.add_watch_dir(str(path))
        await self._pre_first_load(path)
        LOG.info("从 %s 导入插件", path)

        plugin_manifests = self._importer.get_plugin_manifests(path)
        self._resolver.build(plugin_manifests)

        load_order = self._resolver.resolve()

        for name in load_order:
            manifest = plugin_manifests[name]
            LOG.info("加载插件「%s」", name)
            # Collect extras from manifest
            extras = {"_meta_data": manifest}
            # Avoid passing 'name' as a kwarg because 'name' is provided positionally
            extras.update(
                {
                    k: v
                    for k, v in manifest.items()
                    if k in ("version", "author", "description", "dependencies")
                }
            )
            await self.load_plugin(name, **extras)

        self._validate_versions()
        # 并发执行所有插件的初始化
        LOG.info("已加载插件数 [%d]", len(plugin_manifests))

    # -------------------- 单个插件的加载方法 ---------------------
    async def load_plugin(self, name: str, **kwargs) -> Optional[BasePlugin]:
        try:
            self._service_manager.unified_registry.set_current_plugin_name(name)
            module = self._importer.load_plugin_module(name)
            if module is None:
                LOG.error("尝试加载失败的插件 %s: 模块未返回", name)
                return None
            plugin_class = self._find_plugin_class_in_module(module)
            if plugin_class is None:
                LOG.error("尝试加载失败的插件 %s: 未在模块中找到插件类", name)
                return None
            return await self._load_plugin_by_class(plugin_class, name, **kwargs)
        except Exception as e:
            LOG.error("尝试加载失败的插件 %s: %s", name, e)
            return None

    def index_external_plugin(self, plugin_dir: str) -> Optional[str]:
        """索引一个外部插件文件夹

        读取插件的元数据并写入索引，之后可以使用 load_plugin 加载。

        Args:
            plugin_dir: 插件文件夹的路径

        Returns:
            插件名称，如果索引失败则返回 None
        """
        from pathlib import Path

        return self._importer.index_external_plugin(Path(plugin_dir))

    async def unload_plugin(self, name: str, **kwargs) -> bool:
        """卸载单个插件。"""
        plugin = self.plugins.get(name)
        if not plugin:
            LOG.warning("插件 '%s' 未加载，无法卸载", name)
            return False
        try:
            await plugin.__unload__(**kwargs)
            self._importer.unload_plugin_module(name)
            del self.plugins[name]
            return True
        except Exception as e:
            LOG.error("卸载插件 '%s' 时发生错误: %s", name, e)
            return False

    async def reload_plugin(self, name: str, **kwargs) -> bool:
        """重载单个插件。"""
        try:
            await self.unload_plugin(name, **kwargs)
            await self.load_plugin(name)
            LOG.info("插件 '%s' 重载成功", name)
            return True
        except Exception as e:
            LOG.error("重载插件 '%s' 失败: %s", name, e)
            return False

    async def unload_all(self, **kwargs) -> None:
        """一键异步卸载全部插件。"""
        # RBAC 服务会在 on_close 时自动保存数据
        await asyncio.gather(
            *(self.unload_plugin(name, **kwargs) for name in list(self.plugins))
        )
        # 服务关闭由外部 ServiceManager 统一管理

    # -------------------- 查询 API --------------------
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.plugins.get(name, None)

    def get_metadata(self, name: str) -> dict:
        return self.plugins[name].meta_data

    def list_plugins(self, *, obj: bool = False) -> List[Union[str, BasePlugin]]:
        return list(self.plugins.values()) if obj else list(self.plugins.keys())

    # -------------------- 私有辅助 --------------------
    @staticmethod
    def _is_valid(item: object) -> bool:
        """Return True if `item` is a tuple whose first element is a subclass of BasePlugin.

        Expected form: (Type[BasePlugin], manifest_dict)
        """
        if not isinstance(item, tuple):
            return False
        try:
            target = item[0]
            return isinstance(target, type) and issubclass(target, BasePlugin)
        except Exception:
            return False

    def _validate_versions(self) -> None:
        """检查已加载插件的版本约束。"""
        for plugin_name, constraints in self._resolver._constraints.items():
            for dep_name, constraint in constraints.items():
                dep = self.plugins.get(dep_name)
                if not dep:
                    raise PluginDependencyError(plugin_name, dep_name, constraint)
                if not SpecifierSet(constraint).contains(parse_version(dep.version)):
                    raise PluginVersionError(
                        plugin_name, dep_name, constraint, dep.version
                    )

    def _find_plugin_class_in_module(
        self, module: ModuleType
    ) -> Optional[Type[BasePlugin]]:
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
                and obj.__module__ == module.__name__
            ):
                return obj
        return None

    # ------------------- Hook ------------------------
    async def _pre_first_load(self, plugin_root: Path):
        # 第一次扫描插件目录前
        interactive_migrate_plugins(plugin_root)
        self._importer.index_all_plugins(plugin_root)

    async def _after_first_load(self):
        # 完成第一次加载操作后
        pass
