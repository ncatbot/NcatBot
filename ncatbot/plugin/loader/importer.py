"""
模块导入器

负责插件模块的加载和卸载。
跨插件导入通过将插件根目录添加到 sys.path 实现，无需虚拟包或自定义 Finder。
"""

import importlib
import importlib.util
import sys
from types import ModuleType
from typing import Optional, Set, Type

from ncatbot.utils import get_log

from ..base import BasePlugin
from ..manifest import PluginManifest

LOG = get_log("ModuleImporter")


class ModuleImporter:
    """插件模块的加载与卸载。

    跨插件导入机制：

    - 将插件根目录 ``append`` 到 ``sys.path``（低于 stdlib / 第三方包优先级）。
    - 每个插件文件夹即为一个普通 Python 包。
    - 插件 A 可通过 ``from plugin_b_folder.module import xxx`` 导入插件 B 的代码。
    - 插件内部相对导入 ``from . import utils`` 正常工作。
    """

    def __init__(self) -> None:
        self._plugin_roots: Set[str] = set()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def add_plugin_root(self, root_dir: str | object) -> None:
        """将插件根目录添加到 sys.path（仅一次，append 避免遮蔽标准库）。"""
        from pathlib import Path

        root_str = str(Path(str(root_dir)).resolve())
        if root_str not in self._plugin_roots:
            self._plugin_roots.add(root_str)
            sys.path.append(root_str)
            LOG.debug("已添加插件根目录到 sys.path: %s", root_str)

    def load_module(self, manifest: PluginManifest) -> ModuleType:
        """加载插件入口模块并返回。

        Raises:
            ImportError: 无法加载模块
        """
        importlib.invalidate_caches()
        self._clear_pycache(manifest)

        pkg_name = manifest.folder_name
        module_name = f"{pkg_name}.{manifest.entry_stem}"
        plugin_path = str(manifest.plugins_dir)

        created_pkg = False
        created_module = False
        try:
            # 确保插件包存在于 sys.modules
            if pkg_name not in sys.modules:
                init_file = manifest.plugins_dir / "__init__.py"
                if init_file.exists():
                    pkg_spec = importlib.util.spec_from_file_location(
                        pkg_name,
                        str(init_file),
                        submodule_search_locations=[plugin_path],
                    )
                    if pkg_spec and pkg_spec.loader:
                        pkg = importlib.util.module_from_spec(pkg_spec)
                        pkg.__path__ = [plugin_path]
                        pkg.__package__ = pkg_name
                        sys.modules[pkg_name] = pkg
                        pkg_spec.loader.exec_module(pkg)
                    else:
                        raise ImportError(
                            f"无法为插件包 {pkg_name} 创建 spec: {init_file}"
                        )
                else:
                    # 隐式命名空间包
                    pkg = ModuleType(pkg_name)
                    pkg.__path__ = [plugin_path]
                    pkg.__package__ = pkg_name
                    sys.modules[pkg_name] = pkg
                created_pkg = True

            # 加载入口模块
            # __init__.py 中的 ``from .main import ...`` 可能已经触发了入口模块的
            # 导入并执行了装饰器。此时 sys.modules 中已有该模块，直接复用即可，
            # 避免重新 exec 导致装饰器注册出重复的 handler 函数对象。
            existing = sys.modules.get(module_name)
            if existing is not None:
                LOG.debug("入口模块 %s 已由包 __init__ 导入，复用现有模块", module_name)
                return existing

            entry_file = str(manifest.entry_file)
            spec = importlib.util.spec_from_file_location(module_name, entry_file)
            if spec is None or spec.loader is None:
                raise ImportError(
                    f"无法为插件 {manifest.name} 创建模块 spec: {entry_file}"
                )

            module = importlib.util.module_from_spec(spec)
            module.__spec__ = spec
            module.__package__ = pkg_name
            sys.modules[module_name] = module
            created_module = True

            spec.loader.exec_module(module)
            return module

        except Exception:
            if created_module:
                sys.modules.pop(module_name, None)
            if created_pkg:
                sys.modules.pop(pkg_name, None)
            raise

    def unload_module(self, manifest: PluginManifest) -> None:
        """从 sys.modules 中移除插件及其所有子模块。"""
        pkg_name = manifest.folder_name

        to_remove = [
            key
            for key in list(sys.modules)
            if key == pkg_name or key.startswith(f"{pkg_name}.")
        ]
        for key in to_remove:
            del sys.modules[key]

        importlib.invalidate_caches()
        if to_remove:
            LOG.info("已卸载模块 %s (共 %d 个)", manifest.name, len(to_remove))

    def find_plugin_class(
        self, module: ModuleType, class_name: Optional[str] = None
    ) -> Type[BasePlugin]:
        """在模块中查找 BasePlugin 子类。

        Args:
            module: 已加载的模块
            class_name: 指定类名（来自 manifest.entry_class），为 None 时自动发现

        Raises:
            ImportError: 未找到插件类
        """
        if class_name:
            obj = getattr(module, class_name, None)
            if (
                obj is None
                or not isinstance(obj, type)
                or not issubclass(obj, BasePlugin)
            ):
                raise ImportError(
                    f"模块 {module.__name__} 中未找到 BasePlugin 子类: {class_name}"
                )
            return obj

        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
                and obj.__module__ == module.__name__
            ):
                return obj

        raise ImportError(f"模块 {module.__name__} 中未找到 BasePlugin 子类")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _clear_pycache(manifest: PluginManifest) -> None:
        pycache = manifest.plugins_dir / "__pycache__"
        if pycache.exists():
            import shutil

            try:
                shutil.rmtree(pycache)
            except Exception as e:
                LOG.debug("清除 __pycache__ 失败: %s", e)
