"""
事件消费混入类

代理 AsyncEventDispatcher 的 events() / wait_event() 接口，
通过 _mixin_unload 钩子在卸载时自动关闭所有活跃的 EventStream。

Session 便利方法（wait_session_event / wait_session_reply /
session_prompt / session_choose）在 wait_event 基础上封装了
session 绑定、取消词检测、超时处理和自动回复等常用模式。
"""

import asyncio
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
    TYPE_CHECKING,
)

from ncatbot.utils import get_log

from .session_types import SessionCancelled, SessionResult

if TYPE_CHECKING:
    from ncatbot.core import AsyncEventDispatcher, Event, EventStream, P
    from ncatbot.types.qq import EventType

LOG = get_log("EventMixin")


class EventMixin:
    """
    事件消费混入类

    - ``_mixin_unload``: 关闭所有活跃的 EventStream

    使用示例::

        async with self.events("message") as stream:
            async for event in stream:
                ...
    """

    _dispatcher: "AsyncEventDispatcher"

    def events(
        self,
        event_type: Optional[Union[str, "EventType"]] = None,
    ) -> "EventStream":
        """创建事件流，可选按类型过滤。

        返回的 EventStream 支持 async with / async for。
        插件卸载时框架会自动关闭所有未手动关闭的流。

        Args:
            event_type: 事件类型过滤（前缀匹配），如 "message"、"notice" 等

        Returns:
            EventStream 异步迭代器
        """
        stream = self._dispatcher.events(event_type)
        if not hasattr(self, "_active_streams"):
            self._active_streams: List["EventStream"] = []
        self._active_streams.append(stream)
        return stream

    async def wait_event(
        self,
        predicate: Optional[Callable[["Event"], bool]] = None,
        timeout: Optional[float] = None,
    ) -> "Event":
        """等待下一个满足条件的事件。

        Args:
            predicate: 过滤函数，None 表示接受任意事件
            timeout: 超时秒数，None 表示无限等待

        Returns:
            匹配的 Event

        Raises:
            asyncio.TimeoutError: 超时未匹配到事件
        """
        return await self._dispatcher.wait_event(predicate, timeout)

    # ------------------------------------------------------------------
    # Session 便利方法
    # ------------------------------------------------------------------

    async def wait_session_event(
        self,
        event: object,
        *,
        timeout: Optional[float] = None,
        extra_predicate: Optional[Union[Callable[["Event"], bool], "P"]] = None,
        cancel_words: Optional[Sequence[str]] = None,
    ) -> "Event":
        """等待同 session 的下一个事件。

        自动通过 ``from_event(event)`` 绑定 session（同用户/同群/同消息类型），
        可选附加额外谓词和取消词检测。

        Args:
            event: 触发事件（高层 BaseEvent 或底层 Event 均可）
            timeout: 超时秒数，None 表示无限等待
            extra_predicate: 额外过滤条件，与 session 谓词 AND 组合
            cancel_words: 取消词列表，用户输入匹配时抛出 :class:`SessionCancelled`

        Returns:
            匹配的 Event

        Raises:
            asyncio.TimeoutError: 超时未匹配到事件
            SessionCancelled: 用户输入了取消词
        """
        from ncatbot.core import from_event

        pred: Union[Callable[["Event"], bool], "P"] = from_event(event)

        if extra_predicate is not None:
            pred = pred * extra_predicate  # type: ignore[operator]

        reply_event = await self._dispatcher.wait_event(pred, timeout)

        # 取消词检测
        if cancel_words:
            data = reply_event.data
            if hasattr(data, "raw_message"):
                text = data.raw_message.strip()  # type: ignore[union-attr]
                for word in cancel_words:
                    if text == word:
                        raise SessionCancelled(reply_event, word)

        return reply_event

    async def wait_session_reply(
        self,
        event: object,
        *,
        timeout: Optional[float] = None,
        cancel_words: Optional[Sequence[str]] = None,
    ) -> SessionResult:
        """等待同 session 的文本回复，返回 :class:`SessionResult`。

        内部调用 :meth:`wait_session_event`，将超时和取消转为
        ``SessionResult`` 而非异常。

        Args:
            event: 触发事件
            timeout: 超时秒数
            cancel_words: 取消词列表

        Returns:
            SessionResult — 通过 ``.ok`` 判断是否成功，
            ``.text`` 获取回复文本
        """
        try:
            reply_event = await self.wait_session_event(
                event,
                timeout=timeout,
                cancel_words=cancel_words,
            )
        except asyncio.TimeoutError:
            return SessionResult.from_timeout()
        except SessionCancelled as exc:
            return SessionResult.from_cancel(exc.event, exc.word)

        text = ""
        if hasattr(reply_event.data, "raw_message"):
            text = reply_event.data.raw_message.strip()  # type: ignore[union-attr]
        return SessionResult.of(reply_event, text)

    async def session_prompt(
        self,
        prompt_text: str,
        event: object,
        *,
        timeout: Optional[float] = None,
        cancel_words: Optional[Sequence[str]] = None,
        timeout_reply: Optional[str] = None,
        cancel_reply: Optional[str] = None,
    ) -> SessionResult:
        """发送提示消息并等待同 session 回复（一站式）。

        先调用 ``event.reply(prompt_text)`` 发送提示，再等待回复。
        超时/取消时可自动回复用户。

        Args:
            prompt_text: 要发送给用户的提示文本
            event: 触发事件（必须具有 ``.reply()`` 方法）
            timeout: 超时秒数
            cancel_words: 取消词列表
            timeout_reply: 超时时自动回复的文本，None 则不回复
            cancel_reply: 取消时自动回复的文本，None 则不回复

        Returns:
            SessionResult
        """
        await event.reply(prompt_text)  # type: ignore[union-attr]

        result = await self.wait_session_reply(
            event,
            timeout=timeout,
            cancel_words=cancel_words,
        )

        if result.timed_out and timeout_reply:
            await event.reply(timeout_reply)  # type: ignore[union-attr]
        elif result.cancelled and cancel_reply:
            await event.reply(cancel_reply)  # type: ignore[union-attr]

        return result

    async def session_choose(
        self,
        prompt_text: str,
        event: object,
        *,
        choices: Dict[str, str],
        timeout: Optional[float] = None,
        timeout_reply: Optional[str] = None,
        invalid_reply: Optional[str] = None,
        max_retries: int = 0,
    ) -> SessionResult:
        """发送选择题并等待用户选择（支持重试）。

        ``choices`` 为 ``{用户输入文本: 语义key}`` 的映射，
        如 ``{"确认": "confirm", "取消": "cancel"}``。

        Args:
            prompt_text: 提示文本
            event: 触发事件（必须具有 ``.reply()`` 方法）
            choices: 选项映射，键为用户输入，值为返回的 key
            timeout: 超时秒数（每次等待共享同一超时）
            timeout_reply: 超时时自动回复的文本
            invalid_reply: 无效输入时自动回复的文本
            max_retries: 最大重试次数（0 表示不重试）

        Returns:
            SessionResult — ``.key`` 为匹配到的选项 key，
            ``.text`` 为用户原始输入
        """
        await event.reply(prompt_text)  # type: ignore[union-attr]

        remaining = max_retries + 1
        last_result: Optional[SessionResult] = None

        while remaining > 0:
            remaining -= 1

            try:
                reply_event = await self.wait_session_event(
                    event,
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                if timeout_reply:
                    await event.reply(timeout_reply)  # type: ignore[union-attr]
                return SessionResult.from_timeout()

            text = ""
            if hasattr(reply_event.data, "raw_message"):
                text = reply_event.data.raw_message.strip()  # type: ignore[union-attr]

            if text in choices:
                return SessionResult.of(
                    reply_event,
                    text,
                    key=choices[text],
                )

            last_result = SessionResult.from_invalid(text, reply_event)

            if remaining > 0 and invalid_reply:
                await event.reply(invalid_reply)  # type: ignore[union-attr]

        return last_result  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Mixin 钩子
    # ------------------------------------------------------------------

    async def _mixin_unload(self) -> None:
        """关闭所有活跃的 EventStream。"""
        if not hasattr(self, "_active_streams"):
            return
        for stream in self._active_streams:
            try:
                await stream.aclose()
            except Exception:
                pass
        self._active_streams.clear()
