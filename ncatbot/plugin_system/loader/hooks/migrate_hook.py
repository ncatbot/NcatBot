from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ....utils import get_log

import toml

from .code_migrator import migrate_all_plugins

LOG = get_log("MigrateHook")


def find_entry_file(plugin_dir: Path) -> Optional[Path]:
    # Scan the plugin directory (non-recursively) for .py files and
    # return the first file that defines a plugin class.
    for p in sorted(plugin_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix != ".py":
            continue
        try:
            class_name, _ = parse_plugin_class(p)
        except Exception:
            class_name = None
        if class_name:
            return p
    return None


def parse_plugin_class(pyfile: Path) -> (Optional[str], Dict[str, Any]):
    src = pyfile.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            attrs: Dict[str, Any] = {}
            has_onload = False
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            key = t.id
                            try:
                                val = ast.literal_eval(stmt.value)
                            except Exception:
                                val = None
                            attrs[key] = val
                if isinstance(stmt, ast.FunctionDef) and stmt.name in (
                    "on_load",
                    "__onload__",
                ):
                    has_onload = True
            if "name" in attrs or "version" in attrs or has_onload:
                return node.name, attrs
    return None, {}


def read_requirements(req_file: Path) -> List[str]:
    if not req_file.exists():
        return []
    lines: List[str] = []
    for ln in req_file.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("-"):
            continue
        lines.append(s)
    return lines


def build_manifest(
    plugin_dir: Path,
    entry_file: Path,
    class_name: str,
    attrs: Dict[str, Any],
    reqs: List[str],
) -> Dict[str, Any]:
    main_rel = entry_file.name
    name = attrs.get("name") or plugin_dir.name
    version = attrs.get("version") or "0.0.0"
    author = attrs.get("author") or "Your Name"
    description = attrs.get("description") or ""
    deps = attrs.get("dependencies") or {}
    if deps is None:
        deps = {}
    manifest: Dict[str, Any] = {
        "name": name,
        "version": version,
        "author": author,
        "description": description,
        "main": main_rel,
        "entry_class": class_name,
    }
    manifest["dependencies"] = deps
    manifest["pip_dependencies"] = reqs or []
    return manifest


def write_manifest(
    manifest: Dict[str, Any], manifest_path: Path, dry_run: bool = False
) -> None:
    if dry_run:
        LOG.info("[dry-run] would write manifest to %s", manifest_path)
        LOG.info(toml.dumps(manifest))
        return
    manifest_path.write_text(toml.dumps(manifest), encoding="utf-8")
    LOG.info("WROTE %s", manifest_path)


def migrate_plugin(
    plugin_dir: Path, remove_req: bool = False, dry_run: bool = False
) -> None:
    manifest_path = plugin_dir / "manifest.toml"
    if manifest_path.exists():
        LOG.info("skip (already has manifest): %s", plugin_dir)
        return
    entry = find_entry_file(plugin_dir)
    if not entry:
        LOG.info("skip (no entry .py): %s", plugin_dir)
        return
    class_name, attrs = parse_plugin_class(entry)
    if not class_name:
        LOG.info("skip (no plugin class found): %s", plugin_dir)
        return
    reqs = read_requirements(plugin_dir / "requirements.txt")
    manifest = build_manifest(plugin_dir, entry, class_name, attrs, reqs)
    LOG.info("migrating %s -> %s", plugin_dir.name, manifest_path)
    write_manifest(manifest, manifest_path, dry_run=dry_run)
    if remove_req and (plugin_dir / "requirements.txt").exists():
        if dry_run:
            LOG.info("[dry-run] would remove %s", plugin_dir / "requirements.txt")
        else:
            (plugin_dir / "requirements.txt").unlink()
            LOG.info("removed: %s", plugin_dir / "requirements.txt")


def auto_migrate_plugin_code(
    plugins_root: Union[str, Path], dry_run: bool = False
) -> None:
    """
    自动迁移所有插件的代码（非交互式）

    在插件加载前自动执行代码迁移，更新废弃的导入路径和符号名称。
    """
    root = Path(plugins_root).expanduser().resolve()
    if not root.exists():
        LOG.debug("插件目录不存在，跳过代码迁移: %s", root)
        return

    LOG.debug("开始自动迁移插件代码: %s", root)
    results = migrate_all_plugins(root, dry_run=dry_run)

    total_files = sum(len(r) for r in results.values())
    if total_files > 0:
        LOG.info("代码迁移完成，共迁移 %d 个插件中的 %d 个文件", len(results), total_files)
        for plugin_name, plugin_results in results.items():
            for result in plugin_results:
                LOG.debug("  %s: %s", plugin_name, result.file_path.name)
    else:
        LOG.debug("没有需要迁移的代码")


def interactive_migrate_plugins(
    plugins_root: Union[str, Path], remove_req: bool = False, dry_run: bool = False
) -> None:
    """Iterate plugin directories under plugins_root and interactively ask to migrate.

    This function performs two migrations:
    1. Code migration: Updates deprecated imports and symbol names (automatic, non-interactive)
    2. Manifest migration: Creates manifest.toml for plugins without one (interactive)
    """
    root = Path(plugins_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Plugins root not found: {root}")

    # Step 1: 自动执行代码迁移（非交互式）
    auto_migrate_plugin_code(root, dry_run=dry_run)

    # Step 2: 交互式 manifest 迁移
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        manifest = entry / "manifest.toml"
        if manifest.exists():
            continue
        LOG.info(f"\nPlugin: {entry.name}")
        ans = (
            input("  No manifest.toml found — migrate this plugin? [y/N]: ")
            .strip()
            .lower()
        )
        if ans not in ("y", "yes"):
            LOG.info("  skip")
            continue
        try:
            migrate_plugin(entry, remove_req=remove_req, dry_run=dry_run)
        except Exception as e:
            LOG.info(" ERROR: %s", e)

