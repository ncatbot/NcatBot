"""完整功能测试插件 - 测试所有服务的协作"""

from typing import List
from ncatbot.plugin_system import NcatBotPlugin, command_registry
from ncatbot.core import GroupMessageEvent
from ncatbot.utils import get_log

LOG = get_log("TestPlugins")


class FullFeaturePlugin(NcatBotPlugin):
    """完整功能测试插件 - 测试所有服务的协作"""

    name = "full_feature_plugin"
    version = "2.0.0"

    # 综合追踪
    lifecycle_events: List[str] = []
    command_executions: List[str] = []
    handler_events: List[str] = []
    config_operations: List[str] = []

    def _init_(self):
        FullFeaturePlugin.lifecycle_events.append("_init_")

    async def on_load(self):
        FullFeaturePlugin.lifecycle_events.append("on_load")

        # 注册配置
        self.register_config("feature_enabled", True, "功能开关")
        self.register_config("feature_value", "initial", "功能值")
        FullFeaturePlugin.config_operations.append(
            f"registered:feature_enabled={self.config['feature_enabled']}"
        )

        # 注册事件处理器
        self.register_handler("ncatbot.message_event", self._handle_message)
        self.register_handler("full_feature.custom", self._handle_custom)

    async def _handle_message(self, event):
        # event.data 是实际的消息事件
        raw_msg = (
            getattr(event.data, "raw_message", str(event.data)[:20])
            if hasattr(event, "data")
            else str(event)[:20]
        )
        FullFeaturePlugin.handler_events.append(
            f"message:{raw_msg[:20] if isinstance(raw_msg, str) else raw_msg}"
        )

    async def _handle_custom(self, event):
        FullFeaturePlugin.handler_events.append(f"custom:{event}")

    async def on_close(self):
        FullFeaturePlugin.lifecycle_events.append("on_close")

    @command_registry.command("ff_status", prefixes=["", "/"])
    async def ff_status(self, event: GroupMessageEvent):
        FullFeaturePlugin.command_executions.append("ff_status")
        status = {
            "lifecycle": len(FullFeaturePlugin.lifecycle_events),
            "commands": len(FullFeaturePlugin.command_executions),
            "handlers": len(FullFeaturePlugin.handler_events),
            "configs": len(FullFeaturePlugin.config_operations),
        }
        await event.reply(f"Status: {status}")

    @command_registry.command("ff_config", prefixes=["", "/"])
    async def ff_config(
        self, event: GroupMessageEvent, action: str, key: str = "", value: str = ""
    ):
        if action == "get":
            val = self.config.get(key, "NOT_FOUND")
            FullFeaturePlugin.config_operations.append(f"get:{key}={val}")
            await event.reply(f"Config: {key}={val}")
        elif action == "set":
            self.set_config(key, value)
            FullFeaturePlugin.config_operations.append(f"set:{key}={value}")
            await event.reply(f"Set: {key}={value}")

    @classmethod
    def reset_counters(cls):
        cls.lifecycle_events = []
        cls.command_executions = []
        cls.handler_events = []
        cls.config_operations = []
