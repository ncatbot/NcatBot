"""过滤器测试插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.filter_system.decorators import (
    group_filter,
    private_filter,
    admin_filter,
    root_filter,
    filter,
)
from ncatbot.core.service.builtin.unified_registry.filter_system.builtin import (
    GroupFilter,
    PrivateFilter,
    AdminFilter,
    CustomFilter,
    TrueFilter,
)
from ncatbot.core import MessageEvent


class FilterTestPlugin(NcatBotPlugin):
    name = "filter_test_plugin"
    version = "1.0.0"
    description = "过滤器测试"

    async def on_load(self):
        pass

    # ==================== 群聊过滤器 ====================

    @group_filter
    @command_registry.command("group_only")
    async def group_only_cmd(self, event: MessageEvent):
        """仅群聊可用的命令"""
        await event.reply("这是群聊专用命令")

    # ==================== 私聊过滤器 ====================

    @private_filter
    @command_registry.command("private_only")
    async def private_only_cmd(self, event: MessageEvent):
        """仅私聊可用的命令"""
        await event.reply("这是私聊专用命令")

    # ==================== 管理员过滤器 ====================

    @admin_filter
    @command_registry.command("ban")
    async def ban_cmd(self, event: MessageEvent, user_id: str):
        """管理员专用封禁命令"""
        await event.reply(f"已封禁用户: {user_id}")

    @admin_filter
    @command_registry.command("kick")
    async def kick_cmd(self, event: MessageEvent, user_id: str):
        """管理员专用踢出命令"""
        await event.reply(f"已踢出用户: {user_id}")

    # ==================== Root 过滤器 ====================

    @root_filter
    @command_registry.command("shutdown")
    async def shutdown_cmd(self, event: MessageEvent):
        """Root 专用关闭命令"""
        await event.reply("系统关闭中...")

    # ==================== 组合过滤器 ====================

    @group_filter
    @admin_filter
    @command_registry.command("mute")
    async def mute_cmd(self, event: MessageEvent, user_id: str, duration: int = 60):
        """群聊中管理员专用禁言命令"""
        await event.reply(f"已禁言用户 {user_id}，时长 {duration} 秒")

    # ==================== 指定群号的过滤器 ====================

    @filter(GroupFilter(allowed="123456"))
    @command_registry.command("special_group")
    async def special_group_cmd(self, event: MessageEvent):
        """仅特定群可用的命令"""
        await event.reply("这是特定群专用命令")

    @filter(GroupFilter(allowed=[123456, 789012]))
    @command_registry.command("multi_group")
    async def multi_group_cmd(self, event: MessageEvent):
        """多个指定群可用的命令"""
        await event.reply("这是多群专用命令")

    # ==================== 自定义过滤器 ====================

    @filter(CustomFilter(lambda e: len(str(e.raw_message)) < 50, "short_msg"))
    @command_registry.command("short_only")
    async def short_only_cmd(self, event: MessageEvent):
        """仅短消息可用的命令"""
        await event.reply("消息很短")

    # ==================== 组合过滤器 (使用 | 和 &) ====================

    @filter(GroupFilter() | PrivateFilter())
    @command_registry.command("any_chat")
    async def any_chat_cmd(self, event: MessageEvent):
        """群聊或私聊都可用"""
        await event.reply("任意聊天类型")

    @filter(GroupFilter() & AdminFilter())
    @command_registry.command("group_admin")
    async def group_admin_cmd(self, event: MessageEvent):
        """群聊且管理员"""
        await event.reply("群聊管理员")

    # ==================== TrueFilter 测试 ====================

    @filter(TrueFilter())
    @command_registry.command("always_pass")
    async def always_pass_cmd(self, event: MessageEvent):
        """永远通过的命令"""
        await event.reply("总是通过")
