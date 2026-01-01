from .migrate_hook import interactive_migrate_plugins, auto_migrate_plugin_code
from .code_migrator import (
    CodeMigrator,
    MigrationRule,
    MigrationResult,
    ImportReplacementRule,
    SelectiveImportReplacementRule,
    SymbolRenameRule,
    create_default_migrator,
    migrate_plugin_code,
    migrate_all_plugins,
)

__all__ = [
    # 迁移 hooks
    "interactive_migrate_plugins",
    "auto_migrate_plugin_code",
    # 迁移框架 - 基础类型
    "MigrationRule",
    "MigrationResult",
    # 迁移框架 - 内置规则
    "ImportReplacementRule",
    "SelectiveImportReplacementRule",
    "SymbolRenameRule",
    # 迁移框架 - 迁移器
    "CodeMigrator",
    "create_default_migrator",
    # 迁移框架 - 便捷函数
    "migrate_plugin_code",
    "migrate_all_plugins",
]
