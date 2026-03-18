"""私信数据源 — 轮询 bilibili-api Session 获取新私信"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from ncatbot.utils import get_log

from .base import BaseSource

LOG = get_log("SessionSource")


class SessionSource(BaseSource):
    source_type = "session"
    source_id = "session"

    def __init__(
        self,
        credential: Any,
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        poll_interval: float = 6.0,
    ) -> None:
        super().__init__(callback)
        self._credential = credential
        self._poll_interval = poll_interval
        self._session: Optional[Any] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        from bilibili_api.session import Session, EventType

        self._session = Session(credential=self._credential)

        # 注册所有消息类型
        for et in EventType:
            evt_value = str(et.value)

            @self._session.on(et)
            async def _on_event(event: Any, _v: str = evt_value) -> None:
                raw = {
                    "source": "session",
                    "msg_type": _v,
                    "sender_uid": getattr(event, "sender_uid", 0),
                    "receiver_id": getattr(event, "receiver_id", 0),
                    "receiver_type": getattr(event, "receiver_type", 0),
                    "talker_id": getattr(event, "talker_id", 0),
                    "msg_seqno": getattr(event, "msg_seqno", 0),
                    "msg_key": getattr(event, "msg_key", 0),
                    "timestamp": getattr(event, "timestamp", 0),
                    "content": str(getattr(event, "content", "")),
                }
                await self._callback("session", raw)

        self._running = True
        self._task = asyncio.create_task(self._run_session(), name="session_source")
        LOG.info("私信源已启动 (轮询间隔 %.1fs)", self._poll_interval)

    async def _run_session(self) -> None:
        try:
            await self._session.start()
        except asyncio.CancelledError:
            pass
        except Exception:
            LOG.exception("私信源异常退出")
        finally:
            self._running = False

    async def stop(self) -> None:
        if self._session is not None:
            try:
                self._session.close()
            except Exception:
                pass
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._running = False
        self._session = None
        self._task = None
        LOG.info("私信源已停止")
