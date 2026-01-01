"""
代码迁移框架

提供可扩展的代码迁移功能，用于自动更新插件代码中的废弃导入和符号名称。

使用示例:

    # 使用默认迁移器迁移单个插件
    from ncatbot.plugin_system.loader.hooks.code_migrator import migrate_plugin_code
    results = migrate_plugin_code(Path("plugins/MyPlugin"))

    # 迁移所有插件
    from ncatbot.plugin_system.loader.hooks.code_migrator import migrate_all_plugins
    all_results = migrate_all_plugins(Path("plugins"))

    # 自定义迁移器
    from ncatbot.plugin_system.loader.hooks.code_migrator import (
        CodeMigrator,
        ImportReplacementRule,
    )
    migrator = CodeMigrator()
    migrator.register_rule(
        ImportReplacementRule(
            name="my_rule",
            description="我的迁移规则",
            old_import="old.module",
            new_import="new.module",
            old_names={"OldClass": "NewClass"},
        )
    )
    results = migrator.migrate_directory(Path("plugins/MyPlugin"))
"""

from .base import MigrationResult, MigrationRule
from .rules import (
    ImportReplacementRule,
    SelectiveImportReplacementRule,
    SymbolRenameRule,
)
from .migrator import CodeMigrator
from .presets import create_default_migrator
from .utils import migrate_plugin_code, migrate_all_plugins

__all__ = [
    # 基础类型
    "MigrationResult",
    "MigrationRule",
    # 内置规则
    "ImportReplacementRule",
    "SelectiveImportReplacementRule",
    "SymbolRenameRule",
    # 迁移器
    "CodeMigrator",
    # 预设
    "create_default_migrator",
    # 便捷函数
    "migrate_plugin_code",
    "migrate_all_plugins",
]
