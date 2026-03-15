import asyncio
import unittest
from collections.abc import AsyncIterator, Iterable
from types import TracebackType

from ncatbot import NcatBotApp
from ncatbot.adapters import BaseAdapter, InternalEventAdapter, NapCatAdapter, napcat
from ncatbot.events import (
    AdapterAdded,
    AdapterRestartScheduled,
    AdapterRunFailed,
    AppEvent,
    AppStarted,
    AppStarting,
    EventReceived,
    HandlerCompleted,
    HandlerFailed,
    HandlerScheduled,
    HandlersResolved,
    WaitCancelled,
    WaitMatched,
    WaitRegistered,
    WaitTimedOut,
)


class SmokeEvent:
    def __init__(self, value: str):
        self.value = value


class OtherSmokeEvent:
    def __init__(self, value: str):
        self.value = value


class BaseInheritedSmokeEvent:
    def __init__(self, value: str):
        self.value = value


class DerivedInheritedSmokeEvent(BaseInheritedSmokeEvent):
    pass


class FakeAdapter(BaseAdapter):
    def __init__(
        self,
        events: Iterable[object],
        *,
        delay: float = 0.0,
        entered_event: asyncio.Event | None = None,
    ) -> None:
        self._events = list(events)
        self._delay = delay
        self._entered_event = entered_event

    @property
    def platform_name(self) -> str:
        return "fake"

    @property
    def adapter_name(self) -> str:
        return "tests.FakeAdapter"

    @property
    def adapter_version(self) -> str:
        return "0.0"

    @property
    def base_event_type(self) -> type[object]:
        return object

    async def __aenter__(self) -> "FakeAdapter":
        if self._entered_event is not None:
            self._entered_event.set()
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
            for event in self._events:
                if self._delay:
                    await asyncio.sleep(self._delay)
                yield event

        return iterator()


class FlakyAdapter(BaseAdapter):
    def __init__(self) -> None:
        self.run_count = 0

    @property
    def platform_name(self) -> str:
        return "fake"

    @property
    def adapter_name(self) -> str:
        return "tests.FlakyAdapter"

    @property
    def adapter_version(self) -> str:
        return "0.0"

    @property
    def base_event_type(self) -> type[SmokeEvent]:
        return SmokeEvent

    async def __aenter__(self) -> "FlakyAdapter":
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
            self.run_count += 1
            if self.run_count == 1:
                raise RuntimeError("boom")
            yield SmokeEvent("recovered")

        return iterator()


class IdleAdapter(BaseAdapter):
    @property
    def platform_name(self) -> str:
        return "fake"

    @property
    def adapter_name(self) -> str:
        return "tests.IdleAdapter"

    @property
    def adapter_version(self) -> str:
        return "0.0"

    @property
    def base_event_type(self) -> type[object]:
        return object

    async def __aenter__(self) -> "IdleAdapter":
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
                yield object()

        return iterator()


