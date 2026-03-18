"""
异步事件分发器

纯事件路由：通过 callback 接收事件，广播到所有事件流消费者。
外部通过 events() / async for / wait_event 消费事件。
"""

from __future__ import annotations

import asyncio
from typing import (
    Awaitable,
    Callable,
    Optional,
    Set,
    Union,
    TYPE_CHECKING,
)

from ncatbot.types.qq import EventType
from ncatbot.utils import get_log

from .event import Event
from .stream import EventStream, _STOP

if TYPE_CHECKING:
    from ncatbot.types import BaseEventData

LOG = get_log("AsyncEventDispatcher")


class AsyncEventDispatcher:
    """异步事件分发器

    纯事件路由器：
    - 生产端：外部通过 :meth:`callback` 获取回调函数，将 ``BaseEventData`` 喂入。
    - 消费端：通过 :meth:`events` / ``async for`` / :meth:`wait_event` 消费事件。

    用法::

        dispatcher = AsyncEventDispatcher()

        # 将 callback 交给 adapter
        adapter.set_event_callback(dispatcher.callback)

        # 消费事件
        async with dispatcher.events(EventType.MESSAGE) as stream:
            async for event in stream:
                print(event.type, event.data)
    """

    _DEFAULT_STREAM_QUEUE_SIZE = 500

    def __init__(
        self,
        stream_queue_size: int = _DEFAULT_STREAM_QUEUE_SIZE,
    ):
        self._stream_queues: Set[asyncio.Queue] = set()
        self._stream_queue_size = stream_queue_size
        self._waiters: list[_Waiter] = []
        self._closed = False

    # ---- 生产端 ----

    @property
    def callback(self) -> Callable[["BaseEventData"], "Awaitable[None]"]:
        """返回一个异步回调函数，供外部（如 Adapter）推送事件。

        回调签名: ``async (data: BaseEventData) -> None``
        """
        return self._on_event

    async def _on_event(self, data: "BaseEventData") -> None:
        """接收外部推送的事件数据，resolve 类型后广播。"""
        if self._closed:
            return

        event_type = self._resolve_type(data)
        platform = getattr(data, "platform", "unknown")
        event = Event(type=event_type, data=data, platform=platform)

        self._broadcast(event)
        self._resolve_waiters(event)

    # ---- 消费端：事件流 ----

    def events(
        self,
        event_type: Optional[Union[str, EventType]] = None,
    ) -> EventStream:
        """创建事件流。

        Args:
            event_type: 按类型过滤。
                - ``EventType`` 枚举: 前缀匹配（如 ``EventType.MESSAGE`` 匹配所有 message 子类型）。
                - ``str``: 前缀匹配（如 ``"message.group"`` 精确匹配，``"message"`` 匹配所有）。
                - ``None``: 不过滤，接收全部事件。

        Returns:
            :class:`EventStream` 异步可迭代对象，支持 ``async with`` / ``async for`` / ``aclose()``。
        """
        if self._closed:
            raise RuntimeError("AsyncEventDispatcher 已关闭")

        queue: asyncio.Queue = asyncio.Queue(maxsize=self._stream_queue_size)
        self._stream_queues.add(queue)
        return EventStream(self, queue, event_type)

    def __aiter__(self):
        return self.events()

    # ---- 消费端：一次性等待 ----

    async def wait_event(
        self,
        predicate: Optional[Callable[[Event], bool]] = None,
        timeout: Optional[float] = None,
    ) -> Event:
        """等待下一个满足条件的事件。

        Args:
            predicate: 过滤函数，``None`` 表示接受任意事件。
            timeout: 超时秒数，``None`` 表示无限等待。

        Returns:
            匹配的 :class:`Event` 实例。

        Raises:
            asyncio.TimeoutError: 超时未等到匹配事件。
            RuntimeError: dispatcher 已关闭。
        """
        if self._closed:
            raise RuntimeError("AsyncEventDispatcher 已关闭")

        loop = asyncio.get_running_loop()
        future: asyncio.Future[Event] = loop.create_future()
        waiter = _Waiter(predicate=predicate, future=future)
        self._waiters.append(waiter)

        try:
            if timeout is None:
                return await future
            return await asyncio.wait_for(future, timeout)
        finally:
            try:
                self._waiters.remove(waiter)
            except ValueError:
                pass

    # ---- 内部方法 ----

    def _unregister_stream(self, queue: asyncio.Queue) -> None:
        """由 EventStream.aclose() 调用，注销队列。"""
        self._stream_queues.discard(queue)

    def _broadcast(self, event: Event) -> None:
        """将事件广播到所有活跃的流队列。"""
        for queue in tuple(self._stream_queues):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                LOG.debug("事件流队列已满，丢弃最旧事件")
            try:
                queue.put_nowait(event)
            except Exception:
                LOG.exception("写入事件流队列失败")

    def _resolve_waiters(self, event: Event) -> None:
        """尝试 resolve 所有匹配的一次性 waiter。"""
        for waiter in tuple(self._waiters):
            if waiter.future.done():
                continue
            try:
                if waiter.predicate is None or waiter.predicate(event):
                    waiter.future.set_result(event)
            except Exception as exc:
                waiter.future.set_exception(exc)

    async def close(self) -> None:
        """关闭 dispatcher，终止所有活跃事件流和 waiter。"""
        if self._closed:
            return
        self._closed = True

        # 终止所有 stream
        for queue in tuple(self._stream_queues):
            try:
                queue.put_nowait(_STOP)
            except Exception:
                pass
        self._stream_queues.clear()

        # 终止所有 waiter
        closed_err = RuntimeError("AsyncEventDispatcher 已关闭")
        for waiter in self._waiters:
            if not waiter.future.done():
                waiter.future.set_exception(closed_err)
        self._waiters.clear()

    @staticmethod
    def _resolve_type(data: "BaseEventData") -> str:
        """从数据模型推导事件类型字符串

        优先使用平台注册的 secondary key，再 fallback 到全局 map。
        类型值统一 lowercase 归一化。

        例:
          QQ:       post_type=message, message_type=group → "message.group"
          Bilibili: post_type=live, live_event_type=DANMU_MSG → "live.danmu_msg"
          GitHub:   post_type=issue, action=opened → "issue.opened"
        """
        from ncatbot.event.common.factory import get_secondary_key

        post_type = getattr(data, "post_type", "")
        if hasattr(post_type, "value"):
            post_type = post_type.value
        post_type = str(post_type)

        # 全局 secondary key map（QQ 兼容）
        _global_secondary_map = {
            "message": "message_type",
            "message_sent": "message_type",
            "notice": "notice_type",
            "request": "request_type",
            "meta_event": "meta_event_type",
        }

        # 优先查平台注册的 secondary key
        platform = getattr(data, "platform", "")
        if hasattr(platform, "value"):
            platform = platform.value
        attr_name = get_secondary_key(str(platform), post_type)

        # fallback 到全局 map
        if not attr_name:
            attr_name = _global_secondary_map.get(post_type, "")

        secondary = ""
        if attr_name:
            val = getattr(data, attr_name, "")
            secondary = val.value if hasattr(val, "value") else str(val) if val else ""

            # QQ 特殊情况: notice + notify → 使用 sub_type
            if post_type == "notice" and secondary == "notify":
                sub = getattr(data, "sub_type", "")
                secondary = (
                    sub.value
                    if hasattr(sub, "value")
                    else str(sub)
                    if sub
                    else secondary
                )

        # 统一 lowercase 归一化
        if secondary:
            return f"{post_type}.{secondary.lower()}"
        return post_type


class _Waiter:
    """wait_event() 的内部状态。"""

    __slots__ = ("predicate", "future")

    def __init__(
        self,
        predicate: Optional[Callable[[Event], bool]],
        future: asyncio.Future[Event],
    ):
        self.predicate = predicate
        self.future = future
