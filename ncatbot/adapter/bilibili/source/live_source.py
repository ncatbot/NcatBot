"""直播间数据源 — 每个实例监听一个直播间的 WebSocket 弹幕流"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional

from ncatbot.utils import get_log

from .base import BaseSource

LOG = get_log("LiveSource")


class LiveSource(BaseSource):
    source_type = "live"

    def __init__(
        self,
        room_id: int,
        credential: "Any",
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        max_retry: int = 5,
        retry_after: float = 1.0,
    ) -> None:
        super().__init__(callback)
        self.source_id = str(room_id)
        self._room_id = room_id
        self._credential = credential
        self._max_retry = max_retry
        self._retry_after = retry_after
        self._danmaku: Optional["Any"] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        from bilibili_api.live import LiveDanmaku

        self._danmaku = LiveDanmaku(
            room_display_id=self._room_id,
            credential=self._credential,
            max_retry=self._max_retry,
            retry_after=self._retry_after,
        )

        @self._danmaku.on("ALL")
        async def _on_all(event: dict) -> None:
            await self._callback("live", event)

        self._running = True
        self._task = asyncio.create_task(
            self._run_danmaku(), name=f"live_source_{self._room_id}"
        )
        LOG.info("直播源 %s 已启动", self._room_id)

    async def _run_danmaku(self) -> None:
        try:
            await self._danmaku.connect()
        except asyncio.CancelledError:
            pass
        except Exception:
            LOG.exception("直播源 %s 异常退出", self._room_id)
        finally:
            self._running = False

    async def stop(self) -> None:
        if self._danmaku is not None:
            try:
                await self._danmaku.disconnect()
            except Exception:
                pass
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._running = False
        self._danmaku = None
        self._task = None
        LOG.info("直播源 %s 已停止", self._room_id)
