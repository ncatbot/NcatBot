"""热重载测试插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core import MessageEvent, NcatBotEvent
from ncatbot.utils import get_log

LOG = get_log("ReloadTestPlugin")

# 命令响应内容（用于测试热重载后命令输出变化）
COMMAND_RESPONSE: str = "original_response"

# 事件处理器调用计数
HANDLER_CALL_COUNT: int = 0


def reset_counters():
    """重置模块级计数器"""
    global HANDLER_CALL_COUNT
    HANDLER_CALL_COUNT = 0
    ReloadTestPlugin.load_count = 0
    ReloadTestPlugin.unload_count = 0


class ReloadTestPlugin(NcatBotPlugin):
    """热重载测试插件"""

    name = "reload_test_plugin"
    version = "1.0.0"

    # 生命周期追踪（类变量）
    load_count: int = 0
    unload_count: int = 0

    # 用于验证重载的标记值
    MARKER_VALUE: str = "original"

    # 模块级变量引用
    HANDLER_CALL_COUNT = 0

    async def on_load(self):
        ReloadTestPlugin.load_count += 1
        LOG.info(
            f"ReloadTestPlugin on_load (count: {self.load_count}, marker: {self.MARKER_VALUE})"
        )

        # 注册配置项
        self.services.plugin_config.register_config(
            self.name, "reload_count", 0, "重载次数计数", value_type=int
        )
        self.services.plugin_config.register_config(
            self.name, "test_string", "default", "测试字符串", value_type=str
        )

        # 注册事件处理器
        self.register_handler("ncatbot.hot_reload_test_event", self._on_test_event)

    async def on_close(self):
        ReloadTestPlugin.unload_count += 1
        LOG.info(f"ReloadTestPlugin on_close (count: {self.unload_count})")

    @command_registry.command(
        name="reload_test_cmd", aliases=["hrt"], description="热重载测试命令"
    )
    async def test_command(self, event: MessageEvent):
        """测试命令，返回当前的响应内容"""
        await event.reply(COMMAND_RESPONSE)

    @command_registry.command(
        name="hot_reload_config", aliases=["hrc"], description="热重载配置命令"
    )
    async def config_command(self, event: MessageEvent):
        """配置命令，返回当前配置值"""
        count = self.config.get("reload_count", 0)
        test_str = self.config.get("test_string", "default")
        await event.reply(f"reload_count={count}, test_string={test_str}")

    async def _on_test_event(self, event: NcatBotEvent):
        """测试事件处理器"""
        global HANDLER_CALL_COUNT
        HANDLER_CALL_COUNT += 1
        ReloadTestPlugin.HANDLER_CALL_COUNT = HANDLER_CALL_COUNT
        LOG.info(f"收到测试事件: {event.data}")

    @classmethod
    def reset_counters(cls):
        global HANDLER_CALL_COUNT
        HANDLER_CALL_COUNT = 0
        cls.load_count = 0
        cls.unload_count = 0
        cls.HANDLER_CALL_COUNT = 0

    @classmethod
    def get_marker(cls) -> str:
        return cls.MARKER_VALUE


# 导出模块级变量，方便测试访问
plugin = ReloadTestPlugin
