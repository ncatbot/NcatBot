"""
插件清单模型

解析和验证 manifest.toml，提供统一的数据访问接口。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib

from ncatbot.utils import get_log

LOG = get_log("PluginManifest")


@dataclass
class PluginManifest:
    """插件清单，对应 manifest.toml 的内容。"""

    # 必填
    name: str
    version: str
    main: str  # 入口文件（带或不带 .py）
    # 可选
    entry_class: Optional[str] = None  # 为 None 时自动发现
    author: str = "Unknown"
    description: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    pip_dependencies: Dict[str, str] = field(default_factory=dict)

    # 运行时附加（不来自 toml）
    plugin_dir: Path = field(default=Path("."), repr=False)
    folder_name: str = ""

    # 保留原始数据供扩展使用
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # 工厂方法
    # ------------------------------------------------------------------

    @classmethod
    def from_toml(cls, manifest_path: Path) -> "PluginManifest":
        """从 manifest.toml 文件解析清单。

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 缺少必填字段或入口文件不存在
        """
        manifest_path = Path(manifest_path).resolve()
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.toml 不存在: {manifest_path}")

        with open(manifest_path, "rb") as f:
            raw = tomllib.load(f)
        plugin_dir = manifest_path.parent

        # 验证必填字段
        name = raw.get("name")
        version = raw.get("version")
        main_field = raw.get("main")

        missing = []
        if not name:
            missing.append("name")
        if not version:
            missing.append("version")
        if not main_field:
            missing.append("main")
        if missing:
            raise ValueError(f"manifest.toml 缺少必填字段 {missing}: {manifest_path}")

        # 类型断言（已通过上面的 missing 检查）
        assert name is not None
        assert version is not None
        assert main_field is not None

        # 验证入口文件存在
        entry_stem = main_field
        if entry_stem.endswith(".py"):
            entry_stem = entry_stem[:-3]
        entry_file = plugin_dir / f"{entry_stem}.py"
        if not entry_file.exists():
            raise ValueError(
                f"入口文件不存在: {entry_file} (manifest: {manifest_path})"
            )

        return cls(
            name=name,
            version=version,
            main=main_field,
            entry_class=raw.get("entry_class"),
            author=raw.get("author", "Unknown"),
            description=raw.get("description", ""),
            dependencies=raw.get("dependencies") or {},
            pip_dependencies=raw.get("pip_dependencies") or {},
            plugin_dir=plugin_dir,
            folder_name=plugin_dir.name,
            _raw=raw,
        )

    # ------------------------------------------------------------------
    # 便捷属性
    # ------------------------------------------------------------------

    @property
    def entry_stem(self) -> str:
        """入口文件名（无 .py 后缀）"""
        if self.main.endswith(".py"):
            return self.main[:-3]
        return self.main

    @property
    def entry_file(self) -> Path:
        """入口文件的完整路径"""
        return self.plugin_dir / f"{self.entry_stem}.py"

    def as_dict(self) -> Dict[str, Any]:
        """返回元数据字典"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
        }
