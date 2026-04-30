"""
任务执行器

负责定时任务的条件检查、次数限制与回调触发。
"""

import traceback
from typing import Dict, Any, TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from .service import TimeTaskService

LOG = get_log("TimeTaskExecutor")


class TaskExecutor:
    """
    任务执行器

    负责执行定时任务，包括：
    - 条件检查
    - 执行次数检查
    - 调用 job 绑定的 callback
    """

    def __init__(self, service: "TimeTaskService"):
        self._service = service

    def execute(self, job_info: Dict[str, Any]) -> None:
        """执行任务"""
        name = job_info["name"]

        with self._service._lock:
            max_runs = job_info["max_runs"]
            run_count = job_info["run_count"]

        if max_runs and run_count >= max_runs:
            self._service.remove_job(name)
            return

        try:
            if not self._check_conditions(job_info):
                return

            job_info["callback"]()

            with self._service._lock:
                job_info["run_count"] += 1
                run_count = job_info["run_count"]
                max_runs = job_info["max_runs"]

            if max_runs and run_count >= max_runs:
                self._service.remove_job(name)

            if not name.startswith("_"):
                LOG.debug("定时任务已执行: %s", name)
        except Exception as e:
            LOG.error(f"定时任务回调执行失败 [{name}]: {e}")
            LOG.debug(f"任务回调异常堆栈:\n{traceback.format_exc()}")

    def _check_conditions(self, job_info: Dict[str, Any]) -> bool:
        """检查执行条件"""
        return all(cond() for cond in job_info["conditions"])
