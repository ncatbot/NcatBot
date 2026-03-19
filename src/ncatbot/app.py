import asyncio
import inspect
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from itertools import count
from time import perf_counter
from types import UnionType
from typing import Any, overload

from ._adapter_runtime import AdapterRuntime, adapter_event_kwargs
from ._app_support import callable_name, event_type_name
from ._event_broadcaster import EventBroadcaster
from ._handler_registry import EventHandler, HandlerRegistry, HandlerType
from .adapters import BaseAdapter
from .events import (
    AppStarted,
    AppStarting,
    AppStopping,
    EventReceived,
    FrameworkEvent,
    HandlerCompleted,
    HandlerFailed,
    HandlerScheduled,
    HandlersResolved,
    WaitCancelled,
    WaitMatched,
    WaitRegistered,
    WaitTimedOut,
)

logger = logging.getLogger(__name__)


class WaitEventCancelledError(asyncio.CancelledError):
    """Raised when wait_event() is interrupted because the app is stopping."""


class NcatBotApp:
    """Public facade that wires adapters, handlers, waits, and observability together."""

    def __init__(self, adapter_restart_delay: float = 5.0):
        # Keep the public API on this class while delegating the noisy internals
        # to small private components that each own one concern.
        self._handler_registry = HandlerRegistry()
        self.handlers = self._handler_registry.handlers
        self._event_broadcaster = EventBroadcaster[object]()
        self._running = False
        self._stop_event: asyncio.Event | None = None
        self._handler_tasks: set[asyncio.Task[None]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._waiter_ids = count(1)
        self._adapter_runtime = AdapterRuntime(
            adapter_restart_delay=adapter_restart_delay,
            dispatch_event=self._dispatch_event,
            emit_framework_event=self._emit_framework_event,
            is_running=lambda: self._running,
            is_stop_requested=self._is_stop_requested,
            logger=logger,
        )
        self.adapters = self._adapter_runtime.adapters

    def events(self) -> AsyncIterator[object]:
        """返回广播所有 adapter 事件的异步迭代器。"""
        return self._event_broadcaster.subscribe()

    @property
    def is_running(self) -> bool:
        return self._running

    def _is_framework_event(self, event_obj: object) -> bool:
        return isinstance(event_obj, FrameworkEvent)

    def _enqueue_framework_event(self, event: FrameworkEvent):
        self._adapter_runtime.internal_adapter.publish_nowait(event)

    def _emit_framework_event(self, event: FrameworkEvent):
        if self._loop is None:
            self._enqueue_framework_event(event)
            return

        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop is self._loop:
            self._enqueue_framework_event(event)
        else:
            self._loop.call_soon_threadsafe(self._enqueue_framework_event, event)

    def _is_stop_requested(self) -> bool:
        return self._stop_event is not None and self._stop_event.is_set()

    def _should_observe_event(self, event_obj: object) -> bool:
        return not self._is_framework_event(event_obj)

    def add_adapter(self, adapter: BaseAdapter):
        self._adapter_runtime.add_adapter(
            adapter,
            running=self._running,
            loop=self._loop,
        )

    def _spawn_handler_task(
        self,
        handler: HandlerType,
        event_obj: object,
        *,
        observe: bool,
    ) -> None:
        task = asyncio.create_task(self._run_handler(handler, event_obj, observe=observe))
        self._handler_tasks.add(task)
        task.add_done_callback(self._handler_tasks.discard)

    async def _wait_for_handler_tasks(self) -> None:
        while self._handler_tasks:
            tasks = tuple(self._handler_tasks)
            await asyncio.gather(*tasks, return_exceptions=True)

    def _prepare_runtime(self) -> None:
        """Initialize per-run state before adapters start producing events."""
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        self._handler_tasks = set()
        self._event_broadcaster.reset()
        self._adapter_runtime.prepare_runtime()

    def _reset_runtime_state(self) -> None:
        """Clear transient runtime state so the app can be started again."""
        self._running = False
        self._stop_event = None
        self._loop = None
        self._handler_tasks = set()
        self._adapter_runtime.reset_runtime()

    async def _shutdown_runtime(self) -> None:
        """Stop adapters, drain handlers, and close event subscribers in order."""
        try:
            if self._running:
                self._emit_framework_event(AppStopping())
                await asyncio.sleep(0, result=None)

            await self._adapter_runtime.cancel_tasks(include_internal=False)
            self._event_broadcaster.close()
            await self._wait_for_handler_tasks()
            await self._adapter_runtime.cancel_tasks(include_internal=True)
        finally:
            self._reset_runtime_state()

    @overload
    def on_event[T](self, arg: type[T]) -> Callable[[EventHandler[T]], EventHandler[T]]: ...

    @overload
    def on_event(self, arg: UnionType) -> Callable[[EventHandler[Any]], EventHandler[Any]]: ...

    @overload
    def on_event[T](self, arg: EventHandler[T]) -> EventHandler[T]: ...

    def on_event[T](
        self, arg: type[T] | UnionType | EventHandler[T]
    ) -> Callable[[EventHandler[Any]], EventHandler[Any]] | EventHandler[T]:
        """
        支持两种注册方式：
        1) @app.on_event(EventType) 或 @app.on_event(A | B | C)
        2) @app.on_event  # 从 handler 第一个参数注解推断事件类型（支持联合类型）
        """
        return self._handler_registry.on_event(arg)

    async def wait_event(
        self,
        pred: Callable[[object], bool | Coroutine[Any, Any, bool]],
        timeout: float | None = None,
    ) -> Any:
        waiter_id = next(self._waiter_ids)
        predicate_name = callable_name(pred)
        self._emit_framework_event(
            WaitRegistered(
                waiter_id=waiter_id,
                predicate_name=predicate_name,
                timeout=timeout,
            )
        )

        async def wait_for_match() -> Any:
            async for event_obj in self.events():
                matched = pred(event_obj)
                if inspect.isawaitable(matched):
                    matched = await matched
                if matched:
                    self._emit_framework_event(
                        WaitMatched(
                            waiter_id=waiter_id,
                            predicate_name=predicate_name,
                            timeout=timeout,
                            event_type=event_type_name(event_obj),
                            is_framework_event=self._is_framework_event(event_obj),
                        )
                    )
                    return event_obj
            raise WaitEventCancelledError("应用正在停止，等待事件已取消")

        try:
            if timeout is None:
                return await wait_for_match()

            async with asyncio.timeout(timeout):
                return await wait_for_match()
        except TimeoutError as exc:
            self._emit_framework_event(
                WaitTimedOut(
                    waiter_id=waiter_id,
                    predicate_name=predicate_name,
                    timeout=timeout,
                )
            )
            raise TimeoutError("等待事件超时") from exc
        except asyncio.CancelledError:
            self._emit_framework_event(
                WaitCancelled(
                    waiter_id=waiter_id,
                    predicate_name=predicate_name,
                    timeout=timeout,
                )
            )
            raise

    async def _run_handler(
        self,
        handler: HandlerType,
        event_obj: object,
        *,
        observe: bool,
    ) -> None:
        event_type = event_type_name(event_obj)
        handler_name = callable_name(handler)
        started_at = perf_counter()

        try:
            await handler(event_obj)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            duration_ms = (perf_counter() - started_at) * 1000
            if observe:
                self._emit_framework_event(
                    HandlerFailed(
                        event_type=event_type,
                        is_framework_event=False,
                        handler_name=handler_name,
                        duration_ms=duration_ms,
                        exception=exc,
                    )
                )
            logger.exception(
                "Handler %s 处理 %s 时发生错误",
                handler_name,
                event_type,
            )
            return

        if observe:
            duration_ms = (perf_counter() - started_at) * 1000
            self._emit_framework_event(
                HandlerCompleted(
                    event_type=event_type,
                    is_framework_event=False,
                    handler_name=handler_name,
                    duration_ms=duration_ms,
                )
            )

    async def _dispatch_event(self, event_obj: object, source_adapter: BaseAdapter):
        """分发事件给对应的 handler"""
        observe = self._should_observe_event(event_obj)
        event_type = event_type_name(event_obj)

        if observe:
            self._emit_framework_event(
                EventReceived(
                    **adapter_event_kwargs(source_adapter),
                    event_type=event_type,
                    is_framework_event=False,
                )
            )

        self._event_broadcaster.publish(event_obj)

        # 查找监听该类型的 handlers
        handlers = self._handler_registry.resolve(event_obj)

        if observe:
            handler_names = tuple(callable_name(handler) for handler in handlers)
            self._emit_framework_event(
                HandlersResolved(
                    event_type=event_type,
                    is_framework_event=False,
                    handler_count=len(handler_names),
                    handler_names=handler_names,
                )
            )

        for handler in handlers:
            if observe:
                self._emit_framework_event(
                    HandlerScheduled(
                        event_type=event_type,
                        is_framework_event=False,
                        handler_name=callable_name(handler),
                    )
                )
            self._spawn_handler_task(handler, event_obj, observe=observe)

    async def start(self):
        if self._running:
            raise RuntimeError("BotApp 已在运行中")

        self._prepare_runtime()
        self._emit_framework_event(AppStarting())

        try:
            self._adapter_runtime.start_all()
            self._emit_framework_event(AppStarted())
            stop_event = self._stop_event
            assert stop_event is not None
            await stop_event.wait()
        finally:
            await self._shutdown_runtime()

    def stop(self):
        if self._stop_event is not None:
            self._stop_event.set()

    def run(self) -> None:
        """Run the app in a fresh event loop."""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("收到 KeyboardInterrupt，正在停止应用")