class SmokeTests(unittest.IsolatedAsyncioTestCase):
    def test_public_exports_are_available(self) -> None:
        adapter = NapCatAdapter()
        self.assertTrue(issubclass(NapCatAdapter, BaseAdapter))
        self.assertTrue(issubclass(InternalEventAdapter, BaseAdapter))
        self.assertEqual(NapCatAdapter.platform_name.fget(None), "qq")
        self.assertIsNotNone(getattr(napcat, "NapCatClient", None))
        self.assertIs(adapter.base_event_type, napcat.NapCatEvent)
        self.assertTrue(issubclass(AppStarting, AppEvent))

    def test_internal_adapter_is_registered_by_default(self) -> None:
        app = NcatBotApp()
        self.assertIsInstance(app.adapters[0], InternalEventAdapter)

    async def test_dispatches_events_to_union_handler(self) -> None:
        app = NcatBotApp()
        seen: list[str] = []
        handled = asyncio.Event()

        @app.on_event
        async def handle(event: SmokeEvent | OtherSmokeEvent) -> None:
            seen.append(event.value)
            if len(seen) == 2:
                handled.set()
                app.stop()

        app.add_adapter(
            FakeAdapter(
                [SmokeEvent("first"), OtherSmokeEvent("second")],
                delay=0.01,
            )
        )

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertEqual(seen, ["first", "second"])

    async def test_wait_event_receives_published_events(self) -> None:
        app = NcatBotApp()
        entered = asyncio.Event()
        app.add_adapter(
            FakeAdapter(
                [SmokeEvent("ready")],
                delay=0.05,
                entered_event=entered,
            )
        )

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(entered.wait(), timeout=1)

        event = await app.wait_event(
            lambda item: isinstance(item, SmokeEvent),
            timeout=1,
        )
        self.assertIsInstance(event, SmokeEvent)
        self.assertEqual(event.value, "ready")

        app.stop()
        await asyncio.wait_for(task, timeout=1)

    async def test_wait_event_emits_registered_and_matched_events(self) -> None:
        app = NcatBotApp()
        entered = asyncio.Event()
        seen_registered: WaitRegistered | None = None
        seen_matched: WaitMatched | None = None
        handled = asyncio.Event()
        app.add_adapter(
            FakeAdapter(
                [SmokeEvent("ready")],
                delay=0.05,
                entered_event=entered,
            )
        )

        @app.on_event
        async def handle_wait_events(
            event: WaitRegistered | WaitMatched,
        ) -> None:
            nonlocal seen_registered, seen_matched
            if isinstance(event, WaitRegistered):
                seen_registered = event
            else:
                seen_matched = event

            if seen_registered is not None and seen_matched is not None:
                handled.set()

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(entered.wait(), timeout=1)

        matched = await app.wait_event(
            lambda item: isinstance(item, SmokeEvent),
            timeout=1,
        )

        await asyncio.wait_for(handled.wait(), timeout=1)
        app.stop()
        await asyncio.wait_for(task, timeout=1)

        self.assertIsInstance(matched, SmokeEvent)
        self.assertIsNotNone(seen_registered)
        self.assertIsNotNone(seen_matched)
        self.assertEqual(seen_registered.waiter_id, seen_matched.waiter_id)
        self.assertEqual(
            seen_matched.event_type,
            f"{SmokeEvent.__module__}.{SmokeEvent.__qualname__}",
        )
        self.assertFalse(seen_matched.is_framework_event)

    async def test_wait_event_emits_timeout_event(self) -> None:
        app = NcatBotApp()
        seen_registered: WaitRegistered | None = None
        seen_timed_out: WaitTimedOut | None = None
        handled = asyncio.Event()
        app.add_adapter(IdleAdapter())

        @app.on_event
        async def handle_wait_events(
            event: WaitRegistered | WaitTimedOut,
        ) -> None:
            nonlocal seen_registered, seen_timed_out
            if isinstance(event, WaitRegistered):
                seen_registered = event
            else:
                seen_timed_out = event

            if seen_registered is not None and seen_timed_out is not None:
                handled.set()

        task = asyncio.create_task(app.start())

        with self.assertRaises(TimeoutError):
            await app.wait_event(
                lambda item: isinstance(item, SmokeEvent),
                timeout=0.01,
            )

        await asyncio.wait_for(handled.wait(), timeout=1)
        app.stop()
        await asyncio.wait_for(task, timeout=1)

        self.assertIsNotNone(seen_registered)
        self.assertIsNotNone(seen_timed_out)
        self.assertEqual(seen_registered.waiter_id, seen_timed_out.waiter_id)
        self.assertEqual(seen_timed_out.timeout, 0.01)

    async def test_wait_event_emits_cancelled_event(self) -> None:
        app = NcatBotApp()
        seen_registered: WaitRegistered | None = None
        seen_cancelled: WaitCancelled | None = None
        registered = asyncio.Event()
        handled = asyncio.Event()
        app.add_adapter(IdleAdapter())

        @app.on_event
        async def handle_wait_events(
            event: WaitRegistered | WaitCancelled,
        ) -> None:
            nonlocal seen_registered, seen_cancelled
            if isinstance(event, WaitRegistered):
                seen_registered = event
                registered.set()
            else:
                seen_cancelled = event
                handled.set()

        task = asyncio.create_task(app.start())
        wait_task = asyncio.create_task(
            app.wait_event(
                lambda item: isinstance(item, SmokeEvent),
                timeout=1,
            )
        )

        await asyncio.wait_for(registered.wait(), timeout=1)
        wait_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await wait_task

        await asyncio.wait_for(handled.wait(), timeout=1)
        app.stop()
        await asyncio.wait_for(task, timeout=1)

        self.assertIsNotNone(seen_registered)
        self.assertIsNotNone(seen_cancelled)
        self.assertEqual(seen_registered.waiter_id, seen_cancelled.waiter_id)
        self.assertEqual(seen_cancelled.timeout, 1)

    async def test_can_add_adapter_while_running(self) -> None:
        app = NcatBotApp()
        seen: list[str] = []
        entered = asyncio.Event()
        handled = asyncio.Event()

        @app.on_event
        async def handle(event: SmokeEvent) -> None:
            seen.append(event.value)
            if len(seen) == 2:
                handled.set()
                app.stop()

        app.add_adapter(
            FakeAdapter(
                [SmokeEvent("boot")],
                delay=0.01,
                entered_event=entered,
            )
        )

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(entered.wait(), timeout=1)
        app.add_adapter(FakeAdapter([SmokeEvent("hot-add")], delay=0.01))

        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertEqual(seen, ["boot", "hot-add"])

    async def test_deduplicates_union_handler_for_inherited_event(self) -> None:
        app = NcatBotApp()
        calls = 0
        handled = asyncio.Event()

        @app.on_event
        async def handle(
            event: BaseInheritedSmokeEvent | DerivedInheritedSmokeEvent,
        ) -> None:
            nonlocal calls
            calls += 1
            handled.set()
            app.stop()

        app.add_adapter(FakeAdapter([DerivedInheritedSmokeEvent("payload")], delay=0.01))

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertEqual(calls, 1)

    async def test_emits_event_and_handler_lifecycle_events(self) -> None:
        app = NcatBotApp()
        received: EventReceived | None = None
        resolved: HandlersResolved | None = None
        scheduled: list[HandlerScheduled] = []
        completed: HandlerCompleted | None = None
        failed: HandlerFailed | None = None
        handled = asyncio.Event()

        @app.on_event
        async def handle_success(event: SmokeEvent) -> None:
            await asyncio.sleep(0)

        @app.on_event
        async def handle_failure(event: SmokeEvent) -> None:
            raise RuntimeError("handler boom")

        @app.on_event
        async def observe_framework(
            event: (
                EventReceived
                | HandlersResolved
                | HandlerScheduled
                | HandlerCompleted
                | HandlerFailed
            ),
        ) -> None:
            nonlocal received, resolved, completed, failed
            if isinstance(event, EventReceived):
                received = event
            elif isinstance(event, HandlersResolved):
                resolved = event
            elif isinstance(event, HandlerScheduled):
                scheduled.append(event)
            elif isinstance(event, HandlerCompleted):
                completed = event
            else:
                failed = event

            if (
                received is not None
                and resolved is not None
                and len(scheduled) == 2
                and completed is not None
                and failed is not None
            ):
                handled.set()
                app.stop()

        app.add_adapter(FakeAdapter([SmokeEvent("payload")], delay=0.01))

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        event_type = f"{SmokeEvent.__module__}.{SmokeEvent.__qualname__}"
        self.assertIsNotNone(received)
        self.assertEqual(received.event_type, event_type)
        self.assertEqual(received.adapter_name, "tests.FakeAdapter")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.event_type, event_type)
        self.assertEqual(resolved.handler_count, 2)
        self.assertEqual(len(scheduled), 2)
        self.assertTrue(
            any(item.handler_name.endswith("handle_success") for item in scheduled)
        )
        self.assertTrue(
            any(item.handler_name.endswith("handle_failure") for item in scheduled)
        )
        self.assertIsNotNone(completed)
        self.assertTrue(completed.handler_name.endswith("handle_success"))
        self.assertIsNotNone(failed)
        self.assertTrue(failed.handler_name.endswith("handle_failure"))
        self.assertEqual(failed.event_type, event_type)

    async def test_framework_events_are_dispatched(self) -> None:
        app = NcatBotApp()
        seen: list[str] = []
        observed: list[str] = []
        handled = asyncio.Event()

        @app.on_event
        async def handle(event: AdapterAdded | AppStarting | AppStarted) -> None:
            seen.append(type(event).__name__)
            if isinstance(event, AppStarted):
                handled.set()
                app.stop()

        @app.on_event
        async def handle_observed(
            event: EventReceived | HandlersResolved | HandlerScheduled,
        ) -> None:
            observed.append(type(event).__name__)

        app.add_adapter(IdleAdapter())

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertIn("AdapterAdded", seen)
        self.assertIn("AppStarting", seen)
        self.assertIn("AppStarted", seen)
        self.assertEqual(observed, [])

    async def test_restarts_adapter_after_failure(self) -> None:
        app = NcatBotApp(adapter_restart_delay=0.01)
        adapter = FlakyAdapter()
        handled = asyncio.Event()
        seen: list[str] = []

        @app.on_event
        async def handle(event: SmokeEvent) -> None:
            seen.append(event.value)
            handled.set()
            app.stop()

        app.add_adapter(adapter)

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertEqual(seen, ["recovered"])
        self.assertEqual(adapter.run_count, 2)

    async def test_emits_framework_restart_events(self) -> None:
        app = NcatBotApp(adapter_restart_delay=0.01)
        adapter = FlakyAdapter()
        seen_failed: AdapterRunFailed | None = None
        seen_restart: AdapterRestartScheduled | None = None
        handled = asyncio.Event()

        @app.on_event
        async def handle(
            event: AdapterRunFailed | AdapterRestartScheduled,
        ) -> None:
            nonlocal seen_failed, seen_restart
            if isinstance(event, AdapterRunFailed):
                seen_failed = event
            else:
                seen_restart = event

            if seen_failed is not None and seen_restart is not None:
                handled.set()
                app.stop()

        app.add_adapter(adapter)

        task = asyncio.create_task(app.start())
        await asyncio.wait_for(handled.wait(), timeout=1)
        await asyncio.wait_for(task, timeout=1)

        self.assertIsNotNone(seen_failed)
        self.assertIsNotNone(seen_restart)
        self.assertEqual(seen_failed.adapter_name, adapter.adapter_name)
        self.assertEqual(seen_failed.attempt, 1)
        self.assertEqual(seen_restart.delay, 0.01)

    async def test_waits_for_running_handlers_during_shutdown(self) -> None:
        app = NcatBotApp()
        handler_completed = False
        handler_cancelled = False

        @app.on_event
        async def handle_slow(event: SmokeEvent) -> None:
            nonlocal handler_completed, handler_cancelled
            try:
                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                handler_cancelled = True
                raise
            handler_completed = True

        @app.on_event
        async def stop_after_first_event(event: SmokeEvent) -> None:
            app.stop()

        app.add_adapter(FakeAdapter([SmokeEvent("payload")], delay=0.01))

        await asyncio.wait_for(app.start(), timeout=1)

        self.assertTrue(handler_completed)
        self.assertFalse(handler_cancelled)
