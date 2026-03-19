from collections import defaultdict
from collections.abc import Callable, Coroutine
from types import UnionType
from typing import Any, cast, overload

from ._app_support import (
    ensure_async_handler,
    ensure_handler_accepts_event,
    expand_event_types,
    get_event_types_from_handler,
    is_handler_registration,
)

type HandlerReturn = Coroutine[Any, Any, None]
type EventHandler[T] = Callable[[T], HandlerReturn]
type HandlerType = Callable[..., HandlerReturn]


class HandlerRegistry:
    """Store handler registrations and resolve matching handlers for an event."""

    def __init__(self) -> None:
        self.handlers: defaultdict[type[Any], list[HandlerType]] = defaultdict(list)

    def resolve(self, event_obj: object) -> list[HandlerType]:
        """Return matching handlers once each, even if multiple registrations overlap."""
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

    @overload
    def on_event[T](self, arg: type[T]) -> Callable[[EventHandler[T]], EventHandler[T]]: ...

    @overload
    def on_event(self, arg: UnionType) -> Callable[[EventHandler[Any]], EventHandler[Any]]: ...

    @overload
    def on_event[T](self, arg: EventHandler[T]) -> EventHandler[T]: ...

    def on_event[T](
        self, arg: type[T] | UnionType | EventHandler[T]
    ) -> Callable[[EventHandler[Any]], EventHandler[Any]] | EventHandler[T]:
        """Register handlers by explicit event type or by first-parameter annotation."""
        if is_handler_registration(arg):
            func = cast(EventHandler[T], arg)
            ensure_async_handler(func)
            event_types = get_event_types_from_handler(func)
            for event_type in event_types:
                self.handlers[event_type].append(func)
            return func

        event_types = expand_event_types(arg)

        def decorator(func: EventHandler[Any]) -> EventHandler[Any]:
            ensure_async_handler(func)
            ensure_handler_accepts_event(func)
            for event_type in event_types:
                self.handlers[event_type].append(func)
            return func

        return decorator
