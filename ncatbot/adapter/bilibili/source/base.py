"""数据源抽象基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable


class BaseSource(ABC):
    """单一数据源抽象 — 每个实例对应一路事件流。

    回调签名: ``async callback(source_type: str, raw_data: dict) -> None``
    """

    source_type: str  # "live" / "session" / "comment"
    source_id: str  # room_id / "session" / resource_id

    def __init__(
        self,
        callback: Callable[[str, dict], Awaitable[None]],
    ) -> None:
        self._callback = callback
        self._running = False

    @abstractmethod
    async def start(self) -> None:
        """启动数据源（非阻塞，内部自行管理 task）"""

    @abstractmethod
    async def stop(self) -> None:
        """停止数据源，释放资源"""

    @property
    def running(self) -> bool:
        return self._running

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.source_type}:{self.source_id}, running={self._running})"
