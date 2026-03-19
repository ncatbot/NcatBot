import asyncio
from collections.abc import AsyncIterator
from typing import cast


class EventBroadcaster[T]:
    """Broadcast each published item to every active async subscriber."""

    def __init__(self) -> None:
        self._closed = False
        self._closed_sentinel = object()
        self._subscribers: list[asyncio.Queue[T | object]] = []

    def subscribe(self) -> AsyncIterator[T]:
        """Create a new async iterator over future published items."""
        queue: asyncio.Queue[T | object] = asyncio.Queue()
        if self._closed:
            queue.put_nowait(self._closed_sentinel)
        else:
            self._subscribers.append(queue)

        async def iterator() -> AsyncIterator[T]:
            try:
                while True:
                    item = await queue.get()
                    if item is self._closed_sentinel:
                        return
                    yield cast(T, item)
            finally:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)

        return iterator()

    def publish(self, item: T) -> None:
        for subscriber in tuple(self._subscribers):
            subscriber.put_nowait(item)

    def close(self) -> None:
        """Finish all current and future subscriptions for the current run."""
        if self._closed:
            return

        self._closed = True
        for subscriber in tuple(self._subscribers):
            subscriber.put_nowait(self._closed_sentinel)
        self._subscribers.clear()

    def reset(self) -> None:
        """Reopen the broadcaster for the next app run."""
        self._closed = False
