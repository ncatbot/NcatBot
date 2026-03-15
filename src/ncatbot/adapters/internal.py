from asyncio import Queue
from collections.abc import AsyncIterator
from importlib.metadata import PackageNotFoundError, version
from types import TracebackType
from typing import Self

from ..events import FrameworkEvent
from .base import BaseAdapter


def _package_version() -> str:
    try:
        return version("ncatbot")
    except PackageNotFoundError:
        return "0.0.0"


class InternalEventAdapter(BaseAdapter):
    def __init__(self) -> None:
        self._queue: Queue[object] = Queue()
        self._adapter_version = _package_version()

    @property
    def platform_name(self) -> str:
        return "internal"

    @property
    def adapter_name(self) -> str:
        return "Ncatbot.InternalEventAdapter"

    @property
    def adapter_version(self) -> str:
        return self._adapter_version

    @property
    def base_event_type(self) -> type[FrameworkEvent]:
        return FrameworkEvent

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    def __aiter__(self) -> AsyncIterator[object]:
        async def iterator() -> AsyncIterator[object]:
            while True:
                yield await self._queue.get()

        return iterator()

    def publish_nowait(self, event: object) -> None:
        self._queue.put_nowait(event)
