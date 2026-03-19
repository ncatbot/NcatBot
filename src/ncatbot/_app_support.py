import inspect
from collections.abc import Callable
from types import UnionType
from typing import Any, Union, get_args, get_origin


def callable_name(func: Callable[..., Any]) -> str:
    module = getattr(func, "__module__", "")
    qualname = getattr(func, "__qualname__", type(func).__qualname__)
    if module:
        return f"{module}.{qualname}"
    return qualname


def event_type_name(event_obj: object) -> str:
    event_type = type(event_obj)
    return f"{event_type.__module__}.{event_type.__qualname__}"


def expand_event_types(event_type_spec: object) -> tuple[type[Any], ...]:
    origin = get_origin(event_type_spec)
    if origin in (Union, UnionType):
        resolved: list[type[Any]] = []
        for member in get_args(event_type_spec):
            if member is None or member is type(None):
                continue
            resolved.extend(expand_event_types(member))
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


def ensure_handler_accepts_event(func: Callable[..., Any]) -> None:
    signature = inspect.signature(func)
    if not signature.parameters:
        raise TypeError("事件处理函数必须至少接收一个事件参数")

    try:
        signature.bind(object())
    except TypeError as exc:
        raise TypeError("事件处理函数必须能以单个事件参数调用") from exc


def get_event_types_from_handler(
    func: Callable[..., Any],
) -> tuple[type[Any], ...]:
    ensure_handler_accepts_event(func)
    params = list(inspect.signature(func).parameters.values())

    first_param = params[0]
    annotations = inspect.get_annotations(func, eval_str=True)
    event_type = annotations.get(first_param.name, inspect.Signature.empty)
    if event_type is inspect.Signature.empty:
        raise TypeError("使用 @on_event 时，处理函数第一个参数必须标注类型")
    return expand_event_types(event_type)


def is_handler_registration(arg: object) -> bool:
    if isinstance(arg, type):
        return False
    return get_origin(arg) not in (Union, UnionType) and callable(arg)


def ensure_async_handler(func: Callable[..., Any]) -> None:
    if not inspect.iscoroutinefunction(func):
        raise TypeError("事件处理函数必须使用 async def 定义")
