"""基础命令测试插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core.service.builtin.unified_registry.command_system.registry.decorators import (
    option,
    param,
)
from ncatbot.core import MessageEvent


class BasicCommandPlugin(NcatBotPlugin):
    name = "basic_command_plugin"
    version = "1.0.0"
    description = "基础命令测试"

    async def on_load(self):
        pass

    # ==================== 简单命令 ====================

    @command_registry.command("hello")
    async def hello_cmd(self, event: MessageEvent):
        """简单的问候命令"""
        await event.reply("你好！我是机器人。")

    @command_registry.command("ping")
    async def ping_cmd(self, event: MessageEvent):
        """健康检查命令"""
        await event.reply("pong!")

    # ==================== 带参数命令 ====================

    @command_registry.command("echo")
    async def echo_cmd(self, event: MessageEvent, text: str):
        """回显命令"""
        await event.reply(f"你说的是: {text}")

    @command_registry.command("add")
    async def add_cmd(self, event: MessageEvent, a: int, b: int):
        """加法命令"""
        result = a + b
        await event.reply(f"{a} + {b} = {result}")

    @command_registry.command("greet")
    async def greet_cmd(self, event: MessageEvent, name: str, greeting: str = "你好"):
        """带默认参数的命令"""
        await event.reply(f"{greeting}, {name}!")

    # ==================== 带选项命令 ====================

    @command_registry.command("deploy", description="部署应用")
    @option(short_name="v", long_name="verbose", help="显示详细信息")
    @option(short_name="f", long_name="force", help="强制部署")
    @param(name="env", default="dev", help="部署环境")
    async def deploy_cmd(
        self,
        event: MessageEvent,
        app_name: str,
        env: str = "dev",
        verbose: bool = False,
        force: bool = False,
    ):
        """部署命令，支持选项和命名参数"""
        result = f"正在部署 {app_name} 到 {env} 环境"
        if force:
            result += " (强制模式)"
        if verbose:
            result += "\n详细信息: 开始部署流程..."
        await event.reply(result)

    # ==================== 命令别名 ====================

    @command_registry.command("status", aliases=["stat", "st"], description="查看状态")
    async def status_cmd(self, event: MessageEvent):
        """带别名的状态命令"""
        await event.reply("机器人运行正常")
