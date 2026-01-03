"""
NcatBot 插件基类

包含完整的插件初始化逻辑、生命周期管理。
事件系统接口由 BasePlugin 提供。
"""

import inspect
from pathlib import Path
from typing import final, Any, TYPE_CHECKING

from ncatbot.plugin_system import BasePlugin
from ncatbot.plugin_system.config import config
from ncatbot.core import EventBus
from ncatbot.core.service import ServiceManager
from ncatbot.utils import get_log

from .time_task_mixin import TimeTaskMixin
from .config_mixin import ConfigMixin

if TYPE_CHECKING:
    from ncatbot.plugin_system.loader import PluginLoader

LOG = get_log("NcatBotPlugin")


class NcatBotPlugin(BasePlugin, TimeTaskMixin, ConfigMixin):
    """
    NcatBot 插件基类

    继承此类来创建功能完整的插件，包含：
    - 完整的初始化逻辑
    - 定时任务支持 (TimeTaskMixin)
    - 配置管理支持 (ConfigMixin)
    - 事件系统接口

    使用示例：
        ```python
        class MyPlugin(NcatBotPlugin):
            name = "my_plugin"
            version = "1.0.0"

            async def on_load(self):
                self.register_config("api_key", "", "API密钥")
                self.register_handler("message", self.handle_message)
        ```
    """

    def __init__(
        self,
        event_bus: EventBus,
        *,
        debug: bool = False,
        plugin_loader: "PluginLoader",
        service_manager: ServiceManager,
        **extras: Any,
    ) -> None:
        """初始化插件实例。"""
        # 注入外部依赖
        self._event_bus = event_bus
        self._loader = plugin_loader
        self._debug = debug
        for k, v in extras.items():
            setattr(self, k, v)

        # 验证必须属性
        if not getattr(self, "name", None):
            raise ValueError(f"{self.__class__.__name__} 必须定义 name 属性")
        if not getattr(self, "version", None):
            raise ValueError(f"{self.__class__.__name__} 必须定义 version 属性")

        # 初始化内部状态
        self._handlers_id = set()
        self.services = service_manager or ServiceManager()

        # 计算路径
        self.main_file = Path(inspect.getmodule(self.__class__).__file__).resolve()
        base_plugin_dir = Path(config.plugins_dir).resolve()

        try:
            relative_parts = self.main_file.relative_to(base_plugin_dir).parts
            self.source_dir = base_plugin_dir / relative_parts[0]
        except ValueError:
            self.source_dir = self.main_file.parent

        self.workspace = Path(config.plugins_data_dir) / self.name
        self._legacy_data_file = self.workspace / f"{self.name}.yaml"
        self.first_load = not self._legacy_data_file.exists()

    # ------------------------------------------------------------------
    # 生命周期方法
    # ------------------------------------------------------------------
    async def on_load(self) -> None:
        LOG.info(f"插件 {self.name} 加载成功")

    async def on_reload(self) -> None:
        LOG.info(f"插件 {self.name} 重载成功")

    async def on_close(self, *args: Any, **kw: Any) -> None:
        LOG.info(f"插件 {self.name} 卸载成功")

    # ------------------------------------------------------------------
    # 框架专用方法
    # ------------------------------------------------------------------
    @final
    async def __onload__(self) -> None:
        """由框架在加载插件时调用。"""
        self.workspace.mkdir(exist_ok=True, parents=True)

        # 加载配置（迁移逻辑由 Service 处理）
        await self.services.plugin_config.reload_plugin_config(self.name)
        self.config = await self.services.plugin_config.get_or_migrate_config(
            self.name, self._legacy_data_file
        )

        self._init_()
        await self.on_load()

        self.services.unified_registry.handle_plugin_load()

    @final
    async def __unload__(self, *a: Any, **kw: Any) -> None:
        """由框架在卸载插件时调用。"""
        # 清理定时任务
        if hasattr(self, "_time_task_jobs"):
            for name in list(self._time_task_jobs.keys()):
                self.remove_scheduled_task(name)

        try:
            self.unregister_all_handler()
            # 清理配置项注册（保留配置值）
            self.services.plugin_config.unregister_plugin_configs(self.name)
            self.services.unified_registry.handle_plugin_unload(self.name)
            self._close_(*a, **kw)
            await self.on_close(*a, **kw)
        except Exception as e:
            LOG.exception("插件 %s 卸载错误：%s: %s", self.name, type(e), e)
