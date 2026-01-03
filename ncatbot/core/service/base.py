"""
服务基类

所有服务必须继承此类，并实现生命周期钩子。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
from ncatbot.utils import get_log

if TYPE_CHECKING:
    from .manager import ServiceManager

LOG = get_log("Service")


class BaseService(ABC):
    """
    服务基类

    所有外部服务（如网络操作、数据库连接等）应继承此类。

    生命周期：
    1. __init__(): 实例化（轻量级初始化）
    2. on_load(): 异步加载（资源分配、连接建立等）
    3. on_close(): 异步关闭（资源释放、连接关闭等）

    属性：
        name (str): 服务名称（必须定义）
        description (str): 服务描述
        service_manager (ServiceManager): 服务管理器（可选，用于访问其他服务）
    """

    # 服务元数据（子类必须定义 name）
    name: str = None
    description: str = "未提供描述"

    def __init__(self, **config: Any):
        """
        初始化服务实例

        Args:
            **config: 服务配置参数
        """
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 name 属性")

        self.config = config
        self._loaded = False
        self.service_manager: Optional["ServiceManager"] = None

    # ------------------------------------------------------------------
    # 生命周期钩子（子类应重写）
    # ------------------------------------------------------------------

    @abstractmethod
    async def on_load(self) -> None:
        """服务加载时调用（异步）"""
        pass

    @abstractmethod
    async def on_close(self) -> None:
        """服务关闭时调用（异步）"""
        pass

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    async def _load(self) -> None:
        """内部加载方法"""
        if self._loaded:
            return

        await self.on_load()
        self._loaded = True
        LOG.debug(f"服务 {self.name} 加载成功")

    async def _close(self) -> None:
        """内部关闭方法"""
        if not self._loaded:
            return

        await self.on_close()
        self._loaded = False
        LOG.debug(f"服务 {self.name} 关闭成功")

    @property
    def is_loaded(self) -> bool:
        """服务是否已加载"""
        return self._loaded

    @property
    def event_bus(self):
        """获取事件总线"""
        if self.service_manager and self.service_manager.bot_client:
            return self.service_manager.bot_client.event_bus
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, loaded={self._loaded})>"
