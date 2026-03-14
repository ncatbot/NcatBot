"""
定时任务服务

提供线程安全的定时任务调度功能。
通过事件机制触发任务执行。
"""

import threading
import traceback
from typing import Callable, Optional, List, Dict, Any, Union

from schedule import Scheduler

from ncatbot.core.service.base import BaseService
from ncatbot.utils import get_log
from .parser import TimeTaskParser

LOG = get_log("TimeTaskService")


class TimeTaskService(BaseService):
    """
    定时任务服务

    提供线程安全的定时任务调度功能，支持：
    - 间隔任务/每日定点任务/一次性任务
    - 动态参数生成函数/预定义静态参数传入
    - 执行条件判断
    - 运行次数限制

    使用方式：
    1. 服务启动后自动开始调度线程
    2. 通过 add_job/remove_job 添加/移除任务
    3. 任务执行完成后发布 ncatbot.time_task_executed 事件
    """

    name = "time_task"
    description = "定时任务调度服务"

    # 配置参数
    DEFAULT_TICK_INTERVAL = 0.2  # 默认调度间隔

    def __init__(self, **config_args):
        super().__init__(**config_args)

        # 内部调度器
        self._scheduler = Scheduler()
        self._jobs: List[Dict[str, Any]] = []

        # 线程安全锁
        self._lock = threading.RLock()

        # 调度线程控制
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 延迟初始化执行器
        self._executor = None

    @property
    def executor(self):
        """获取任务执行器（延迟初始化）"""
        if self._executor is None:
            from .executor import TaskExecutor

            self._executor = TaskExecutor(self)
        return self._executor

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def on_load(self) -> None:
        """启动调度线程"""
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
        conditions: Optional[List[Callable[[], bool]]] = None,
        max_runs: Optional[int] = None,
        plugin_name: Optional[str] = None,
    ) -> bool:
        """
        添加定时任务

        任务执行时会发布事件 ncatbot.[plugin_name].[task_name]，
        由订阅该事件的处理器执行实际任务逻辑。

        Args:
            name: 任务唯一标识名称
            interval: 调度时间参数
            conditions: 执行条件列表
            max_runs: 最大执行次数
            plugin_name: 插件名称，用于生成事件类型

        Returns:
            是否添加成功
        """
        with self._lock:
            # 名称唯一性检查
            if any(job["name"] == name for job in self._jobs):
                LOG.warning(f"定时任务添加失败: 任务名称 '{name}' 已存在")
                return False

            try:
                return self._create_job(
                    name=name,
                    interval=interval,
                    conditions=conditions,
                    max_runs=max_runs,
                    plugin_name=plugin_name,
                )
            except Exception as e:
                LOG.error(f"定时任务添加失败: {e}")
                LOG.debug(f"任务添加异常堆栈:\n{traceback.format_exc()}")
                return False

    def remove_job(self, name: str) -> bool:
        """
        移除指定名称的任务

        Args:
            name: 要移除的任务名称

        Returns:
            是否成功找到并移除任务
        """
        with self._lock:
            for job in self._jobs:
                if job["name"] == name:
                    self._scheduler.cancel_job(job["schedule_job"])
                    self._jobs.remove(job)
                    LOG.debug(f"移除定时任务: {name}")
                    return True
        return False

    def get_job_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态信息

        Args:
            name: 任务名称

        Returns:
            包含状态信息的字典
        """
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
        """
        列出所有任务名称

        Returns:
            任务名称列表
        """
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
        conditions: Optional[List[Callable[[], bool]]],
        max_runs: Optional[int],
        plugin_name: Optional[str],
    ) -> bool:
        """创建并注册任务（内部方法，已持有锁）"""
        # 解析时间参数
        interval_cfg = TimeTaskParser.parse(str(interval))

        # 一次性任务强制设置 max_runs=1
        if interval_cfg["type"] == "once":
            if max_runs and max_runs != 1:
                raise ValueError("一次性任务必须设置 max_runs=1")
            max_runs = 1

        job_info: Dict[str, Any] = {
            "name": name,
            "plugin_name": plugin_name,
            "max_runs": max_runs,
            "run_count": 0,
            "conditions": conditions or [],
        }

        # 创建包装函数
        def job_wrapper():
            self.executor.execute(job_info)

        # 创建调度任务
        job = self._create_schedule_job(interval_cfg, job_wrapper)

        if job is None:
            LOG.error(f"无法识别的任务调度类型: {interval_cfg['type']}")
            return False

        job_info["schedule_job"] = job
        self._jobs.append(job_info)
        LOG.debug(f"添加定时任务: {name}")
        return True

    def _create_schedule_job(self, interval_cfg: Dict, job_wrapper: Callable):
        """根据配置创建调度任务"""
        if interval_cfg["type"] == "interval":
            return self._scheduler.every(interval_cfg["value"]).seconds.do(job_wrapper)
        elif interval_cfg["type"] == "daily":
            return self._scheduler.every().day.at(interval_cfg["value"]).do(job_wrapper)
        elif interval_cfg["type"] == "once":
            return self._scheduler.every(interval_cfg["value"]).seconds.do(job_wrapper)
        return None
