"""
服务基类

所有服务必须继承此类，并实现生命周期钩子。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional, TYPE_CHECKING
from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.types import BaseEventData

LOG = get_log("Service")

# 事件发布回调类型
EventCallback = Callable[["BaseEventData"], Awaitable[None]]


class BaseService(ABC):
    """
    服务基类

    生命周期：
    1. __init__(): 实例化（轻量级初始化）
    2. on_load(): 异步加载（资源分配、线程启动等）
    3. on_close(): 异步关闭（资源释放、线程停止等）

    属性：
        name (str): 服务名称（必须定义）
        description (str): 服务描述
        dependencies (list): 依赖的其他服务名称列表
        emit_event (EventCallback | None): 事件发布回调，由 ServiceManager 在 load 时注入
    """

    name: str = None
    description: str = "未提供描述"
    dependencies: list = []

    def __init__(self, **config: Any):
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} 必须定义 name 属性")

        self.config = config
        self._loaded = False
        self.emit_event: Optional[EventCallback] = None

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
        self.emit_event = None
        LOG.debug(f"服务 {self.name} 关闭成功")

    @property
    def is_loaded(self) -> bool:
        """服务是否已加载"""
        return self._loaded

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, loaded={self._loaded})>"
