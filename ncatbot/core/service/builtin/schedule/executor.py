"""
任务执行器

负责定时任务的条件检查、次数限制与回调触发。
"""

import traceback
from typing import Dict, Any, Optional, TYPE_CHECKING

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
    - 通过回调通知任务触发
    """

    def __init__(self, service: "TimeTaskService"):
        self._service = service

    def execute(self, job_info: Dict[str, Any]) -> None:
        """执行任务"""
        name = job_info["name"]
        plugin_name = job_info.get("plugin_name")

        if job_info["max_runs"] and job_info["run_count"] >= job_info["max_runs"]:
            self._service.remove_job(name)
            return

        if not self._check_conditions(job_info):
            return

        try:
            self._notify_task_triggered(name, plugin_name)
            job_info["run_count"] += 1
        except Exception as e:
            LOG.error(f"定时任务回调执行失败 [{name}]: {e}")
            LOG.debug(f"任务回调异常堆栈:\n{traceback.format_exc()}")

    def _check_conditions(self, job_info: Dict[str, Any]) -> bool:
        """检查执行条件"""
        return all(cond() for cond in job_info["conditions"])

    def _notify_task_triggered(
        self, task_name: str, plugin_name: Optional[str]
    ) -> None:
        """通知任务触发（通过回调）"""
        callback = self._service.on_task_triggered
        if callback is None:
            LOG.debug(f"未设置 on_task_triggered 回调，跳过: {task_name}")
            return

        callback(task_name, plugin_name)
        LOG.debug(f"已触发定时任务回调: {task_name} (plugin={plugin_name})")
