"""
服务管理器

负责服务的注册、加载、卸载。
"""

from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING
from ncatbot.utils import get_log
from .base import BaseService

if TYPE_CHECKING:
    from .builtin import (
        MessageRouter,
        PreUploadService,
        PluginConfigService,
        RBACService,
        UnifiedRegistryService,
        FileWatcherService,
        PluginDataService,
    )
    from ncatbot.core.client import BotClient

LOG = get_log("ServiceManager")


class ServiceManager:
    """
    服务管理器

    管理所有服务的生命周期，提供服务的注册、加载、卸载、获取等功能。

    内置服务（支持 IDE 类型提示）：
        - message_router: MessageRouter - 消息路由服务
        - preupload: PreUploadService - 消息和文件预上传服务
        - plugin_config: PluginConfigService - 插件配置服务

    使用示例：
        ```python
        manager = ServiceManager()

        # 注册内置服务
        manager.register(MessageRouter)
        manager.register(PreUploadService)

        # 加载并使用
        await manager.load_all()

        # 类型安全的访问（IDE 提示支持）
        preupload = manager.preupload  # 类型: PreUploadService
        ```
    """

    _debug_mode: bool = False
    _test_mode: bool = False

    def __init__(self):
        """初始化服务管理器"""
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._bot_client: Optional["BotClient"] = None

    def set_debug_mode(self, enable: bool = True) -> None:
        """设置调试模式"""
        self._debug_mode = enable

    def set_test_mode(self, enable: bool = True) -> None:
        """设置测试模式"""
        self._test_mode = enable

    def set_bot_client(self, bot_client: "BotClient") -> None:
        """设置 BotClient 引用"""
        self._bot_client = bot_client

    @property
    def bot_client(self) -> "BotClient":
        """获取 BotClient"""
        return self._bot_client  # type: ignore

    # -------------------------------------------------------------------------
    # region 内置服务属性（支持 IDE 类型提示）
    # -------------------------------------------------------------------------

    @property
    def message_router(self) -> "MessageRouter":
        """消息路由服务"""
        return self._services.get("message_router")  # type: ignore

    @property
    def preupload(self) -> "PreUploadService":
        """消息和文件预上传服务"""
        return self._services.get("preupload")  # type: ignore

    @property
    def plugin_config(self) -> "PluginConfigService":
        """插件配置服务"""
        return self._services.get("plugin_config")  # type: ignore

    @property
    def rbac(self) -> "RBACService":
        """RBAC 服务"""
        return self._services.get("rbac")  # type: ignore

    @property
    def unified_registry(self) -> "UnifiedRegistryService":
        """统一注册服务"""
        return self._services.get("unified_registry")  # type: ignore

    @property
    def file_watcher(self) -> "FileWatcherService":
        """文件监视服务"""
        return self._services.get("file_watcher")  # type: ignore

    @property
    def plugin_data(self) -> "PluginDataService":
        """插件数据服务"""
        return self._services.get("plugin_data")  # type: ignore

    # -------------------------------------------------------------------------
    # region 服务管理方法
    # -------------------------------------------------------------------------

    def register(self, service_class: Type[BaseService], **config: Any) -> None:
        """注册服务类"""
        temp = service_class(**config)
        name = temp.name

        self._service_classes[name] = service_class
        self._service_configs[name] = config

    async def load(self, service_name: str) -> BaseService:
        """加载服务"""
        if service_name in self._services:
            return self._services[service_name]

        if service_name not in self._service_classes:
            raise KeyError(f"服务 {service_name} 未注册")

        service = self._service_classes[service_name](
            **self._service_configs[service_name]
        )
        # 注入 ServiceManager 到服务中
        service.service_manager = self
        await service._load()
        self._services[service_name] = service
        return service

    async def unload(self, service_name: str) -> None:
        """卸载服务"""
        if service_name not in self._services:
            return

        await self._services[service_name]._close()
        del self._services[service_name]

    async def load_all(self) -> None:
        """加载所有已注册的服务"""
        for name in self._service_classes:
            if name not in self._services:
                await self.load(name)

    async def close_all(self) -> None:
        """关闭所有已加载的服务"""
        for name in list(self._services.keys()):
            await self.unload(name)

    def get(self, service_name: str) -> Optional[BaseService]:
        """获取服务实例"""
        return self._services.get(service_name)

    def has(self, service_name: str) -> bool:
        """检查服务是否已加载"""
        return service_name in self._services

    def list_services(self) -> List[str]:
        """列出所有已加载的服务名称"""
        return list(self._services.keys())
