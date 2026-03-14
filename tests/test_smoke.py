import asyncio
import unittest
from collections.abc import AsyncIterator, Iterable
from types import TracebackType

from ncatbot import NcatBotApp
from ncatbot.adapters import BaseAdapter, NapCatAdapter, napcat


class SmokeEvent:
    def __init__(self, value: str):
        self.value = value


class OtherSmokeEvent:
    def __init__(self, value: str):
        self.value = value


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


class SmokeTests(unittest.IsolatedAsyncioTestCase):
    def test_public_exports_are_available(self) -> None:
        self.assertTrue(issubclass(NapCatAdapter, BaseAdapter))
        self.assertEqual(NapCatAdapter.platform_name.fget(None), "qq")
        self.assertIsNotNone(getattr(napcat, "NapCatClient", None))

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
