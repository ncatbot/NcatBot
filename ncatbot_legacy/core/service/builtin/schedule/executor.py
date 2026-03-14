"""
任务执行器

提供定时任务的执行逻辑。
通过发布事件 ncatbot.[plugin_name].[task_name] 触发任务执行。
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
    - 发布任务事件（由订阅者执行实际逻辑）
    """

    def __init__(self, service: "TimeTaskService"):
        self._service = service

    def execute(self, job_info: Dict[str, Any]) -> None:
        """
        执行任务

        通过发布 ncatbot.[plugin_name].[task_name] 事件来触发任务。
        实际的任务逻辑由订阅该事件的处理器执行。

        Args:
            job_info: 任务信息字典
        """
        name = job_info["name"]
        plugin_name = job_info.get("plugin_name")

        # 执行次数检查
        if job_info["max_runs"] and job_info["run_count"] >= job_info["max_runs"]:
            self._service.remove_job(name)
            return

        # 条件检查
        if not self._check_conditions(job_info):
            return

        try:
            self._publish_task_event(plugin_name, name)
            job_info["run_count"] += 1
        except Exception as e:
            LOG.error(f"定时任务事件发布失败 [{name}]: {e}")
            LOG.debug(f"任务事件发布异常堆栈:\n{traceback.format_exc()}")

    def _check_conditions(self, job_info: Dict[str, Any]) -> bool:
        """检查执行条件"""
        return all(cond() for cond in job_info["conditions"])

    def _publish_task_event(self, plugin_name: Optional[str], task_name: str) -> None:
        """
        发布任务执行事件（线程安全）

        事件类型格式: ncatbot.[plugin_name].[task_name]
        如果没有 plugin_name，则格式为: ncatbot.time_task.[task_name]
        """
        service_manager = self._service.service_manager
        if service_manager is None:
            LOG.debug(f"无法发布任务事件 [{task_name}]: ServiceManager 不可用")
            return

        bot_client = getattr(service_manager, "bot_client", None)
        if bot_client is None:
            LOG.debug(f"无法发布任务事件 [{task_name}]: BotClient 不可用")
            return

        event_bus = getattr(bot_client, "event_bus", None)
        if event_bus is None:
            LOG.debug(f"无法发布任务事件 [{task_name}]: EventBus 不可用")
            return

        from ncatbot.core.client.ncatbot_event import NcatBotEvent

        # 构建事件类型: ncatbot.[plugin_name].[task_name]
        if plugin_name:
            event_type = f"ncatbot.{plugin_name}.{task_name}"
        else:
            event_type = f"ncatbot.time_task.{task_name}"

        event = NcatBotEvent(
            type=event_type,
            data={"task_name": task_name, "plugin_name": plugin_name},
        )

        # 使用 EventBus 提供的线程安全接口
        event_bus.publish_threadsafe_wait(event, timeout=1.0)
        LOG.debug(f"已发布定时任务事件: {event_type}")
