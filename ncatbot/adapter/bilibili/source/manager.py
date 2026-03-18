"""SourceManager — 多数据源并发调度器

管理直播间 / 私信 / 评论三类数据源的生命周期，
支持运行时动态增删。
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List

from ncatbot.utils import get_log

from .base import BaseSource
from .live_source import LiveSource
from .session_source import SessionSource
from .comment_source import CommentSource

LOG = get_log("SourceManager")


class SourceManager:
    """多数据源调度中枢"""

    def __init__(
        self,
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        max_retry: int = 5,
        retry_after: float = 1.0,
        session_poll_interval: float = 6.0,
        comment_poll_interval: float = 30.0,
    ) -> None:
        self._callback = callback
        self._sources: Dict[str, BaseSource] = {}
        self._max_retry = max_retry
        self._retry_after = retry_after
        self._session_poll_interval = session_poll_interval
        self._comment_poll_interval = comment_poll_interval
        self._stop_event = asyncio.Event()

    # ---- 直播间 ----

    async def add_live_room(self, room_id: int, credential: Any) -> None:
        key = f"live:{room_id}"
        if key in self._sources:
            LOG.warning("直播源 %s 已存在，跳过", room_id)
            return
        source = LiveSource(
            room_id=room_id,
            credential=credential,
            callback=self._callback,
            max_retry=self._max_retry,
            retry_after=self._retry_after,
        )
        self._sources[key] = source
        await source.start()

    async def remove_live_room(self, room_id: int) -> None:
        key = f"live:{room_id}"
        source = self._sources.pop(key, None)
        if source is not None:
            await source.stop()

    # ---- 私信 ----

    async def start_session(self, credential: Any) -> None:
        key = "session"
        if key in self._sources:
            LOG.warning("私信源已存在，跳过")
            return
        source = SessionSource(
            credential=credential,
            callback=self._callback,
            poll_interval=self._session_poll_interval,
        )
        self._sources[key] = source
        await source.start()

    async def stop_session(self) -> None:
        source = self._sources.pop("session", None)
        if source is not None:
            await source.stop()

    # ---- 评论 ----

    async def add_comment_watch(
        self, resource_id: str, resource_type: str, credential: Any
    ) -> None:
        key = f"comment:{resource_id}"
        if key in self._sources:
            LOG.warning("评论源 %s 已存在，跳过", resource_id)
            return
        source = CommentSource(
            resource_id=resource_id,
            resource_type=resource_type,
            credential=credential,
            callback=self._callback,
            poll_interval=self._comment_poll_interval,
        )
        self._sources[key] = source
        await source.start()

    async def remove_comment_watch(self, resource_id: str) -> None:
        key = f"comment:{resource_id}"
        source = self._sources.pop(key, None)
        if source is not None:
            await source.stop()

    # ---- 查询 ----

    def list_sources(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": s.source_type,
                "id": s.source_id,
                "running": s.running,
            }
            for s in self._sources.values()
        ]

    # ---- 生命周期 ----

    async def run_forever(self) -> None:
        """阻塞直到 ``stop_all()`` 被调用"""
        LOG.info("SourceManager 开始运行，当前源数: %d", len(self._sources))
        await self._stop_event.wait()

    async def stop_all(self) -> None:
        """停止所有数据源"""
        LOG.info("正在停止所有数据源...")
        for source in list(self._sources.values()):
            try:
                await source.stop()
            except Exception:
                LOG.debug("停止源 %s 异常", source, exc_info=True)
        self._sources.clear()
        self._stop_event.set()
