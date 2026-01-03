"""
RBAC 和过滤器集成测试插件

用于测试 RBAC 服务与各种过滤器的联动。
"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core import MessageEvent
from ncatbot.core.service.builtin.unified_registry import (
    command_registry,
    admin_filter,
    root_filter,
    group_filter,
    private_filter,
)


class RBACTestPlugin(NcatBotPlugin):
    """RBAC 测试插件"""

    name = "rbac_test_plugin"
    version = "1.0.0"

    # 记录命令执行情况
    command_executions: list = []

    @classmethod
    def reset_counters(cls):
        """重置计数器"""
        cls.command_executions = []

    # ==================== 需要管理员权限的命令 ====================

    @admin_filter
    @command_registry.command(name="admin_cmd", description="需要管理员权限的命令")
    async def admin_cmd(self, event: MessageEvent):
        """管理员命令"""
        self.command_executions.append(("admin_cmd", event.user_id))
        await event.reply(f"admin_cmd executed by {event.user_id}")

    @admin_filter
    @command_registry.command(
        name="kick_user", description="踢出用户（需要管理员权限）"
    )
    async def kick_user_cmd(self, event: MessageEvent, target: str):
        """踢人命令"""
        self.command_executions.append(("kick_user", event.user_id, target))
        await event.reply(f"kicked {target}")

    # ==================== 需要 Root 权限的命令 ====================

    @root_filter
    @command_registry.command(name="root_cmd", description="需要 Root 权限的命令")
    async def root_cmd(self, event: MessageEvent):
        """Root 命令"""
        self.command_executions.append(("root_cmd", event.user_id))
        await event.reply(f"root_cmd executed by {event.user_id}")

    @root_filter
    @command_registry.command(name="shutdown", description="关闭系统（需要 Root 权限）")
    async def shutdown_cmd(self, event: MessageEvent):
        """关机命令"""
        self.command_executions.append(("shutdown", event.user_id))
        await event.reply("system shutdown initiated")

    # ==================== 组合过滤器命令 ====================

    @admin_filter
    @group_filter
    @command_registry.command(name="group_admin_cmd", description="群聊管理员命令")
    async def group_admin_cmd(self, event: MessageEvent):
        """群聊管理员命令"""
        self.command_executions.append(
            ("group_admin_cmd", event.user_id, event.group_id)
        )
        await event.reply("group_admin_cmd executed")

    @root_filter
    @private_filter
    @command_registry.command(name="private_root_cmd", description="私聊 Root 命令")
    async def private_root_cmd(self, event: MessageEvent):
        """私聊 Root 命令"""
        self.command_executions.append(("private_root_cmd", event.user_id))
        await event.reply("private_root_cmd executed")

    # ==================== 无权限要求的命令 ====================

    @command_registry.command(name="public_cmd", description="公开命令（无权限要求）")
    async def public_cmd(self, event: MessageEvent):
        """公开命令"""
        self.command_executions.append(("public_cmd", event.user_id))
        await event.reply("public_cmd executed")

    @group_filter
    @command_registry.command(name="group_cmd", description="群聊命令（无权限要求）")
    async def group_cmd(self, event: MessageEvent):
        """群聊命令"""
        self.command_executions.append(("group_cmd", event.user_id))
        await event.reply("group_cmd executed")
