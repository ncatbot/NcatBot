"""动态数据源 — 轮询指定用户的动态列表，基于时间戳增量检测新/删动态

采用 DataPair 模式缓存每个用户的最新动态时间戳：
- new_ts > old_ts → 发布了新动态
- new_ts < old_ts → 删除了动态（推送深拷贝的 old_data）
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any, Awaitable, Callable, Optional

from ncatbot.utils import get_log

from .base import BaseSource

LOG = get_log("DynamicSource")


class _DynamicDataPair:
    """缓存单个用户的新旧动态数据"""

    __slots__ = ("old_data", "new_data", "old_ts", "new_ts")

    def __init__(self) -> None:
        self.old_data: Optional[dict] = None
        self.new_data: Optional[dict] = None
        self.old_ts: int = 0
        self.new_ts: int = 0

    def update(self, latest_item: dict, pub_ts: int) -> None:
        """更新数据对：将当前 new 移到 old，新数据放入 new"""
        if self.old_data is None:
            # 首次写入，初始化双端
            self.old_data = deepcopy(latest_item)
            self.new_data = latest_item
            self.old_ts = pub_ts
            self.new_ts = pub_ts
        else:
            self.old_data = deepcopy(self.new_data)
            self.old_ts = self.new_ts
            self.new_data = latest_item
            self.new_ts = pub_ts


class DynamicSource(BaseSource):
    source_type = "dynamic"

    def __init__(
        self,
        uid: int,
        credential: Any,
        callback: Callable[[str, dict], Awaitable[None]],
        *,
        poll_interval: float = 600.0,
    ) -> None:
        super().__init__(callback)
        self.source_id = str(uid)
        self._uid = uid
        self._credential = credential
        self._poll_interval = poll_interval
        self._pair: _DynamicDataPair = _DynamicDataPair()
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._task = asyncio.create_task(
            self._poll_loop(), name=f"dynamic_source_{self._uid}"
        )
        LOG.info("动态源 %s 已启动 (轮询间隔 %.0fs)", self._uid, self._poll_interval)

    @staticmethod
    def _extract_latest(resp: dict) -> Optional[dict]:
        """从接口响应中取时间戳最大的一条动态（仅支持新版 items 格式）"""
        items = resp.get("items") or []
        if not items:
            return None
        return max(
            items,
            key=lambda it: int(
                ((it.get("modules") or {}).get("module_author") or {}).get("pub_ts", 0)
            ),
        )

    @staticmethod
    def _extract_pub_ts(item: dict) -> int:
        """提取动态发布时间戳（仅新版 API items 格式）"""
        modules = item.get("modules") or {}
        author = modules.get("module_author") or {}
        return int(author.get("pub_ts", 0))

    async def _poll_loop(self) -> None:
        from bilibili_api.user import User

        user = User(uid=self._uid, credential=self._credential)

        # 初次拉取，填充 DataPair 基线
        try:
            resp = await user.get_dynamics_new()
            latest = self._extract_latest(resp)
            if latest:
                ts = self._extract_pub_ts(latest)
                self._pair.update(latest, ts)
                LOG.debug("动态源 %s 初始时间戳: %d", self._uid, ts)
        except Exception:
            LOG.warning("动态源 %s 初次拉取失败", self._uid)

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._poll_interval
                )
                break
            except asyncio.TimeoutError:
                pass

            try:
                resp = await user.get_dynamics_new()
                latest = self._extract_latest(resp)
                if latest is None:
                    continue

                new_ts = self._extract_pub_ts(latest)
                old_ts = self._pair.new_ts

                if old_ts == 0:
                    # 首次有数据
                    self._pair.update(latest, new_ts)
                    continue

                if new_ts > old_ts:
                    # 新动态发布
                    self._pair.update(latest, new_ts)
                    raw = {
                        "source": "dynamic",
                        "uid": self._uid,
                        "status": "new",
                        "dynamic": self._pair.new_data,
                    }
                    await self._callback("dynamic", raw)

                elif new_ts < old_ts:
                    # 动态被删除 — 推送被删动态的缓存（即上次轮询的 new_data）
                    deleted_data = deepcopy(self._pair.new_data)
                    self._pair.update(latest, new_ts)
                    raw = {
                        "source": "dynamic",
                        "uid": self._uid,
                        "status": "deleted",
                        "dynamic": deleted_data,
                    }
                    await self._callback("dynamic", raw)

                # new_ts == old_ts → 无变化，跳过

            except asyncio.CancelledError:
                break
            except Exception:
                LOG.debug("动态源 %s 轮询异常", self._uid, exc_info=True)

        self._running = False

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
        LOG.debug("动态源 %s 已停止", self._uid)
