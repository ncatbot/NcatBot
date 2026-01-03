"""生命周期插件 - 测试 on_load/on_close"""

from typing import List

from ncatbot.plugin_system import NcatBotPlugin


class LifecyclePlugin(NcatBotPlugin):
    """生命周期插件 - 测试 on_load/on_close"""

    name = "lifecycle_plugin"
    version = "1.0.0"

    lifecycle_events: List[str] = []

    async def on_load(self):
        LifecyclePlugin.lifecycle_events.append("loaded")

    async def on_close(self):
        LifecyclePlugin.lifecycle_events.append("closed")
