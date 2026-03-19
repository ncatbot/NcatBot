"""
common/08_command_group — 命令组分层路由插件

演示功能:
  - 使用 CommandGroupHook 实现分层命令
  - 参数类型自动绑定（int/float/str/At）
  - 命令别名支持
  - @hook.subcommand() 装饰器注册子命令并由主 handler 分发
"""

import inspect
from ncatbot.core import CommandGroupHook, registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class CommandGroupDemoPlugin(NcatBotPlugin):
    name = "command_group_common"
    version = "1.0.0"
    author = "NcatBot"
    description = "命令组分层路由示例 — CommandGroupHook 正确用法"

    # ============================================================================
    # 方案 1: Admin 命令组 — 支持 kick/ban 子命令
    # ============================================================================
    admin_hook = CommandGroupHook("admin", "/admin", "a", ignore_case=True)

    @admin_hook.subcommand("kick", "remove")
    async def admin_kick(self, event: GroupMessageEvent, user_id: int):
        """踢出成员: /admin kick 12345"""
        try:
            await event.api.manage.set_group_kick(
                group_id=event.group_id, user_id=user_id
            )
            await event.reply(f"✓ 已踢出成员 {user_id}")
        except Exception as e:
            await event.reply(f"✗ 踢出失败: {e}")

    @admin_hook.subcommand("ban")
    async def admin_ban(
        self, event: GroupMessageEvent, user_id: int, minutes: int = 60
    ):
        """禁言成员: /admin ban 12345 或 /admin ban 12345 120"""
        try:
            await event.api.manage.set_group_ban(
                group_id=event.group_id,
                user_id=user_id,
                duration=minutes * 60,
            )
            await event.reply(f"✓ 已禁言成员 {user_id} {minutes} 分钟")
        except Exception as e:
            await event.reply(f"✗ 禁言失败: {e}")

    @registrar.on_group_message()
    @admin_hook
    async def on_admin(self, event: GroupMessageEvent, **kwargs):
        """处理 admin 命令组

        CommandGroupHook 会自动识别子命令，提取参数到 kwargs
        主 handler 通过检查 kwargs 来调度到真正的子命令处理器
        """
        # 获取消息中的子命令名
        message_text = event.data.message.text.strip()
        # 提取命令名后的第一个单词（子命令）
        parts = message_text.split(None, 1)
        if len(parts) < 2:
            await event.reply(
                "❓ 缺少子命令。用法: /admin <kick|ban> <user_id> [minutes]"
            )
            return

        subcommand_text = parts[1].split()[0].lower() if parts[1] else None
        if not subcommand_text:
            await event.reply("❓ 缺少子命令")
            return

        # 根据子命令查找处理器
        hooks = self.admin_hook._subcommands
        # 找到匹配的子命令处理器（不区分大小写）
        handler = None
        for cmd_name, cmd_handler in hooks.items():
            if cmd_name == subcommand_text.lower():
                handler = cmd_handler
                break

        if handler:
            # 调用子命令处理器，传入提取的参数
            sig = inspect.signature(handler)
            allowed_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            await handler(self, event, **allowed_kwargs)
        else:
            await event.reply(f"❌ 未知的子命令: {subcommand_text}")

    # ============================================================================
    # 方案 2: Calc 命令组 — 支持 add/divide/echo 子命令
    # ============================================================================
    calc_hook = CommandGroupHook("calc")

    @calc_hook.subcommand("add")
    async def calc_add(self, event: GroupMessageEvent, a: int, b: int):
        """加法: /calc add 10 20"""
        result = a + b
        await event.reply(f"📊 {a} + {b} = {result}")

    @calc_hook.subcommand("divide")
    async def calc_divide(self, event: GroupMessageEvent, a: float, b: float):
        """除法: /calc divide 10 3"""
        if b == 0:
            await event.reply("✗ 错误: 除以零")
        else:
            result = a / b
            await event.reply(f"📊 {a} / {b} = {result}")

    @calc_hook.subcommand("echo")
    async def calc_echo(self, event: GroupMessageEvent, text: str):
        """回显: /calc echo hello world"""
        await event.reply(f"🔊 {text}")

    @registrar.on_group_message()
    @calc_hook
    async def on_calc(self, event: GroupMessageEvent, **kwargs):
        """处理计算器命令"""
        message_text = event.data.message.text.strip()
        parts = message_text.split(None, 1)
        if len(parts) < 2:
            await event.reply("❓ 缺少子命令。用法: /calc <add|divide|echo> [args...]")
            return

        subcommand_text = parts[1].split()[0].lower() if parts[1] else None
        if not subcommand_text:
            return

        hooks = self.calc_hook._subcommands
        handler = None
        for cmd_name, cmd_handler in hooks.items():
            if cmd_name == subcommand_text.lower():
                handler = cmd_handler
                break

        if handler:
            sig = inspect.signature(handler)
            allowed_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            await handler(self, event, **allowed_kwargs)
        else:
            await event.reply(f"❌ 未知的子命令: {subcommand_text}")

    # ============================================================================
    # 方案 3: Help 命令 — 多别名支持
    # ============================================================================
    help_hook = CommandGroupHook("help", "?", ignore_case=True)

    @help_hook.subcommand("admin")
    async def help_admin(self, event: GroupMessageEvent):
        """管理员帮助"""
        await event.reply(
            "Admin Commands:\n/admin kick <id>\n/admin ban <id> [minutes]"
        )

    @help_hook.subcommand("calc")
    async def help_calc(self, event: GroupMessageEvent):
        """计算器帮助"""
        await event.reply(
            "Calc Commands:\n/calc add <a> <b>\n/calc divide <a> <b>\n/calc echo <text>"
        )

    @registrar.on_group_message()
    @help_hook
    async def on_help(self, event: GroupMessageEvent, **kwargs):
        """处理帮助命令 (支持 /help 或 /?)"""
        message_text = event.data.message.text.strip()
        parts = message_text.split(None, 1)

        if len(parts) < 2:
            # 无子命令时显示通用帮助
            await event.reply(
                "📖 Available Commands:\n"
                "  /help admin - Admin commands\n"
                "  /help calc - Calc commands"
            )
            return

        subcommand_text = parts[1].split()[0].lower() if parts[1] else None
        if not subcommand_text:
            return

        hooks = self.help_hook._subcommands
        handler = None
        for cmd_name, cmd_handler in hooks.items():
            if cmd_name == subcommand_text.lower():
                handler = cmd_handler
                break

        if handler:
            await handler(self, event)
        else:
            await event.reply(f"❌ 未知的帮助主题: {subcommand_text}")
