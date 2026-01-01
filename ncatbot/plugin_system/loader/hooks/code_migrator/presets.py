"""
代码迁移框架 - 预设迁移规则

这里定义了 ncatbot 项目的预设迁移规则，用于自动更新废弃的导入路径和符号名称。
"""

from __future__ import annotations

from .migrator import CodeMigrator
from .rules import ImportReplacementRule, SelectiveImportReplacementRule


def create_default_migrator() -> CodeMigrator:
    """
    创建包含默认迁移规则的迁移器

    当前包含的迁移规则:
    1. BaseMessageEvent -> MessageEvent (ncatbot.core.event -> ncatbot.core)
    2. NcatBotEvent 导入路径变更 (ncatbot.plugin_system.event -> ncatbot.core)
    3. NcatBotEvent 从 ncatbot.plugin_system 选择性迁移到 ncatbot.core
    """
    migrator = CodeMigrator()

    # 规则1: BaseMessageEvent -> MessageEvent
    # 导入路径: ncatbot.core.event -> ncatbot.core
    migrator.register_rule(
        ImportReplacementRule(
            name="BaseMessageEvent_to_MessageEvent",
            description="将 BaseMessageEvent 重命名为 MessageEvent，并更新导入路径",
            old_import="ncatbot.core.event",
            new_import="ncatbot.core",
            old_names={"BaseMessageEvent": "MessageEvent"},
        )
    )

    # 规则2: NcatBotEvent 导入路径变更
    # ncatbot.plugin_system.event -> ncatbot.core
    migrator.register_rule(
        ImportReplacementRule(
            name="NcatBotEvent_import_path",
            description="更新 NcatBotEvent 的导入路径",
            old_import="ncatbot.plugin_system.event",
            new_import="ncatbot.core",
            old_names={},
        )
    )

    # 规则3: NcatBotEvent 从 ncatbot.plugin_system 迁移到 ncatbot.core
    # 使用选择性迁移，只迁移 NcatBotEvent，保留其他导入
    migrator.register_rule(
        SelectiveImportReplacementRule(
            name="NcatBotEvent_from_plugin_system",
            description="仅将 NcatBotEvent 从 ncatbot.plugin_system 迁移到 ncatbot.core",
            old_import="ncatbot.plugin_system",
            new_import="ncatbot.core",
            target_names={"NcatBotEvent"},
            renames={},
        )
    )

    return migrator
