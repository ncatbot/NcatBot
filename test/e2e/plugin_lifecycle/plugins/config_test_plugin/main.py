"""配置测试插件 - 测试与 PluginConfigService 的协作"""

from typing import List
from ncatbot.plugin_system import NcatBotPlugin, command_registry
from ncatbot.core import GroupMessageEvent
from ncatbot.utils import get_log

LOG = get_log("TestPlugins")


class ConfigTestPlugin(NcatBotPlugin):
    """配置测试插件 - 测试与 PluginConfigService 的协作"""

    name = "config_test_plugin"
    version = "1.0.0"

    # 配置追踪
    config_values_on_load: dict = {}
    config_change_history: List[tuple] = []

    async def on_load(self):
        LOG.debug("ConfigTestPlugin on_load called")

        # 注册配置项
        self.register_config(
            name="api_key",
            default_value="default_api_key",
            description="API密钥配置",
        )
        self.register_config(
            name="max_retries",
            default_value=3,
            description="最大重试次数",
            value_type=int,
        )
        self.register_config(
            name="enabled", default_value=True, description="是否启用", value_type=bool
        )

        # 记录加载时的配置值
        ConfigTestPlugin.config_values_on_load = {
            "api_key": self.config["api_key"],
            "max_retries": self.config["max_retries"],
            "enabled": self.config["enabled"],
        }

    async def on_close(self):
        LOG.debug("ConfigTestPlugin on_close called")

    @command_registry.command("cfg_get", description="获取配置", prefixes=["", "/"])
    async def cfg_get(self, event: GroupMessageEvent, key: str = ""):
        if key:
            value = self.config.get(key, "NOT_FOUND")
            await event.reply(f"Config {key}: {value}")
        else:
            await event.reply(f"All configs: {dict(self.config)}")

    @command_registry.command("cfg_set", description="设置配置", prefixes=["", "/"])
    async def cfg_set(self, event: GroupMessageEvent, key: str, value: str):
        old = self.config.get(key)
        self.set_config(key, value)
        ConfigTestPlugin.config_change_history.append((key, old, value))
        await event.reply(f"Config {key}: {old} -> {value}")

    @classmethod
    def reset_counters(cls):
        cls.config_values_on_load = {}
        cls.config_change_history = []
