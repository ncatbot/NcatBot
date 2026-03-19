import asyncio
from collections.abc import AsyncIterator, Coroutine
from types import TracebackType
from typing import Any, Self, cast

import pytest

from ncatbot import NcatBotApp, WaitEventCancelledError
from ncatbot.events import AppStarted, AppStarting, AppStopping


def run_async[T](coro: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coro)


async def collect_events(app: NcatBotApp, sink: list[object]) -> None:
    async for event in app.events():
        sink.append(event)


class DummyEvent:
    pass


class ChildDummyEvent(DummyEvent):
    pass


class IdleAdapter:
    @property
    def platform_name(self) -> str:
        return "dummy"

    @property
    def adapter_name(self) -> str:
        return "dummy.Adapter"

    @property
    def adapter_version(self) -> str:
        return "0"

    @property
    def base_event_type(self) -> type[DummyEvent]:
        return DummyEvent

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
                await asyncio.sleep(3600)
                yield DummyEvent()

        return iterator()


class QueueAdapter:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[object] = asyncio.Queue()

    @property
    def platform_name(self) -> str:
        return "dummy"

    @property
    def adapter_name(self) -> str:
        return "dummy.QueueAdapter"

    @property
    def adapter_version(self) -> str:
        return "0"

    @property
    def base_event_type(self) -> type[DummyEvent]:
        return DummyEvent

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
                yield await self.queue.get()

        return iterator()


def test_on_event_rejects_sync_handler_without_explicit_event_type() -> None:
    app = NcatBotApp()

    def sync_handler(event: DummyEvent) -> None:
        return None

    with pytest.raises(TypeError, match="async def"):
        app.on_event(cast(Any, sync_handler))


def test_on_event_rejects_sync_handler_with_explicit_event_type() -> None:
    app = NcatBotApp()

    def sync_handler(event: DummyEvent) -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="async def"):
        decorator(cast(Any, sync_handler))


def test_on_event_rejects_explicit_handler_without_event_param() -> None:
    app = NcatBotApp()

    async def bad_handler() -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="至少接收一个事件参数"):
        decorator(cast(Any, bad_handler))


def test_on_event_rejects_explicit_handler_with_extra_required_param() -> None:
    app = NcatBotApp()

    async def bad_handler(event: DummyEvent, extra: str) -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="单个事件参数"):
        decorator(cast(Any, bad_handler))


def test_on_event_accepts_bound_async_method() -> None:
    app = NcatBotApp()

    class HandlerOwner:
        async def handle(self, event: DummyEvent) -> None:
            return None

    handler = HandlerOwner()
    app.on_event(handler.handle)

    assert app.handlers[DummyEvent] == [handler.handle]


def test_handler_registered_for_multiple_matching_types_runs_once() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        adapter = QueueAdapter()
        app.add_adapter(adapter)
        call_count = 0

        @app.on_event(DummyEvent | ChildDummyEvent)
        async def handle(event: DummyEvent) -> None:
            nonlocal call_count
            call_count += 1
            app.stop()

        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        await adapter.queue.put(ChildDummyEvent())
        await start_task

        assert call_count == 1
        assert app.handlers[DummyEvent] == [handle]
        assert app.handlers[ChildDummyEvent] == [handle]

    run_async(scenario())


def test_add_adapter_rejects_duplicate_instance() -> None:
    app = NcatBotApp()
    adapter = IdleAdapter()

    app.add_adapter(adapter)

    with pytest.raises(ValueError, match="重复添加"):
        app.add_adapter(adapter)


def test_wait_event_is_cancelled_when_app_stops() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        app.add_adapter(IdleAdapter())

        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        waiter = asyncio.create_task(app.wait_event(lambda _: False))
        await asyncio.sleep(0.05)

        app.stop()
        await start_task

        with pytest.raises(WaitEventCancelledError, match="应用正在停止"):
            await waiter

    run_async(scenario())


def test_events_subscriber_started_before_run_receives_events_and_closes() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        adapter = QueueAdapter()
        app.add_adapter(adapter)

        seen: list[object] = []
        consumer = asyncio.create_task(collect_events(app, seen))
        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        event = DummyEvent()
        await adapter.queue.put(event)
        await asyncio.sleep(0.05)

        app.stop()
        await start_task
        await consumer

        assert any(item is event for item in seen)

    run_async(scenario())


def test_app_async_iterator_receives_events_and_closes() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        adapter = QueueAdapter()
        app.add_adapter(adapter)

        seen: list[object] = []

        async def consume() -> None:
            async for event in app:
                seen.append(event)

        consumer = asyncio.create_task(consume())
        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        event = DummyEvent()
        await adapter.queue.put(event)
        await asyncio.sleep(0.05)

        app.stop()
        await start_task
        await consumer

        assert any(item is event for item in seen)

    run_async(scenario())


def test_events_after_stop_are_immediately_closed() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        app.add_adapter(IdleAdapter())

        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        app.stop()
        await start_task

        seen = [event async for event in app.events()]
        assert seen == []

    run_async(scenario())


def test_app_can_restart_after_stop() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        adapter = QueueAdapter()
        app.add_adapter(adapter)

        async def run_once() -> object:
            seen: list[object] = []
            start_task = asyncio.create_task(app.start())
            await asyncio.sleep(0.05)
            consumer = asyncio.create_task(collect_events(app, seen))

            event = DummyEvent()
            await adapter.queue.put(event)
            await asyncio.sleep(0.05)

            app.stop()
            await start_task
            await consumer

            assert any(item is event for item in seen)
            return event

        first_event = await run_once()
        second_event = await run_once()

        assert first_event is not second_event

    run_async(scenario())


def test_add_adapter_while_running_starts_it_immediately() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        seen: list[object] = []
        consumer = asyncio.create_task(collect_events(app, seen))
        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        adapter = QueueAdapter()
        app.add_adapter(adapter)
        await asyncio.sleep(0.05)

        event = DummyEvent()
        await adapter.queue.put(event)
        await asyncio.sleep(0.05)

        app.stop()
        await start_task
        await consumer

        assert any(item is event for item in seen)

    run_async(scenario())


def test_framework_lifecycle_events_are_published_on_event_stream() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        seen: list[object] = []

        consumer = asyncio.create_task(collect_events(app, seen))
        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        app.stop()
        await start_task
        await consumer

        event_types = [type(event) for event in seen]
        assert AppStarting in event_types
        assert AppStarted in event_types
        assert AppStopping in event_types
        assert event_types.index(AppStarting) < event_types.index(AppStarted)
        assert event_types.index(AppStarted) < event_types.index(AppStopping)

    run_async(scenario())
