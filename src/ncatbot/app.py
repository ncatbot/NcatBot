import asyncio
import inspect
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Coroutine
from types import UnionType
from typing import Any, Union, cast, get_args, get_origin, overload

from .adapters import BaseAdapter

type HandlerReturn = Coroutine[Any, Any, None]
type EventHandler[T] = Callable[[T], HandlerReturn]
type HandlerType = Callable[..., HandlerReturn]

class BotApp:
    def __init__(self):
        # 现在的 key 是类型对象，比如 MessageEvent，value 是 handler 列表
        self.handlers: defaultdict[type, list[HandlerType]] = defaultdict(list)
        self.adapters: list[BaseAdapter] = []
        self._event_stream_closed = object()
        self._event_subscribers: list[asyncio.Queue[object]] = []
        self._running = False
        self._stop_event: asyncio.Event | None = None
        self._adapter_tasks: list[asyncio.Task[None]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def events(self) -> AsyncIterator[object]:
        """返回广播所有 adapter 事件的异步迭代器。"""
        queue: asyncio.Queue[object] = asyncio.Queue()
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
        for subscriber in tuple(self._event_subscribers):
            subscriber.put_nowait(self._event_stream_closed)
        self._event_subscribers.clear()

    @property
    def is_running(self) -> bool:
        return self._running

    def add_adapter(self, adapter: BaseAdapter):
        self.adapters.append(adapter)
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
        self._adapter_tasks.append(task)

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

    async def _dispatch_event(self, event_obj: object):
        """分发事件给对应的 handler"""
        self._publish_event(event_obj)

        # 查找监听该类型的 handlers
        handlers: list[HandlerType] = []
        for registered_type, funcs in self.handlers.items():
            if isinstance(event_obj, registered_type):
                handlers.extend(funcs)

        for handler in handlers:
            asyncio.create_task(handler(event_obj))

    async def _run_adapter(self, adapter: BaseAdapter):
        try:
            async with adapter:
                # 现在拿到的是具体的事件对象
                async for event_obj in adapter:
                    await self._dispatch_event(event_obj)
        except Exception as e:
            print(f"Adapter {adapter.adapter_name} 发生错误: {e}")

    async def start(self):
        if self._running:
            raise RuntimeError("BotApp 已在运行中")

        self._running = True
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        self._adapter_tasks = []

        try:
            for adapter in self.adapters:
                self._spawn_adapter_task(adapter)

            await self._stop_event.wait()
        finally:
            self._running = False
            self._stop_event = None
            self._loop = None

            tasks, self._adapter_tasks = self._adapter_tasks, []
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            self._close_event_streams()

    def stop(self):
        if self._stop_event is not None:
            self._stop_event.set()

    def run(self):
        asyncio.run(self.start())
