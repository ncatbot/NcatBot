"""命令分组测试插件

测试：
- 使用 group() 创建命令组
- 在子组中注册命令
- 独立命令作为对照
"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core import MessageEvent


# 创建命令组
user_group = command_registry.group("user", description="用户管理")
config_group = command_registry.group("config", description="配置管理")


class CommandGroupsPlugin(NcatBotPlugin):
    name = "command_groups_plugin"
    version = "1.0.0"
    description = "命令分组测试"

    async def on_load(self):
        pass

    # ==================== 用户管理组内命令 ====================

    @user_group.command("info", description="查看用户信息")
    async def user_info_cmd(self, event: MessageEvent, user_id: str):
        """查看用户信息"""
        await event.reply(f"用户 {user_id} 的信息")

    @user_group.command("list", description="列出用户")
    async def user_list_cmd(self, event: MessageEvent, page: int = 1):
        """列出所有用户"""
        await event.reply(f"用户列表 (第 {page} 页)")

    @user_group.command("search", description="搜索用户")
    async def user_search_cmd(self, event: MessageEvent, keyword: str):
        """搜索用户"""
        await event.reply(f"搜索用户: {keyword}")

    # ==================== 配置管理组内命令 ====================

    @config_group.command("get", description="获取配置")
    async def config_get_cmd(self, event: MessageEvent, key: str):
        """获取配置项"""
        await event.reply(f"配置项 {key} 的值: (mock)")

    @config_group.command("set", description="设置配置")
    async def config_set_cmd(self, event: MessageEvent, key: str, value: str):
        """设置配置项"""
        await event.reply(f"已设置 {key} = {value}")

    @config_group.command("list", description="列出配置")
    async def config_list_cmd(self, event: MessageEvent):
        """列出所有配置"""
        await event.reply("所有配置项列表")

    # ==================== 独立命令（作为对照） ====================

    @command_registry.command("help", description="帮助信息")
    async def help_cmd(self, event: MessageEvent, cmd: str = None):
        """显示帮助信息"""
        if cmd:
            await event.reply(f"命令 {cmd} 的帮助信息")
        else:
            await event.reply("可用命令组: user, config")
