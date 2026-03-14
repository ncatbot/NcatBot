from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from types import TracebackType


class BaseAdapter(ABC):
    """
    适配器基类
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        pass

    @property
    @abstractmethod
    def adapter_version(self) -> str:
        pass

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        pass

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[object]:
        pass
