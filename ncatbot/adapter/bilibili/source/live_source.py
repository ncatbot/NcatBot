"""直播间数据源 — 每个实例在独立线程中监听一个直播间的 WebSocket 弹幕流

每个 LiveSource 拥有独立的线程和事件循环，避免多房间或
LiveDanmaku 内部阻塞操作影响主事件循环。事件通过
``asyncio.run_coroutine_threadsafe`` 线程安全地回调到主循环。
"""

from __future__ import annotations

import asyncio
import threading
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
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready = threading.Event()

    async def start(self) -> None:
        if self._running:
            return

        self._main_loop = asyncio.get_running_loop()
        self._ready.clear()

        from bilibili_api.live import LiveDanmaku

        self._danmaku = LiveDanmaku(
            room_display_id=self._room_id,
            credential=self._credential,
            max_retry=self._max_retry,
            retry_after=self._retry_after,
        )

        @self._danmaku.on("ALL")
        async def _on_all(event: dict) -> None:
            # 开播事件：获取直播间信息附加到事件数据
            if event.get("type") == "LIVE":
                data = event.get("data", {})
                if isinstance(data, dict) and data.get("live_time", 0):
                    await self._attach_room_info(event)

            # 线程安全地将事件回调到主事件循环
            if self._main_loop is not None and self._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._callback("live", event), self._main_loop
                )

        self._running = True
        self._thread = threading.Thread(
            target=self._run_thread,
            name=f"LiveSource({self._room_id})",
            daemon=True,
        )
        self._thread.start()
        LOG.info("直播源 %s 已启动 (线程: %s)", self._room_id, self._thread.name)

    def _run_thread(self) -> None:
        """线程入口：创建独立事件循环并运行 LiveDanmaku 连接。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._connect_danmaku())
        except RuntimeError as exc:
            # stop() 在 connect() 自然返回前调用了 loop.stop()，属于正常关闭路径
            if "Event loop stopped before Future completed" in str(exc):
                LOG.debug(
                    "直播源 %s 事件循环在连接完成前被停止（正常关闭）", self._room_id
                )
            else:
                LOG.exception("直播源 %s 线程异常退出", self._room_id)
        except Exception:
            LOG.exception("直播源 %s 线程异常退出", self._room_id)
        finally:
            self._running = False
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception:
                pass
            loop.close()
            self._loop = None

    async def _attach_room_info(self, event: dict) -> None:
        """在子线程事件循环中获取直播间信息并附加到事件数据。"""
        try:
            from bilibili_api.live import LiveRoom

            room = LiveRoom(
                room_display_id=self._room_id,
                credential=self._credential,
            )
            raw_info = await room.get_room_info()
            event["room_info"] = raw_info
            LOG.info(
                "直播源 %s 开播，已获取直播间信息: %s",
                self._room_id,
                raw_info.get("room_info", {}).get("title", ""),
            )
        except Exception:
            LOG.warning("直播源 %s 获取直播间信息失败", self._room_id, exc_info=True)

    async def _connect_danmaku(self) -> None:
        """在独立事件循环中运行弹幕连接。"""

        @self._danmaku.on("VERIFICATION_SUCCESSFUL")
        async def _on_connected(_: dict) -> None:
            self._ready.set()
            LOG.debug("直播源 %s WebSocket 验证成功", self._room_id)

        try:
            await self._danmaku.connect()
        except asyncio.CancelledError:
            pass
        except Exception:
            LOG.exception("直播源 %s 连接异常", self._room_id)
        finally:
            self._ready.set()  # 防止异常时 ready 永远阻塞

    async def stop(self) -> None:
        if self._danmaku is not None and self._loop is not None:
            loop = self._loop
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._danmaku.disconnect(), loop
                )
                future.result(timeout=10)
            except Exception:
                LOG.debug("断开直播源 %s 时异常", self._room_id, exc_info=True)
            # disconnect() 完成后 connect() 会自然返回，不需要手动 stop loop
            # 直接等待线程退出即可（join 已有超时保护）

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=15)
            if self._thread.is_alive():
                LOG.warning("直播源 %s 线程未能在超时内退出", self._room_id)

        self._running = False
        self._danmaku = None
        self._thread = None
        self._loop = None
        LOG.info("直播源 %s 已停止", self._room_id)
