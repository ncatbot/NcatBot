"""事件处理器测试插件 - 测试与 register_handler 的协作"""

from typing import List
from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("TestPlugins")


class HandlerTestPlugin(NcatBotPlugin):
    """事件处理器测试插件 - 测试与 register_handler 的协作"""

    name = "handler_test_plugin"
    version = "1.0.0"

    # 事件追踪
    message_events: List[dict] = []
    custom_events: List[dict] = []
    handler_ids: List[str] = []

    async def on_load(self):
        LOG.debug("HandlerTestPlugin on_load called")

        # 注册消息事件处理器
        handler_id = self.register_handler(
            "ncatbot.message_event", self._on_message_event
        )
        HandlerTestPlugin.handler_ids.append(str(handler_id))

        # 注册自定义事件处理器
        custom_id = self.register_handler(
            "handler_test.custom_event", self._on_custom_event
        )
        HandlerTestPlugin.handler_ids.append(str(custom_id))

    async def _on_message_event(self, event):
        HandlerTestPlugin.message_events.append(
            {"raw_message": getattr(event, "raw_message", str(event))}
        )
        LOG.debug(f"HandlerTestPlugin received message event: {event}")

    async def _on_custom_event(self, event):
        HandlerTestPlugin.custom_events.append(
            {"data": event.data if hasattr(event, "data") else event}
        )
        LOG.debug(f"HandlerTestPlugin received custom event: {event}")

    async def on_close(self):
        LOG.debug("HandlerTestPlugin on_close called")

    @classmethod
    def reset_counters(cls):
        cls.message_events = []
        cls.custom_events = []
        cls.handler_ids = []
