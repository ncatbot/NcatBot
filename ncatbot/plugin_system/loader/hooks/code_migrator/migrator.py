"""
代码迁移框架 - 迁移器核心
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from .....utils import get_log
from .base import MigrationResult, MigrationRule

LOG = get_log("CodeMigrator")


class CodeMigrator:
    """代码迁移器"""

    def __init__(self):
        self._rules: List[MigrationRule] = []
        self._migrated_files: Set[Path] = set()

    def register_rule(self, rule: MigrationRule) -> "CodeMigrator":
        """注册迁移规则"""
        self._rules.append(rule)
        LOG.debug("注册迁移规则: %s", rule.name)
        return self

    def migrate_file(
        self, file_path: Path, dry_run: bool = False
    ) -> Optional[MigrationResult]:
        """
        迁移单个文件

        Args:
            file_path: 文件路径
            dry_run: 是否仅预览（不写入文件）

        Returns:
            迁移结果，如果没有变更则返回 None
        """
        if not file_path.exists() or not file_path.is_file():
            return None

        if file_path.suffix != ".py":
            return None

        try:
            original_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            LOG.warning("无法读取文件 %s: %s", file_path, e)
            return None

        migrated_content = original_content
        all_changes: List[str] = []

        for rule in self._rules:
            migrated_content, changes = rule.apply(migrated_content, file_path)
            all_changes.extend(changes)

        result = MigrationResult(
            file_path=file_path,
            original_content=original_content,
            migrated_content=migrated_content,
            changes=all_changes,
        )

        if result.has_changes:
            if dry_run:
                LOG.info("[dry-run] 将迁移文件: %s", file_path)
                for change in all_changes:
                    LOG.info("  - %s", change)
            else:
                try:
                    file_path.write_text(migrated_content, encoding="utf-8")
                    self._migrated_files.add(file_path)
                    LOG.info("已迁移文件: %s", file_path)
                    for change in all_changes:
                        LOG.info("  - %s", change)
                except Exception as e:
                    LOG.error("写入文件失败 %s: %s", file_path, e)
                    return None

        return result if result.has_changes else None

    def migrate_directory(
        self,
        directory: Path,
        recursive: bool = True,
        dry_run: bool = False,
    ) -> List[MigrationResult]:
        """
        迁移目录下的所有 Python 文件

        Args:
            directory: 目录路径
            recursive: 是否递归处理子目录
            dry_run: 是否仅预览

        Returns:
            所有有变更的迁移结果列表
        """
        results: List[MigrationResult] = []

        if not directory.exists() or not directory.is_dir():
            return results

        pattern = "**/*.py" if recursive else "*.py"
        for file_path in directory.glob(pattern):
            result = self.migrate_file(file_path, dry_run=dry_run)
            if result:
                results.append(result)

        return results

    def get_migrated_files(self) -> Set[Path]:
        """获取已迁移的文件列表"""
        return self._migrated_files.copy()

    def reset(self) -> None:
        """重置迁移状态"""
        self._migrated_files.clear()
