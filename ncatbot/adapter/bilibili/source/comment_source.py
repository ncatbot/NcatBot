"""评论数据源 — 轮询指定资源的评论列表，增量检测新评论"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Optional, Set

from ncatbot.utils import get_log

from .base import BaseSource

LOG = get_log("CommentSource")

# bilibili-api CommentResourceType 值映射
_RESOURCE_TYPE_MAP = {
    "video": 1,
    "article": 12,
    "dynamic_draw": 11,
    "dynamic": 17,
    "audio": 14,
    "audio_list": 19,
}


class CommentSource(BaseSource):
    source_type = "comment"

    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        credential: Any,
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        poll_interval: float = 30.0,
    ) -> None:
        super().__init__(callback)
        self.source_id = resource_id
        self._resource_id = resource_id
        self._resource_type = resource_type
        self._credential = credential
        self._poll_interval = poll_interval
        self._known_ids: Set[int] = set()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._task = asyncio.create_task(
            self._poll_loop(), name=f"comment_source_{self._resource_id}"
        )
        LOG.info("评论源 %s (%s) 已启动", self._resource_id, self._resource_type)

    async def _poll_loop(self) -> None:
        from bilibili_api.comment import get_comments
        from bilibili_api.comment import CommentResourceType

        oid = self._resolve_oid()
        res_type = _RESOURCE_TYPE_MAP.get(self._resource_type, 1)

        # 初次拉取，记录已有评论 ID
        try:
            resp = await get_comments(
                oid=oid,
                type_=CommentResourceType(res_type),
                credential=self._credential,
            )
            for reply in resp.get("replies", []) or []:
                self._known_ids.add(reply["rpid"])
        except Exception:
            LOG.warning("评论源 %s 初次拉取失败", self._resource_id)

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._poll_interval
                )
                break  # stop_event 被触发
            except asyncio.TimeoutError:
                pass

            try:
                resp = await get_comments(
                    oid=oid,
                    type_=CommentResourceType(res_type),
                    credential=self._credential,
                )
                for reply in resp.get("replies", []) or []:
                    rpid = reply["rpid"]
                    if rpid not in self._known_ids:
                        self._known_ids.add(rpid)
                        raw = {
                            "source": "comment",
                            "resource_id": self._resource_id,
                            "resource_type": self._resource_type,
                            "reply": reply,
                        }
                        await self._callback("comment", raw)
            except asyncio.CancelledError:
                break
            except Exception:
                LOG.debug("评论源 %s 轮询异常", self._resource_id, exc_info=True)

        self._running = False

    def _resolve_oid(self) -> int:
        """将 resource_id (可能是 BV 号) 转为 oid (int)"""
        # 纯数字直接转
        try:
            return int(self._resource_id)
        except ValueError:
            pass
        # BV 号转 AV 号
        from bilibili_api.utils.aid_bvid_transformer import bvid2aid

        return bvid2aid(self._resource_id)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        self._running = False
        self._task = None
        LOG.info("评论源 %s 已停止", self._resource_id)
