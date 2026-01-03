"""基础测试插件 - 仅测试基本生命周期"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("TestPlugins")


class BasicTestPlugin(NcatBotPlugin):
    """基础测试插件 - 仅测试基本生命周期"""

    name = "basic_test_plugin"
    version = "1.0.0"

    # 生命周期追踪（类变量，在测试间共享）
    load_count: int = 0
    unload_count: int = 0
    init_called: bool = False

    def _init_(self):
        BasicTestPlugin.init_called = True
        LOG.debug("BasicTestPlugin _init_ called")

    async def on_load(self):
        BasicTestPlugin.load_count += 1
        LOG.debug(f"BasicTestPlugin on_load called (count: {self.load_count})")

    async def on_close(self):
        BasicTestPlugin.unload_count += 1
        LOG.debug(f"BasicTestPlugin on_close called (count: {self.unload_count})")

    @classmethod
    def reset_counters(cls):
        cls.load_count = 0
        cls.unload_count = 0
        cls.init_called = False
