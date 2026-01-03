"""
文件监视服务

监视插件目录中的文件变化，通过回调通知需要热重载的插件。
"""

import asyncio
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Set, Dict, Awaitable

from ncatbot.core.service.base import BaseService
from ncatbot.utils import get_log

LOG = get_log("FileWatcher")

# 回调类型：接收插件目录名，返回是否成功处理
ReloadCallback = Callable[[str], Awaitable[bool]]


class FileWatcherService(BaseService):
    """
    文件监视服务

    监视插件目录中的 .py 文件变化，当检测到变化时通过回调通知。

    使用方式：
    1. 服务启动后调用 set_reload_callback() 注册回调
    2. 当插件目录中的文件发生变化时，服务会调用回调函数
    3. 回调函数负责实际的插件卸载/加载操作
    """

    name = "file_watcher"
    description = "插件文件监视服务"

    # 默认配置
    DEFAULT_WATCH_INTERVAL = 1.0  # 生产环境扫描间隔
    DEFAULT_DEBOUNCE_DELAY = 1.0  # 生产环境防抖延迟
    FAST_WATCH_INTERVAL = 0.02  # debug 模式扫描间隔
    FAST_DEBOUNCE_DELAY = 0.02  # debug 模式防抖延迟

    def __init__(self, **config_args):
        """
        Args:
        """
        super().__init__(**config_args)

        # 文件监视状态
        self._watcher_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._file_cache: Dict[str, float] = {}  # 文件路径 -> 修改时间

        # 监视的目录集合（统一管理所有目录）
        self._watch_dirs: Set[str] = set()

        # 待处理的插件目录
        self._pending_dirs: Set[str] = set()
        self._pending_lock = threading.Lock()
        self._last_process_time: float = 0
        self._first_scan_done = False

        # 回调函数
        self._reload_callback: Optional[ReloadCallback] = None

        # 暂停控制（用于测试隔离）
        self._paused = threading.Event()
        self._paused.set()  # 初始状态：未暂停（可运行）

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def on_load(self) -> None:
        """启动文件监视"""
        # 添加主插件目录
        # 根据 debug 模式自动选择间隔
        is_test_mode = getattr(self.service_manager, "_test_mode", False)
        self._watch_interval = (
            self.FAST_WATCH_INTERVAL if is_test_mode else self.DEFAULT_WATCH_INTERVAL
        )
        self._debounce_delay = (
            self.FAST_DEBOUNCE_DELAY if is_test_mode else self.DEFAULT_DEBOUNCE_DELAY
        )

        self._stop_event.clear()
        self._watcher_thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="FileWatcherThread"
        )
        self._watcher_thread.start()
        LOG.info("文件监视服务已启动")

    async def on_close(self) -> None:
        """停止文件监视"""
        self._stop_event.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=5)

        self._file_cache.clear()
        with self._pending_lock:
            self._pending_dirs.clear()

        LOG.info("文件监视服务已停止")

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def set_reload_callback(self, callback: ReloadCallback) -> None:
        """
        设置热重载回调函数

        当检测到插件目录中的文件变化时，会调用此回调。

        Args:
            callback: 异步回调函数，接收插件目录名作为参数
        """
        self._reload_callback = callback
        LOG.debug("已设置热重载回调")

    @property
    def is_watching(self) -> bool:
        """是否正在监视"""
        return self._watcher_thread is not None and self._watcher_thread.is_alive()

    @property
    def pending_count(self) -> int:
        """待处理的插件目录数量"""
        with self._pending_lock:
            return len(self._pending_dirs)

    def add_watch_dir(self, directory: str) -> None:
        """添加监视目录"""
        abs_path = str(Path(directory).resolve())
        if abs_path not in self._watch_dirs:
            self._watch_dirs.add(abs_path)
            LOG.debug(f"添加监视目录: {abs_path}")

    def pause(self) -> None:
        """
        暂停文件变化处理

        watcher 线程仍在运行和扫描，但不会触发回调。
        用于测试时防止文件重置触发意外的重载。
        """
        self._paused.clear()
        LOG.debug("文件监视处理已暂停")

    def resume(self) -> None:
        """
        恢复文件变化处理

        恢复后会处理暂停期间累积的变化。
        """
        self._paused.set()
        LOG.debug("文件监视处理已恢复")

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _watch_loop(self) -> None:
        """文件监视主循环"""
        LOG.info(f"开始监视目录: {self._watch_dirs}")

        while not self._stop_event.is_set():
            try:
                for watch_dir in list(self._watch_dirs):
                    if os.path.exists(watch_dir):
                        self._scan_files(watch_dir)
                self._process_pending()
                self._stop_event.wait(self._watch_interval)
            except Exception as e:
                LOG.error(f"文件监视出错: {e}")
                self._stop_event.wait(self._watch_interval)

    def _scan_files(self, plugins_dir: str) -> None:
        """扫描插件目录中的文件变化"""
        for py_file in Path(plugins_dir).rglob("*.py"):
            file_path = str(py_file)

            if "site-packages" in file_path:
                continue

            try:
                mod_time = os.path.getmtime(file_path)

                if file_path not in self._file_cache:
                    self._file_cache[file_path] = mod_time
                    if self._first_scan_done:
                        self._on_file_changed(file_path, plugins_dir)
                elif self._file_cache[file_path] != mod_time:
                    self._file_cache[file_path] = mod_time
                    self._on_file_changed(file_path, plugins_dir)
            except OSError as e:
                LOG.debug(f"无法获取文件修改时间 {file_path}: {e}")

        deleted = [f for f in self._file_cache if not os.path.exists(f)]
        for file_path in deleted:
            del self._file_cache[file_path]
            if self._first_scan_done:
                self._on_file_changed(file_path, plugins_dir)

        self._first_scan_done = True

    def _on_file_changed(self, file_path: str, plugins_dir: str) -> None:
        """处理文件变化"""
        if not getattr(self.service_manager, "_debug_mode", False):
            return

        LOG.info(f"检测到文件变化: {file_path}")

        try:
            rel_path = os.path.relpath(file_path, plugins_dir)
            parts = rel_path.split(os.sep)
            if len(parts) > 1:
                first_level_dir = parts[0]
                with self._pending_lock:
                    self._pending_dirs.add(first_level_dir)
                LOG.debug(f"添加待处理插件目录: {first_level_dir}")
        except Exception as e:
            LOG.warning(f"处理文件路径失败: {e}")

    def _process_pending(self) -> None:
        """处理待重载的插件"""
        # 如果暂停，跳过处理（但保留 pending 队列）
        if not self._paused.is_set():
            return

        current_time = time.time()

        with self._pending_lock:
            if not self._pending_dirs:
                return
            if current_time - self._last_process_time < self._debounce_delay:
                return

            dirs_to_process = self._pending_dirs.copy()
            self._pending_dirs.clear()
            self._last_process_time = current_time

        if not self._reload_callback:
            LOG.warning("未设置热重载回调，跳过处理")
            return

        LOG.info(f"处理修改的插件目录: {dirs_to_process}")

        for plugin_dir in dirs_to_process:
            self._trigger_reload(plugin_dir)

    def _trigger_reload(self, plugin_dir: str) -> None:
        """触发重载回调"""
        if self._reload_callback is None:
            LOG.warning(f"无热重载回调，跳过插件 {plugin_dir}")
            return

        callback = self._reload_callback

        async def run_callback():
            try:
                await callback(plugin_dir)
            except Exception as e:
                LOG.error(f"热重载插件 {plugin_dir} 失败: {e}")

        try:
            asyncio.run(run_callback())
        except Exception as e:
            LOG.error(f"执行热重载回调失败: {e}")
