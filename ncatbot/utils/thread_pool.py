import threading
from typing import Callable, Any, TypeVar, Coroutine, List
import inspect
import asyncio

T = TypeVar("T")


def run_coroutine(func: Callable[..., Coroutine[Any, Any, T]], *args, **kwargs):
    """
    在新线程中运行协程函数

    ⚠️ 已废弃!NcatBot 已重构为纯异步架构。
    此函数使用 asyncio.run() 会阻塞线程,违背异步并发原则。

    新代码请使用:
    - 在异步上下文中: await func(*args, **kwargs)
    - 在程序入口: asyncio.run(func(*args, **kwargs))

    :param func: 协程函数
    :param args: 位置参数
    :param kwargs: 关键字参数
    :return: 协程函数的返回值
    """
    import warnings

    warnings.warn(
        "run_coroutine 已废弃,NcatBot 已重构为纯异步架构。"
        "请直接使用 await 或 asyncio.run()",
        DeprecationWarning,
        stacklevel=2,
    )

    if not inspect.iscoroutinefunction(func):
        return func(*args, **kwargs)

    result: List[T] = []

    def runner():
        try:
            result.append(asyncio.run(func(*args, **kwargs)))
        except Exception as e:
            result.append(e)

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if isinstance(result[0], Exception):
        raise result[0]
    return result[0]
