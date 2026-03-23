"""
插件加载器

组合 Indexer + Resolver + Importer，管理插件的完整生命周期。
通过 asyncio.create_task 订阅 FileWatcher 回调实现热重载。
"""

import asyncio
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type, TYPE_CHECKING

from ncatbot.utils import get_log

from ..base import BasePlugin
from ..manifest import PluginManifest
from .indexer import PluginIndexer
from .resolver import DependencyResolver
from .importer import ModuleImporter
from .pip_helper import check_requirements, install_packages, format_missing_report

if TYPE_CHECKING:
    from ncatbot.core import HandlerDispatcher

LOG = get_log("PluginLoader")


class PluginLoader:
    """插件加载器

    典型用法::

        loader = PluginLoader()
        await loader.load_all(Path("plugins"))

        # 热重载由 setup_hot_reload 自动配置
    """

    def __init__(self) -> None:
        self._indexer = PluginIndexer()
        self._resolver = DependencyResolver()
        self._importer = ModuleImporter()
        self.plugins: Dict[str, BasePlugin] = {}

        # 热重载相关
        self._reload_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reload_task: Optional[asyncio.Task] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # 插件实例化时的注入回调（由外部设置）
        self._on_plugin_init: Optional[Callable[[BasePlugin, PluginManifest], None]] = (
            None
        )

        # Handler 分发器（由 BotClient 注入）
        self._handler_dispatcher: Optional["HandlerDispatcher"] = None

    # ------------------------------------------------------------------
    # 批量加载
    # ------------------------------------------------------------------

    async def load_all(self, plugins_dir: Path) -> List[str]:
        """扫描目录并按依赖顺序加载所有插件。

        Returns:
            成功加载的插件名列表
        """
        # 将插件根目录加入 sys.path（使跨插件导入可用）
        self._importer.add_plugin_root(plugins_dir)

        manifests = self._indexer.scan(plugins_dir)
        if not manifests:
            LOG.info("未在 %s 中发现插件", plugins_dir)
            return []

        # 依赖解析
        load_order = self._resolver.resolve(manifests)
        self._resolver.validate_versions(manifests)

        # pip 依赖检查
        skip_plugins = await self._check_pip_deps_batch(manifests)

        # 按序加载
        loaded = []
        for name in load_order:
            if name in skip_plugins:
                LOG.warning("跳过插件 %s（pip 依赖未满足）", name)
                continue
            plugin = await self.load_plugin(name)
            if plugin is not None:
                loaded.append(name)

        LOG.info("已加载 %d/%d 个插件", len(loaded), len(manifests))
        return loaded

    async def load_selected(
        self,
        plugins_dir: Path,
        names: List[str],
        *,
        skip_pip: bool = True,
    ) -> List[str]:
        """只加载指定插件及其传递依赖。

        Args:
            plugins_dir: 插件根目录
            names: 需要加载的目标插件名列表
            skip_pip: 是否跳过 pip 依赖检查（测试环境默认跳过）

        Returns:
            成功加载的插件名列表
        """
        self._importer.add_plugin_root(plugins_dir)

        manifests = self._indexer.scan(plugins_dir)
        if not manifests:
            LOG.info("未在 %s 中发现插件", plugins_dir)
            return []

        # 解析目标插件及其传递依赖的加载顺序
        load_order = self._resolver.resolve_subset(manifests, names)
        # 只对子集做版本验证
        subset = {n: manifests[n] for n in load_order}
        self._resolver.validate_versions(subset)

        # pip 依赖检查
        skip_plugins: set = set()
        if not skip_pip:
            skip_plugins = await self._check_pip_deps_batch(subset)

        loaded = []
        for name in load_order:
            if name in skip_plugins:
                LOG.warning("跳过插件 %s（pip 依赖未满足）", name)
                continue
            plugin = await self.load_plugin(name)
            if plugin is not None:
                loaded.append(name)

        LOG.info("已选择性加载 %d/%d 个插件", len(loaded), len(load_order))
        return loaded

    # ------------------------------------------------------------------
    # 单个插件操作
    # ------------------------------------------------------------------

    def set_handler_dispatcher(self, dispatcher: "HandlerDispatcher") -> None:
        """注入 HandlerDispatcher 实例（由 BotClient 调用）。"""
        self._handler_dispatcher = dispatcher

    async def load_plugin(self, name: str) -> Optional[BasePlugin]:
        """加载单个插件（必须已索引）。"""
        from ncatbot.core import (
            set_current_plugin,
        )
        from ncatbot.core.registry.context import (
            _current_plugin_ctx,
        )
        from ncatbot.core import flush_pending, clear_pending

        manifest = self._indexer.get(name)
        if manifest is None:
            LOG.error("插件 %s 未索引，无法加载", name)
            return None

        # 单插件加载时也检查 pip 依赖
        if manifest.pip_dependencies:
            if not await self._ensure_pip_deps(manifest):
                return None

        try:
            # ContextVar 包裹模块加载，确保装饰器能读取到当前插件名
            token = set_current_plugin(name)
            try:
                module = self._importer.load_module(manifest)
            finally:
                _current_plugin_ctx.reset(token)

            plugin_class = self._importer.find_plugin_class(
                module, manifest.entry_class
            )
            plugin = self._instantiate(plugin_class, manifest)

            # 框架加载
            await plugin.__onload__()

            # 将装饰器收集的 handler 注册到 HandlerDispatcher
            if self._handler_dispatcher is not None:
                flush_pending(self._handler_dispatcher, name, plugin_instance=plugin)

            self.plugins[name] = plugin
            LOG.info("插件加载成功: %s v%s", name, manifest.version)
            return plugin

        except Exception as e:
            # 加载失败时清理残留的 pending handlers
            clear_pending(name)
            LOG.error("加载插件 %s 失败: %s", name, e)
            return None

    async def unload_plugin(self, name: str) -> bool:
        """卸载单个插件。"""
        from ncatbot.core import clear_pending

        plugin = self.plugins.get(name)
        if plugin is None:
            LOG.warning("插件 %s 未加载", name)
            return False

        manifest = self._indexer.get(name)
        try:
            await plugin.__unload__()
        except Exception as e:
            LOG.error("插件 %s __unload__ 异常: %s", name, e)

        # 从 HandlerDispatcher 移除该插件的所有 handler
        if self._handler_dispatcher is not None:
            self._handler_dispatcher.revoke_plugin(name)

        # 清理可能残留的 pending handlers
        clear_pending(name)

        if manifest is not None:
            self._importer.unload_module(manifest)

        del self.plugins[name]
        LOG.info("插件已卸载: %s", name)
        return True

    async def reload_plugin(self, name: str) -> bool:
        """重载单个插件（卸载 → 重索引 → 加载）。"""
        manifest = self._indexer.get(name)
        if manifest is None:
            LOG.error("无法重载未索引的插件: %s", name)
            return False

        await self.unload_plugin(name)
        await asyncio.sleep(0.02)  # 等待清理完成

        # 重新读取 manifest（支持清单变更）
        new_manifest = self._indexer.rescan_plugin(name)
        if new_manifest is None:
            LOG.error("重载插件 %s 时重索引失败", name)
            return False

        result = await self.load_plugin(name)
        if result is not None:
            LOG.info("插件 %s 重载成功", name)
            return True
        return False

    async def unload_all(self) -> None:
        """卸载所有插件。"""
        await asyncio.gather(*(self.unload_plugin(name) for name in list(self.plugins)))

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    def get_plugin_name_by_folder(self, folder_name: str) -> Optional[str]:
        """根据文件夹名查找插件名。"""
        manifest = self._indexer.get_by_folder(folder_name)
        return manifest.name if manifest else None

    # ------------------------------------------------------------------
    # 热重载
    # ------------------------------------------------------------------

    def setup_hot_reload(
        self, file_watcher, *, loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        """配置热重载。

        将 FileWatcherService 的回调连接到重载队列，并启动异步消费任务。

        Args:
            file_watcher: FileWatcherService 实例
            loop: 事件循环（默认使用当前 running loop）
        """
        self._event_loop = loop or asyncio.get_running_loop()

        def _on_change(plugin_folder: str):
            """FileWatcher 回调（在 watcher 线程中执行）"""
            assert self._event_loop is not None
            self._event_loop.call_soon_threadsafe(
                self._reload_queue.put_nowait, plugin_folder
            )

        file_watcher.on_file_changed = _on_change
        self._reload_task = asyncio.ensure_future(
            self._reload_consumer(), loop=self._event_loop
        )
        LOG.info("热重载已启动")

    async def stop_hot_reload(self) -> None:
        """停止热重载消费任务。"""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass
            self._reload_task = None
            LOG.info("热重载已停止")

    async def _reload_consumer(self) -> None:
        """异步任务：从队列中消费文件变更事件并执行重载。"""
        while True:
            folder_name = await self._reload_queue.get()
            plugin_name = self.get_plugin_name_by_folder(folder_name)
            if plugin_name is None:
                LOG.debug("未知插件目录: %s，跳过重载", folder_name)
                continue

            if plugin_name not in self.plugins:
                LOG.debug("插件 %s 未加载，跳过重载", plugin_name)
                continue

            LOG.info("热重载触发: %s (文件夹: %s)", plugin_name, folder_name)
            try:
                await self.reload_plugin(plugin_name)
            except Exception as e:
                LOG.error("热重载失败 [%s]: %s", plugin_name, e)

    # ------------------------------------------------------------------
    # 内置插件
    # ------------------------------------------------------------------

    async def load_builtin_plugins(self) -> None:
        """加载内置插件。"""
        from ...plugin.builtin import BUILTIN_PLUGINS

        last_loaded: Optional[BasePlugin] = None

        for plugin_class in BUILTIN_PLUGINS:
            name = plugin_class.name
            if name in self.plugins:
                LOG.warning("内置插件 %s 已加载，跳过", name)
                continue

            manifest = PluginManifest(
                name=name,
                version=plugin_class.version,
                main="__builtin__",
                author=getattr(plugin_class, "author", "NcatBot"),
                description=getattr(plugin_class, "description", ""),
                plugins_dir=Path("data") / name,
                folder_name=name,
            )

            try:
                plugin = self._instantiate(plugin_class, manifest)
                await plugin.__onload__()
                self.plugins[name] = plugin
                last_loaded = plugin
                LOG.info("内置插件加载成功: %s v%s", name, manifest.version)
            except Exception as e:
                LOG.error("加载内置插件 %s 失败: %s", name, e)

        # 内置模块在首次 flush_pending(__global__) 之后才导入，@registrar 收集在 __global__。
        # 移到真实插件名以便 unload_plugin 时 revoke_plugin 能移除；并注入实例以绑定 self。
        if self._handler_dispatcher is not None and last_loaded is not None:
            from ncatbot.core import flush_pending
            from ncatbot.core.registry.registrar import _pending_handlers

            pending = _pending_handlers.pop("__global__", [])
            if pending:
                _pending_handlers[last_loaded.name] = pending
            flush_pending(
                self._handler_dispatcher,
                last_loaded.name,
                plugin_instance=last_loaded,
            )

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _check_pip_deps_batch(self, manifests: Dict[str, PluginManifest]) -> set:
        """批量检查所有插件的 pip 依赖，返回应跳过的插件名集合。"""
        from ncatbot.utils import async_confirm
        from ncatbot.utils import get_config_manager

        config = get_config_manager()
        if not config.plugin.auto_install_pip_deps:
            # 配置禁用自动安装，仅输出警告
            skip = set()
            for name, manifest in manifests.items():
                if manifest.pip_dependencies:
                    _, missing = check_requirements(manifest.pip_dependencies)
                    if missing:
                        LOG.warning("%s", format_missing_report(name, missing))
                        skip.add(name)
            return skip

        # 合并所有插件的 pip 依赖（去重，同名取第一个出现的约束）
        all_deps: Dict[str, str] = {}
        dep_to_plugins: Dict[str, List[str]] = {}
        for name, manifest in manifests.items():
            for pkg, constraint in manifest.pip_dependencies.items():
                if pkg not in all_deps:
                    all_deps[pkg] = constraint
                dep_to_plugins.setdefault(pkg, []).append(name)

        if not all_deps:
            return set()

        _, missing = check_requirements(all_deps)
        if not missing:
            return set()

        # 构建报告
        report_lines = ["以下插件需要额外安装 pip 依赖:"]
        for req in missing:
            pkg_name = (
                req.split(">")[0]
                .split("<")[0]
                .split("=")[0]
                .split("!")[0]
                .split("~")[0]
                .strip()
            )
            plugins = dep_to_plugins.get(pkg_name, ["?"])
            report_lines.append(f"  - {req} (被 {', '.join(plugins)} 使用)")
        report = "\n".join(report_lines)
        LOG.info("%s", report)

        # 询问用户
        if config.effective_skip_pip_install_confirm():
            approved = True
        else:
            approved = await async_confirm(
                f"是否安装以上 {len(missing)} 个依赖?", default=True
            )
        if not approved:
            # 找出哪些插件受影响
            missing_names = {
                req.split(">")[0]
                .split("<")[0]
                .split("=")[0]
                .split("!")[0]
                .split("~")[0]
                .strip()
                for req in missing
            }
            skip = set()
            for name, manifest in manifests.items():
                if missing_names & set(manifest.pip_dependencies.keys()):
                    skip.add(name)
            LOG.info("用户拒绝安装，跳过插件: %s", skip)
            return skip

        # 执行安装
        if install_packages(missing):
            return set()

        # 安装失败，重新检查哪些还缺
        _, still_missing = check_requirements(all_deps)
        if not still_missing:
            return set()

        still_missing_names = {
            req.split(">")[0]
            .split("<")[0]
            .split("=")[0]
            .split("!")[0]
            .split("~")[0]
            .strip()
            for req in still_missing
        }
        skip = set()
        for name, manifest in manifests.items():
            if still_missing_names & set(manifest.pip_dependencies.keys()):
                skip.add(name)
        LOG.warning("部分依赖安装失败，跳过插件: %s", skip)
        return skip

    async def _ensure_pip_deps(self, manifest: PluginManifest) -> bool:
        """检查并安装单个插件的 pip 依赖。返回 True 表示满足/已安装。"""
        from ncatbot.utils import async_confirm
        from ncatbot.utils import get_config_manager

        _, missing = check_requirements(manifest.pip_dependencies)
        if not missing:
            return True

        LOG.info("%s", format_missing_report(manifest.name, missing))

        config = get_config_manager()
        if not config.plugin.auto_install_pip_deps:
            LOG.warning("auto_install_pip_deps 已禁用，跳过插件 %s", manifest.name)
            return False

        if config.effective_skip_pip_install_confirm():
            approved = True
        else:
            approved = await async_confirm(
                f"插件 {manifest.name} 需要安装 {len(missing)} 个 pip 依赖，是否安装?",
                default=True,
            )
        if not approved:
            LOG.info("用户拒绝安装，跳过插件 %s", manifest.name)
            return False

        if not install_packages(missing):
            LOG.error("依赖安装失败，跳过插件 %s", manifest.name)
            return False

        return True

    def _instantiate(
        self, plugin_class: Type[BasePlugin], manifest: PluginManifest
    ) -> BasePlugin:
        """实例化插件并注入运行时属性。"""
        plugin = plugin_class()

        # 注入插件元数据（manifest 优先于类属性）
        plugin.name = manifest.name
        plugin.version = manifest.version
        if manifest.author:
            plugin.author = manifest.author
        if manifest.description:
            plugin.description = manifest.description

        # 注入框架属性
        plugin._manifest = manifest
        from ncatbot.utils import get_config_manager

        plugin._debug = get_config_manager().effective_debug
        plugin.workspace = Path("data") / manifest.name
        plugin.config = {}
        plugin.data = {}

        # 外部注入回调
        if self._on_plugin_init:
            self._on_plugin_init(plugin, manifest)

        return plugin
