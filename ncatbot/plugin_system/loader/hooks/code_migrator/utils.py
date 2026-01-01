"""
代码迁移框架 - 便捷函数
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .....utils import get_log
from .base import MigrationResult
from .presets import create_default_migrator

LOG = get_log("CodeMigrator")


def migrate_plugin_code(
    plugin_dir: Path, dry_run: bool = False
) -> List[MigrationResult]:
    """
    迁移插件目录下的代码

    Args:
        plugin_dir: 插件目录
        dry_run: 是否仅预览

    Returns:
        迁移结果列表
    """
    migrator = create_default_migrator()
    return migrator.migrate_directory(plugin_dir, recursive=True, dry_run=dry_run)


def migrate_all_plugins(
    plugins_root: Path, dry_run: bool = False
) -> Dict[str, List[MigrationResult]]:
    """
    迁移所有插件的代码

    Args:
        plugins_root: 插件根目录
        dry_run: 是否仅预览

    Returns:
        {插件名: 迁移结果列表}
    """
    results: Dict[str, List[MigrationResult]] = {}

    if not plugins_root.exists():
        LOG.warning("插件目录不存在: %s", plugins_root)
        return results

    for entry in plugins_root.iterdir():
        if not entry.is_dir():
            continue

        plugin_results = migrate_plugin_code(entry, dry_run=dry_run)
        if plugin_results:
            results[entry.name] = plugin_results

    return results
