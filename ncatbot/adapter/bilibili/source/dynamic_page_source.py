"""动态页数据源 — 轮询动态主页，一次性监听多个订阅 UP 主的新动态

通过 bilibili_api.dynamic.get_dynamic_page_info 拉取动态主页，
按订阅 UID 集合过滤，基于每个 UP 主的最新时间戳增量检测新动态。
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from ncatbot.utils import get_log

from .base import BaseSource

LOG = get_log("DynamicPageSource")

# 默认轮询间隔 3 分钟
_DEFAULT_POLL_INTERVAL = 180.0


class DynamicPageSource(BaseSource):
    source_type = "dynamic"

    def __init__(
        self,
        credential: Any,
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(callback)
        self.source_id = "dynamic_page"
        self._credential = credential
        self._poll_interval = poll_interval
        # 订阅的 UP 主 UID 集合
        self._watched_uids: Set[int] = set()
        # 每个 UP 主的最新已知动态时间戳
        self._last_ts: Dict[int, int] = {}
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def add_uid(self, uid: int) -> None:
        """添加一个订阅 UID"""
        self._watched_uids.add(uid)

    def remove_uid(self, uid: int) -> None:
        """移除一个订阅 UID"""
        self._watched_uids.discard(uid)
        self._last_ts.pop(uid, None)

    def has_uid(self, uid: int) -> bool:
        return uid in self._watched_uids

    @property
    def empty(self) -> bool:
        return len(self._watched_uids) == 0

    async def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._task = asyncio.create_task(self._poll_loop(), name="dynamic_page_source")
        LOG.info(
            "动态页源已启动 (轮询间隔 %.0fs, 订阅 %d 个 UID)",
            self._poll_interval,
            len(self._watched_uids),
        )

    # ---- 静态工具 ----

    @staticmethod
    def _extract_uid(item: dict) -> int:
        """从动态 item 中提取作者 UID"""
        modules = item.get("modules") or {}
        author = modules.get("module_author") or {}
        return int(author.get("mid", 0))

    @staticmethod
    def _extract_pub_ts(item: dict) -> int:
        """提取动态发布时间戳"""
        modules = item.get("modules") or {}
        author = modules.get("module_author") or {}
        return int(author.get("pub_ts", 0))

    # ---- 轮询 ----

    async def _fetch_page(self) -> list:
        """拉取动态主页第一页"""
        from bilibili_api.dynamic import get_dynamic_page_info

        resp = await get_dynamic_page_info(credential=self._credential)
        return resp.get("items") or []

    async def _poll_loop(self) -> None:
        # 初次拉取，建立时间戳基线
        try:
            items = await self._fetch_page()
            self._init_baselines(items)
        except Exception:
            LOG.warning("动态页源初次拉取失败", exc_info=True)

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._poll_interval
                )
                break
            except asyncio.TimeoutError:
                pass

            try:
                items = await self._fetch_page()
                await self._detect_new_dynamics(items)
            except asyncio.CancelledError:
                break
            except Exception:
                LOG.debug("动态页源轮询异常", exc_info=True)

        self._running = False

    def _init_baselines(self, items: list) -> None:
        """用首次拉取的结果初始化每个订阅 UID 的时间戳基线"""
        for item in items:
            uid = self._extract_uid(item)
            if uid not in self._watched_uids:
                continue
            ts = self._extract_pub_ts(item)
            # 只记录更大的时间戳（同一 UID 可能有多条）
            if ts > self._last_ts.get(uid, 0):
                self._last_ts[uid] = ts
        LOG.debug("动态页源基线: %s", self._last_ts)

    async def _detect_new_dynamics(self, items: list) -> None:
        """检测并推送新动态"""
        # 按 UID 分组，收集每个订阅 UP 主的动态
        uid_items: Dict[int, list] = {}
        for item in items:
            uid = self._extract_uid(item)
            if uid not in self._watched_uids:
                continue
            uid_items.setdefault(uid, []).append(item)

        for uid, dyn_items in uid_items.items():
            old_ts = self._last_ts.get(uid, 0)
            # 过滤出新动态（时间戳严格大于已知最大值）
            new_items = [it for it in dyn_items if self._extract_pub_ts(it) > old_ts]
            if not new_items:
                continue

            # 按时间戳升序推送，确保先发的先推
            new_items.sort(key=self._extract_pub_ts)
            for item in new_items:
                ts = self._extract_pub_ts(item)
                raw = {
                    "source": "dynamic",
                    "uid": uid,
                    "status": "new",
                    "dynamic": item,
                }
                await self._callback("dynamic", raw)
                # 更新时间戳
                if ts > self._last_ts.get(uid, 0):
                    self._last_ts[uid] = ts

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
        LOG.debug("动态页源已停止")
