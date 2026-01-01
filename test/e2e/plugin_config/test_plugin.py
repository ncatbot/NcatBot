"""
Plugin Config E2E 测试插件
"""

from ncatbot.plugin_system import NcatBotPlugin, config_item
from ncatbot.core import GroupMessageEvent


class PluginConfigTestPlugin(NcatBotPlugin):
    """测试插件配置功能的插件"""

    name = "plugin_config_test_plugin"
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        # 注册配置项
        self.test_string = config_item(
            key="test_string",
            default="default_value",
            description="测试字符串配置"
        )
        self.test_number = config_item(
            key="test_number",
            default=42,
            description="测试数字配置"
        )
        self.test_bool = config_item(
            key="test_bool",
            default=True,
            description="测试布尔配置"
        )

    async def on_load(self):
        # 注册命令
        from ncatbot.plugin_system import command_registry

        @command_registry.command("config_test", description="配置测试命令")
        async def config_test_command(event: GroupMessageEvent):
            current_config = {
                "test_string": self.test_string.get(),
                "test_number": self.test_number.get(),
                "test_bool": self.test_bool.get()
            }
            await event.reply(f"当前配置: {current_config}")

        @command_registry.command("config_set", description="设置配置")
        async def config_set_command(event: GroupMessageEvent, key: str, value: str):
            try:
                if key == "test_string":
                    self.test_string.set(value)
                elif key == "test_number":
                    self.test_number.set(int(value))
                elif key == "test_bool":
                    self.test_bool.set(value.lower() in ("true", "1", "yes"))
                else:
                    await event.reply(f"未知配置项: {key}")
                    return

                await event.reply(f"配置已更新: {key} = {value}")
            except Exception as e:
                await event.reply(f"设置失败: {e}")

        @command_registry.command("config_save", description="保存配置")
        async def config_save_command(event: GroupMessageEvent):
            # 配置会自动保存，这里只是为了测试
            await event.reply("配置保存完成")
