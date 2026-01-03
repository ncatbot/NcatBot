import sys
import importlib
import importlib.util
import importlib.machinery
import toml
from pathlib import Path
import re
import copy
from types import ModuleType
from typing import Dict, List, Optional

from ncatbot.utils import get_log

from ..config import config
from ..packhelper import PackageHelper

LOG = get_log("ModuleImporter")
_AUTO_INSTALL = config.auto_install_pip_pack


class _ModuleImporter:
    """把「目录->模块对象」的细节收敛到这里，方便做单元测试。"""

    def __init__(self):
        # 存储每个插件解析出的 manifest 数据： name -> dict
        self._manifests: Dict[str, dict] = {}
        # 插件名 -> 插件目录的绝对路径
        self._plugin_folders: Dict[str, Path] = {}
        # 原始插件名 -> sanitized 名称（用于生成合法的包名）
        self._sanitized_names: Dict[str, str] = {}
        self._used_sanitized: set = set()

    def _ensure_sanitized(self, plugin_name: str) -> str:
        """Generate and record a sanitized package-friendly name for a plugin.

        The sanitized name contains only ASCII letters, digits and underscores,
        and will not start with a digit. If a collision occurs the name will be
        suffixed with `_1`, `_2`, ... to ensure uniqueness. Returns the
        sanitized name.
        """
        if plugin_name in self._sanitized_names:
            return self._sanitized_names[plugin_name]

        base_sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", plugin_name)
        if base_sanitized and base_sanitized[0].isdigit():
            base_sanitized = f"_{base_sanitized}"
        if not base_sanitized:
            base_sanitized = "_plugin"
        sanitized = base_sanitized
        idx = 1
        while sanitized in self._used_sanitized:
            sanitized = f"{base_sanitized}_{idx}"
            idx += 1
        self._used_sanitized.add(sanitized)
        self._sanitized_names[plugin_name] = sanitized
        LOG.debug("插件名映射: %s -> %s", plugin_name, sanitized)
        return sanitized

    def _ensure_entry(self, plugin_dir: Path, main_field: str) -> bool:
        """Check whether the manifest 'main' entry exists under `plugin_dir`.

        Supports values with or without a `.py` suffix. Returns True if the
        entry file exists, False otherwise.
        """
        main_path = plugin_dir / main_field
        if main_path.exists():
            return True
        # 如果未带 .py 后缀，再尝试添加 .py
        if (
            not main_field.endswith(".py")
            and (plugin_dir / (main_field + ".py")).exists()
        ):
            return True
        LOG.warning(
            "文件夹 %s 的 manifest 'main' 指向的入口文件未找到: %s，跳过",
            plugin_dir.name,
            main_field,
        )
        return False

    def _index_single_plugin(self, plugin_dir: Path) -> Optional[str]:
        """索引单个插件目录

        Args:
            plugin_dir: 插件目录路径

        Returns:
            插件名称，如果索引失败则返回 None
        """
        plugin_dir = Path(plugin_dir).resolve()
        manifest_path = plugin_dir / "manifest.toml"

        if not plugin_dir.is_dir():
            LOG.debug("跳过非目录: %s", plugin_dir)
            return None

        if not manifest_path.exists():
            LOG.debug("跳过缺少 manifest.toml 的目录: %s", plugin_dir)
            return None

        try:
            manifest = toml.load(manifest_path)

            # 基本校验：必须包含 name/version/main
            plugin_name = manifest.get("name")
            version = manifest.get("version")
            main_field = manifest.get("main")

            if not plugin_name or not version or not main_field:
                LOG.warning("插件 %s 的 manifest 缺少必填字段，跳过", plugin_dir)
                return None

            if not self._ensure_entry(plugin_dir, main_field):
                return None

            if plugin_name in self._plugin_folders:
                LOG.warning("插件 %s 已存在，跳过加载", plugin_name)
                LOG.info(
                    "文件夹 %s 和文件夹 %s 下存在同名插件 %s",
                    self._plugin_folders[plugin_name],
                    plugin_dir,
                    plugin_name,
                )
                return None

            self._plugin_folders[plugin_name] = plugin_dir
            self._manifests[plugin_name] = manifest
            self._ensure_sanitized(plugin_name)

            LOG.debug("已索引插件: %s (路径: %s)", plugin_name, plugin_dir)
            return plugin_name

        except Exception:
            LOG.exception("解析 manifest 失败: %s", manifest_path)
            return None

    def index_all_plugins(self, plugin_root: Path) -> List[str]:
        """扫描并索引 directory 下所有合法的插件，返回插件名列表"""
        for entry in plugin_root.iterdir():
            self._index_single_plugin(entry)
        return list(self._plugin_folders.keys())

    def index_external_plugin(self, plugin_dir: Path) -> Optional[str]:
        """索引一个外部插件文件夹

        Args:
            plugin_dir: 插件文件夹路径

        Returns:
            插件名称，如果索引失败则返回 None
        """
        return self._index_single_plugin(plugin_dir)

    def get_plugin_name_by_folder(self, folder_name: str) -> Optional[str]:
        """根据文件夹名称获取插件名称

        支持两种情况：
        1. folder_name 是完整路径
        2. folder_name 是文件夹名称，需要匹配存储路径的最后一部分
        """
        folder_path = Path(folder_name)
        for plugin_name, stored_path in self._plugin_folders.items():
            # 完整路径匹配
            if stored_path == folder_path or str(stored_path) == folder_name:
                return plugin_name
            # 匹配路径的最后一部分（文件夹名）
            if stored_path.name == folder_name:
                return plugin_name
        return None

    def get_plugin_manifests(self, plugin_root: Path) -> Dict[str, Dict]:
        if not self._manifests:
            raise ValueError("未索引任何插件")
        return copy.copy(self._manifests)

    def unload_plugin_module(self, plugin_name: str) -> bool:
        """卸载指定模块及其所有子模块"""
        if not plugin_name or not isinstance(plugin_name, str):
            LOG.warning("无效的模块名称: %s", plugin_name)
            return False

        pkg_name = self._get_plugin_pkg_name(plugin_name)

        # Collect candidates: modules that are the plugin package or its submodules.
        modules_to_remove = [
            module_name
            for module_name in list(sys.modules.keys())
            if module_name == pkg_name or module_name.startswith(f"{pkg_name}.")
        ]

        if not modules_to_remove:
            LOG.debug("模块 %s 未加载，无需卸载", plugin_name)
            return True

        removed_count = 0
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
                removed_count += 1
                LOG.debug("已卸载模块: %s", module_name)
            except KeyError:
                # already removed concurrently; ignore
                pass

        # Invalidate import caches in case files change on disk later
        try:
            importlib.invalidate_caches()
        except Exception:
            LOG.debug("invalidate_caches failed for %s", plugin_name)

        LOG.info("成功卸载模块 %s (共 %d 个模块)", plugin_name, removed_count)
        return True

    def load_plugin_module(self, plugin_name: str) -> Optional[ModuleType]:
        # 清除导入缓存，确保读取最新的源文件
        importlib.invalidate_caches()

        # 清除插件目录的 __pycache__，确保重新编译源文件
        plugin_dir = self._get_plugin_dir(plugin_name)
        pycache_dir = plugin_dir / "__pycache__"
        if pycache_dir.exists():
            import shutil

            try:
                shutil.rmtree(pycache_dir)
                LOG.debug("已清除插件 %s 的字节码缓存", plugin_name)
            except Exception as e:
                LOG.warning("清除字节码缓存失败: %s", e)

        original_sys_path = sys.path.copy()
        created_pkg = False
        created_module = False
        try:
            plugin_path = str(plugin_dir)
            sys.path.insert(0, plugin_path)

            pkg_name = self._get_plugin_pkg_name(plugin_name)
            module_name = self._get_plugin_main_module_name(plugin_name)

            if pkg_name not in sys.modules:
                # 创建一个空的模块作为包
                pkg_module = importlib.util.module_from_spec(
                    importlib.machinery.ModuleSpec(pkg_name, None, is_package=True)
                )
                pkg_module.__path__ = [plugin_path]
                sys.modules[pkg_name] = pkg_module
                created_pkg = True

            entry_file = self._get_plugin_entry_file(plugin_name)
            spec = importlib.util.spec_from_file_location(module_name, entry_file)
            if spec is None or spec.loader is None:
                LOG.exception(
                    "无法为插件 %s 创建模块 spec 或 loader 缺失: %s",
                    plugin_name,
                    entry_file,
                )
                raise ImportError(
                    f"Cannot load plugin {plugin_name}: spec or loader is None for {entry_file}"
                )
            module = importlib.util.module_from_spec(spec)
            # 明确保存 spec，便于调试/反射
            module.__spec__ = spec

            # 显式指定包名，确保相对导入 (from . import xxx) 正常工作
            module.__package__ = pkg_name

            # 注册模块对象（如果 exec 失败，需要回滚）
            sys.modules[module_name] = module
            created_module = True

            try:
                spec.loader.exec_module(module)
            except Exception:
                # 回滚我们对此次导入所做的 sys.modules 修改（仅回滚此函数中新建的项）
                if created_module:
                    sys.modules.pop(module_name, None)
                if created_pkg:
                    sys.modules.pop(pkg_name, None)
                raise

            return module
        except Exception as e:
            LOG.error("导入模块 %s 时出错: %s", plugin_name, e)
            raise
        finally:
            sys.path = original_sys_path

    def _get_plugin_pkg_name(self, name: str) -> str:
        # 使用 sanitized 名称生成包名，若未记录则退回到原始 name
        sanitized = self._sanitized_names.get(name, name)
        return f"ncatbot_plugin.{sanitized}"

    def _get_plugin_entry_stem(self, name: str) -> str:
        """手滑把 .py 漏了也无所谓了"""
        manifest = self.get_plugin_manifest(name)
        if manifest is None:
            raise ValueError(f"插件 {name} 的 manifest 未找到")
        filename: str = manifest.get("main", "")
        if filename.endswith(".py"):
            return filename[:-3]
        return filename

    def _get_plugin_entry_file(self, name: str) -> str:
        return str(
            self._get_plugin_dir(name) / (self._get_plugin_entry_stem(name) + ".py")
        )

    def _get_plugin_main_module_name(self, name: str) -> str:
        return f"{self._get_plugin_pkg_name(name)}.{self._get_plugin_entry_stem(name)}"

    def get_plugin_manifest(self, plugin_name: str) -> Optional[dict]:
        """返回已解析的 manifest（若 inspect_all 已解析过）。

        注意：如果未调用 `inspect_all` 此方法可能返回 `None`。
        """
        return self._manifests.get(plugin_name)

    def _get_plugin_dir(self, name: str) -> Path:
        """获取插件目录路径"""
        return self._plugin_folders[name]

    def _maybe_install_deps(self, plugin_path: Path) -> None:
        if not _AUTO_INSTALL:
            return

        def ensure_req_from_requirements():
            req_file = (
                plugin_path / "requirements.txt"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".requirements.txt")
            )
            if not req_file.exists():
                return

            for line in req_file.read_text(encoding="utf-8").splitlines():
                req = line.strip()
                if not req or req.startswith("#") or req.startswith("-"):
                    continue
                self._ensure_package(req)

        def ensure_req_from_pyproject():
            pyproject = (
                plugin_path / "pyproject.toml"
                if plugin_path.is_dir()
                else plugin_path.with_suffix(".pyproject.toml")
            )
            if not pyproject.exists():
                return
            data = toml.load(pyproject)
            requires = data.get("project", {}).get("dependencies", [])
            for req in requires:
                self._ensure_package(req)

        ensure_req_from_pyproject()
        ensure_req_from_requirements()

    def _ensure_package(self, req: str) -> None:
        """检查包是否存在，不存在则安装。"""
        PackageHelper.ensure(req)
