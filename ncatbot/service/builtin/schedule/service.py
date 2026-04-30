"""
定时任务服务

提供线程安全的定时任务调度功能，通过回调通知任务触发。
"""

import asyncio
import threading
import traceback
from typing import Callable, Optional, List, Dict, Any, Union

from schedule import Scheduler

from ...base import BaseService
from ncatbot.utils import get_log
from .parser import TimeTaskParser
from .executor import TaskExecutor

LOG = get_log("TimeTaskService")


class TimeTaskService(BaseService):
    """定时任务调度服务

    每个任务通过 ``add_job(callback=...)`` 绑定回调，
    调度线程仅负责判定触发时机，实际执行交给独立工作线程。
    """

    name = "time_task"
    description = "定时任务调度服务"

    DEFAULT_TICK_INTERVAL = 0.2

    def __init__(self, **config_args):
        super().__init__(**config_args)

        self._scheduler = Scheduler()
        self._jobs: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        self._executor = None

    @property
    def executor(self):
        """获取任务执行器（延迟初始化）"""
        if self._executor is None:
            self._executor = TaskExecutor(self)
        return self._executor

    @property
    def event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """获取服务绑定的主事件循环。"""
        return self._event_loop

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def on_load(self) -> None:
        """启动调度线程"""
        self._event_loop = asyncio.get_running_loop()
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._schedule_loop, daemon=True, name="TimeTaskSchedulerThread"
        )
        self._scheduler_thread.start()
        LOG.info("定时任务服务已启动")

    async def on_close(self) -> None:
        """停止调度线程"""
        self._stop_event.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=5)

        with self._lock:
            self._jobs.clear()

        self._event_loop = None
        LOG.info("定时任务服务已停止")

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._scheduler_thread is not None and self._scheduler_thread.is_alive()

    @property
    def job_count(self) -> int:
        """当前任务数量"""
        with self._lock:
            return len(self._jobs)

    def add_job(
        self,
        name: str,
        interval: Union[str, int, float],
        callback: Callable[[], None],
        conditions: Optional[List[Callable[[], bool]]] = None,
        max_runs: Optional[int] = None,
        plugin_name: Optional[str] = None,
    ) -> bool:
        """
        添加定时任务

        Args:
            name: 任务唯一标识名称
            interval: 调度时间参数
            callback: 任务触发时调用的回调函数（在工作线程中执行）
            conditions: 执行条件列表
            max_runs: 最大执行次数
            plugin_name: 插件名称

        Returns:
            是否添加成功
        """
        with self._lock:
            if any(job["name"] == name for job in self._jobs):
                LOG.warning(f"定时任务添加失败: 任务名称 '{name}' 已存在")
                return False

            try:
                return self._create_job(
                    name=name,
                    interval=interval,
                    callback=callback,
                    conditions=conditions,
                    max_runs=max_runs,
                    plugin_name=plugin_name,
                )
            except Exception as e:
                LOG.error(f"定时任务添加失败: {e}")
                LOG.debug(f"任务添加异常堆栈:\n{traceback.format_exc()}")
                return False

    def remove_job(self, name: str) -> bool:
        """移除指定名称的任务"""
        with self._lock:
            for job in self._jobs:
                if job["name"] == name:
                    self._scheduler.cancel_job(job["schedule_job"])
                    self._jobs.remove(job)
                    LOG.debug(f"移除定时任务: {name}")
                    return True
        return False

    def get_job_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态信息"""
        with self._lock:
            for job in self._jobs:
                if job["name"] == name:
                    return {
                        "name": name,
                        "next_run": job["schedule_job"].next_run,
                        "run_count": job["run_count"],
                        "max_runs": job["max_runs"],
                    }
        return None

    def list_jobs(self) -> List[str]:
        """列出所有任务名称"""
        with self._lock:
            return [job["name"] for job in self._jobs]

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

    def _schedule_loop(self) -> None:
        """调度主循环"""
        LOG.debug("调度线程已启动")
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    self._scheduler.run_pending()
                self._stop_event.wait(self.DEFAULT_TICK_INTERVAL)
            except Exception as e:
                LOG.error(f"调度循环出错: {e}")
                self._stop_event.wait(self.DEFAULT_TICK_INTERVAL)

    def _create_job(
        self,
        name: str,
        interval: Union[str, int, float],
        callback: Callable[[], None],
        conditions: Optional[List[Callable[[], bool]]],
        max_runs: Optional[int],
        plugin_name: Optional[str],
    ) -> bool:
        """创建并注册任务（内部方法，已持有锁）"""
        interval_cfg = TimeTaskParser.parse(str(interval))

        if interval_cfg["type"] == "once":
            if max_runs and max_runs != 1:
                raise ValueError("一次性任务必须设置 max_runs=1")
            max_runs = 1

        job_info: Dict[str, Any] = {
            "name": name,
            "plugin_name": plugin_name,
            "callback": callback,
            "max_runs": max_runs,
            "run_count": 0,
            "is_running": False,
            "conditions": conditions or [],
        }

        def job_wrapper():
            self._dispatch_job(job_info)

        job = self._create_schedule_job(interval_cfg, job_wrapper)

        if job is None:
            LOG.error(f"无法识别的任务调度类型: {interval_cfg['type']}")
            return False

        job_info["schedule_job"] = job
        self._jobs.append(job_info)
        LOG.debug(f"添加定时任务: {name}")
        return True

    def _dispatch_job(self, job_info: Dict[str, Any]) -> None:
        """将到点任务派发到独立工作线程，避免阻塞调度线程。"""
        name = job_info["name"]

        with self._lock:
            if job_info["is_running"]:
                if not name.startswith("_"):
                    LOG.debug("定时任务仍在执行，跳过本次触发: %s", name)
                return
            job_info["is_running"] = True

        worker = threading.Thread(
            target=self._run_job,
            args=(job_info,),
            daemon=True,
            name=f"TimeTaskWorker-{name}",
        )

        try:
            worker.start()
        except Exception:
            with self._lock:
                job_info["is_running"] = False
            raise

    def _run_job(self, job_info: Dict[str, Any]) -> None:
        """在工作线程中执行任务并清理运行态。"""
        try:
            self.executor.execute(job_info)
        finally:
            with self._lock:
                job_info["is_running"] = False

    def _create_schedule_job(self, interval_cfg: Dict, job_wrapper: Callable):
        """根据配置创建调度任务"""
        if interval_cfg["type"] == "interval":
            return self._scheduler.every(interval_cfg["value"]).seconds.do(job_wrapper)
        elif interval_cfg["type"] == "daily":
            return self._scheduler.every().day.at(interval_cfg["value"]).do(job_wrapper)
        elif interval_cfg["type"] == "once":
            return self._scheduler.every(interval_cfg["value"]).seconds.do(job_wrapper)
        return None
