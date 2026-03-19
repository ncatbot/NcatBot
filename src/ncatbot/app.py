import asyncio
import inspect
import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Coroutine
from itertools import count
from time import perf_counter
from types import UnionType
from typing import Any, Literal, TypedDict, Union, cast, get_args, get_origin, overload

from .adapters import BaseAdapter, InternalEventAdapter
from .events import (
    AdapterAdded,
    AdapterRestartScheduled,
    AdapterRunExited,
    AdapterRunFailed,
    AdapterRunStarting,
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

type HandlerReturn = Coroutine[Any, Any, None]
type EventHandler[T] = Callable[[T], HandlerReturn]
type HandlerType = Callable[..., HandlerReturn]


class AdapterEventKwargs(TypedDict):
    adapter_name: str
    platform_name: str
    adapter_version: str


class NcatBotApp:
    def __init__(self, adapter_restart_delay: float = 5.0):
        # 现在的 key 是类型对象，比如 MessageEvent，value 是 handler 列表
        self.handlers: defaultdict[type, list[HandlerType]] = defaultdict(list)
        self.adapters: list[BaseAdapter] = []
        self._event_stream_closed = object()
        self._event_streams_closed = False
        self._event_subscribers: list[asyncio.Queue[object]] = []
        self._running = False
        self._stop_event: asyncio.Event | None = None
        self._adapter_tasks: dict[BaseAdapter, asyncio.Task[None]] = {}
        self._handler_tasks: set[asyncio.Task[None]] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._adapter_restart_delay = adapter_restart_delay
        self._waiter_ids = count(1)
        self._internal_adapter = InternalEventAdapter()
        self._attach_adapter(self._internal_adapter)

    def events(self) -> AsyncIterator[object]:
        """返回广播所有 adapter 事件的异步迭代器。"""
        queue: asyncio.Queue[object] = asyncio.Queue()
        if self._event_streams_closed:
            queue.put_nowait(self._event_stream_closed)
        else:
            self._event_subscribers.append(queue)

        async def iterator() -> AsyncIterator[object]:
            try:
                while True:
                    event_obj = await queue.get()
                    if event_obj is self._event_stream_closed:
                        return
                    yield event_obj
            finally:
                if queue in self._event_subscribers:
                    self._event_subscribers.remove(queue)

        return iterator()

    def _publish_event(self, event_obj: object):
        for subscriber in tuple(self._event_subscribers):
            subscriber.put_nowait(event_obj)

    def _close_event_streams(self):
        self._event_streams_closed = True
        for subscriber in tuple(self._event_subscribers):
            subscriber.put_nowait(self._event_stream_closed)
        self._event_subscribers.clear()

    @property
    def is_running(self) -> bool:
        return self._running

    def _attach_adapter(self, adapter: BaseAdapter):
        self.adapters.append(adapter)

    def _callable_name(self, func: Callable[..., Any]) -> str:
        module = getattr(func, "__module__", "")
        qualname = getattr(func, "__qualname__", type(func).__qualname__)
        if module:
            return f"{module}.{qualname}"
        return qualname

    def _event_type_name(self, event_obj: object) -> str:
        event_type = type(event_obj)
        return f"{event_type.__module__}.{event_type.__qualname__}"

    def _is_internal_adapter(self, adapter: BaseAdapter) -> bool:
        return adapter is self._internal_adapter

    def _is_framework_event(self, event_obj: object) -> bool:
        return isinstance(event_obj, FrameworkEvent)

    def _adapter_event_kwargs(self, adapter: BaseAdapter) -> AdapterEventKwargs:
        return {
            "adapter_name": adapter.adapter_name,
            "platform_name": adapter.platform_name,
            "adapter_version": adapter.adapter_version,
        }

    def _enqueue_framework_event(self, event: FrameworkEvent):
        self._internal_adapter.publish_nowait(event)

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
        self._attach_adapter(adapter)
        if not self._is_internal_adapter(adapter):
            self._emit_framework_event(
                AdapterAdded(**self._adapter_event_kwargs(adapter))
            )
        if self._running and self._loop is not None:
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                current_loop = None

            if current_loop is self._loop:
                self._spawn_adapter_task(adapter)
            else:
                self._loop.call_soon_threadsafe(self._spawn_adapter_task, adapter)

    def _spawn_adapter_task(self, adapter: BaseAdapter):
        task = asyncio.create_task(self._run_adapter(adapter))
        self._adapter_tasks[adapter] = task
        task.add_done_callback(lambda _: self._adapter_tasks.pop(adapter, None))

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

    def _resolve_handlers(self, event_obj: object) -> list[HandlerType]:
        handlers: list[HandlerType] = []
        seen_handler_ids: set[int] = set()

        for registered_type, funcs in self.handlers.items():
            if not isinstance(event_obj, registered_type):
                continue

            for handler in funcs:
                handler_id = id(handler)
                if handler_id in seen_handler_ids:
                    continue
                seen_handler_ids.add(handler_id)
                handlers.append(handler)

        return handlers

    async def _wait_for_handler_tasks(self) -> None:
        while self._handler_tasks:
            tasks = tuple(self._handler_tasks)
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _cancel_adapter_tasks(self, *, include_internal: bool) -> None:
        tasks = tuple(
            task
            for adapter, task in self._adapter_tasks.items()
            if include_internal or not self._is_internal_adapter(adapter)
        )
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _expand_event_types(self, event_type_spec: object) -> tuple[type[Any], ...]:
        origin = get_origin(event_type_spec)
        if origin in (Union, UnionType):
            resolved: list[type[Any]] = []
            for member in get_args(event_type_spec):
                if member is None or member is type(None):
                    continue
                resolved.extend(self._expand_event_types(member))
            if not resolved:
                raise TypeError("联合类型中必须至少包含一个具体事件类型")

            deduplicated: list[type[Any]] = []
            for event_type in resolved:
                if event_type not in deduplicated:
                    deduplicated.append(event_type)
            return tuple(deduplicated)

        if isinstance(event_type_spec, type):
            return (event_type_spec,)

        raise TypeError("事件类型必须是具体类类型，或由它们组成的联合类型（A | B）")

    def _get_event_types_from_handler[T](self, func: EventHandler[T]) -> tuple[type[Any], ...]:
        params = list(inspect.signature(func).parameters.values())
        if not params:
            raise TypeError("事件处理函数必须至少接收一个事件参数")

        first_param = params[0]
        annotations = inspect.get_annotations(func, eval_str=True)
        event_type = annotations.get(first_param.name, inspect.Signature.empty)
        if event_type is inspect.Signature.empty:
            raise TypeError(
                "使用 @on_event 时，处理函数第一个参数必须标注类型"
            )
        return self._expand_event_types(event_type)

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
        if inspect.isfunction(arg):
            func = cast(EventHandler[T], arg)
            event_types = self._get_event_types_from_handler(func)
            for event_type in event_types:
                self.handlers[event_type].append(func)
            return func

        event_types = self._expand_event_types(arg)

        def decorator(func: EventHandler[Any]) -> EventHandler[Any]:
            for event_type in event_types:
                self.handlers[event_type].append(func)
            return func

        return decorator

    async def wait_event(
        self,
        pred: Callable[[object], bool | Coroutine[Any, Any, bool]],
        timeout: float | None = None,
    ) -> Any:
        waiter_id = next(self._waiter_ids)
        predicate_name = self._callable_name(pred)
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
                            event_type=self._event_type_name(event_obj),
                            is_framework_event=self._is_framework_event(event_obj),
                        )
                    )
                    return event_obj
            raise RuntimeError("事件流已关闭，未等到匹配事件")

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
        event_type = self._event_type_name(event_obj)
        handler_name = self._callable_name(handler)
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
        event_type = self._event_type_name(event_obj)

        if observe:
            self._emit_framework_event(
                EventReceived(
                    **self._adapter_event_kwargs(source_adapter),
                    event_type=event_type,
                    is_framework_event=False,
                )
            )

        self._publish_event(event_obj)

        # 查找监听该类型的 handlers
        handlers = self._resolve_handlers(event_obj)

        if observe:
            handler_names = tuple(self._callable_name(handler) for handler in handlers)
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
                        handler_name=self._callable_name(handler),
                    )
                )
            self._spawn_handler_task(handler, event_obj, observe=observe)

    async def _run_adapter(self, adapter: BaseAdapter):
        attempt = 0
        while True:
            attempt += 1
            if not self._is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRunStarting(
                        **self._adapter_event_kwargs(adapter),
                        attempt=attempt,
                    )
                )

            exit_reason: Literal["completed", "failed", "stopped"] = "completed"
            try:
                async with adapter:
                    # 现在拿到的是具体的事件对象
                    async for event_obj in adapter:
                        await self._dispatch_event(event_obj, adapter)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                exit_reason = "failed"
                if not self._is_internal_adapter(adapter):
                    self._emit_framework_event(
                        AdapterRunFailed(
                            **self._adapter_event_kwargs(adapter),
                            attempt=attempt,
                            exception=e,
                        )
                    )
                logger.exception("Adapter %s 发生错误", adapter.adapter_name)

            if self._is_stop_requested():
                exit_reason = "stopped"

            if not self._is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRunExited(
                        **self._adapter_event_kwargs(adapter),
                        attempt=attempt,
                        reason=exit_reason,
                    )
                )

            if not self._running or self._is_stop_requested():
                return

            if not self._is_internal_adapter(adapter):
                self._emit_framework_event(
                    AdapterRestartScheduled(
                        **self._adapter_event_kwargs(adapter),
                        attempt=attempt,
                        delay=self._adapter_restart_delay,
                    )
                )
            logger.warning(
                "Adapter %s 已退出，%.2f 秒后重试",
                adapter.adapter_name,
                self._adapter_restart_delay,
            )
            await asyncio.sleep(self._adapter_restart_delay, result=None)

    async def start(self):
        if self._running:
            raise RuntimeError("BotApp 已在运行中")

        self._running = True
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        self._adapter_tasks = {}
        self._handler_tasks = set()
        self._event_streams_closed = False
        self._emit_framework_event(AppStarting())

        try:
            for adapter in self.adapters:
                self._spawn_adapter_task(adapter)

            self._emit_framework_event(AppStarted())
            await self._stop_event.wait()
        finally:
            if self._running:
                self._emit_framework_event(AppStopping())
                await asyncio.sleep(0, result=None)

            await self._cancel_adapter_tasks(include_internal=False)
            self._close_event_streams()
            await self._wait_for_handler_tasks()
            await self._cancel_adapter_tasks(include_internal=True)

            self._running = False
            self._stop_event = None
            self._loop = None
            self._adapter_tasks = {}
            self._handler_tasks = set()

    def stop(self):
        if self._stop_event is not None:
            self._stop_event.set()

    def run(self) -> None:
        """Run the app in a fresh event loop."""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("收到 KeyboardInterrupt，正在停止应用")
