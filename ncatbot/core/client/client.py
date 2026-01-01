"""
Bot 客户端

组合各模块，提供统一的 Bot 客户端接口。
"""

from typing import List, Type, TypeVar, TYPE_CHECKING

from ncatbot.utils import get_log
from ncatbot.utils.error import NcatBotError
from ncatbot.core.api import BotAPI
from ncatbot.core.service import ServiceManager, MessageRouter, PreUploadService

from .event_bus import EventBus
from .dispatcher import EventDispatcher
from .registry import EventRegistry
from .lifecycle import LifecycleManager

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin

T = TypeVar("T")
LOG = get_log("Client")


class BotClient(EventRegistry, LifecycleManager):
    """
    Bot 客户端
    
    架构：
    ┌─────────────────────────────────────────────────────────┐
    │                       BotClient                         │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ Services │  │ EventBus │  │ Registry │  │Lifecycle│ │
    │  │(服务层)   │ │(分发中心) │ │(注册接口)  │ │(生命周期)│ │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
    │       │             │             │             │       │
    │       └─────────────┴─────────────┴─────────────┘       │
    │                         ↓                               │
    │                   EventDispatcher                       │
    │                    (解析 & 分发)                         │
    └─────────────────────────────────────────────────────────┘
    
    事件流：
    MessageRouter → Dispatcher → EventBus → Handlers/Plugins
    
    继承：
    - EventRegistry: 提供事件注册和装饰器接口
    """

    _initialized = False

    def __init__(self, max_workers: int = 16):
        """
        初始化 Bot 客户端
        
        Args:
            max_workers: 兼容参数，已废弃
        """
        if BotClient._initialized:
            raise NcatBotError("BotClient 实例只能创建一次")
        BotClient._initialized = True

        # 核心组件
        self.event_bus = EventBus()
        
        # 初始化父类 EventRegistry
        EventRegistry.__init__(self, self.event_bus)
        
        # 服务管理器
        self.services = ServiceManager()
        
        # 注册内置服务
        self.services.register(MessageRouter)
        self.services.register(PreUploadService)
        
        # API（延迟绑定 send 回调，在服务加载后绑定）
        self.api: BotAPI = None  # 将在 _setup_api 中初始化
        
        # 事件分发器（延迟初始化）
        self.dispatcher: EventDispatcher = None
        
        # 生命周期管理器
        LifecycleManager.__init__(self, self.services, self.event_bus, self)
        
        # 注册内置处理器
        self._register_builtin_handlers()
    
    async def _setup_api(self) -> None:
        """设置 API（在服务加载后调用）"""
        router: MessageRouter = self.services.message_router
        if router:
            # 传入 service_manager 以支持预上传等服务
            self.api = BotAPI(router.send, service_manager=self.services)
            
            # 事件分发器
            self.dispatcher = EventDispatcher(self.event_bus, self.api)
            router.set_event_callback(self.dispatcher)

    def _register_builtin_handlers(self):
        """注册内置处理器"""
        self.on_startup()(lambda e: LOG.info(f"Bot {e.self_id} 启动成功"))

    # ==================== 工具方法 ====================

    def get_registered_plugins(self) -> List["BasePlugin"]:
        """获取已注册的插件列表"""
        if self.plugin_loader:
            return list(self.plugin_loader.plugins.values())
        return []

    def get_plugin(self, plugin_type: Type[T]) -> T:
        """获取指定类型的插件"""
        for plugin in self.get_registered_plugins():
            if isinstance(plugin, plugin_type):
                return plugin
        raise ValueError(f"插件 {plugin_type.__name__} 未找到")