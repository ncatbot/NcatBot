"""
定时任务混入类

代理 TimeTaskService 的高频接口，简化插件中定时任务的使用。
"""

import asyncio
import inspect
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Union,
    cast,
    final,
)

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.service import ServiceManager, TimeTaskService

LOG = get_log("TimeTaskMixin")


class TimeTaskMixin:
    """
    定时任务混入类

    使用示例::

        class MyPlugin(NcatBotPlugin):
            async def on_load(self):
                self.add_scheduled_task("heartbeat", "30s")

            async def on_close(self):
                pass  # cleanup_scheduled_tasks() 由框架自动调用
    """

    name: str
    services: "ServiceManager"

    @property
    def _time_task(self) -> Optional["TimeTaskService"]:
        """获取定时任务服务实例"""
        if not hasattr(self, "services"):
            return None
        svc = self.services.get("time_task")
        return svc  # type: ignore[return-value]

    @final
    def add_scheduled_task(
        self,
        name: str,
        interval: Union[str, int, float],
        conditions: Optional[List[Callable[[], bool]]] = None,
        max_runs: Optional[int] = None,
        callback: Optional[Callable] = None,
    ) -> bool:
        """添加定时任务。

        Args:
            name: 任务唯一名称
            interval: 调度时间参数，支持:
                - 秒数: 120, 0.5
                - 时间字符串: '30s', '2h30m', '0.5d'
                - 每日时间: 'HH:MM'
                - 一次性: 'YYYY-MM-DD HH:MM:SS'
            conditions: 执行条件列表，全部为 True 时才执行
            max_runs: 最大执行次数
            callback: 任务触发时调用的回调函数（可选，默认查找 self.{name} 方法）

        Returns:
            是否添加成功
        """
        service = self._time_task
        if service is None:
            LOG.warning("定时任务服务不可用，无法添加任务")
            return False

        if not hasattr(self, "_scheduled_task_names"):
            self._scheduled_task_names: List[str] = []

        # 构造回调：显式传入 > 同名方法查找
        if callback is None:
            method = getattr(self, name, None)
            if method is None or not callable(method):
                raise AttributeError(
                    f"插件 {getattr(self, 'name', '?')} 没有方法 '{name}'，"
                    f"请定义 async def {name}(self) 或显式传入 callback 参数"
                )
            callback = method

        # 包装为线程安全的同步回调（scheduler 线程中调用）
        wrapped = self._wrap_task_callback(
            callback,
            getattr(service, "event_loop", None),
        )

        plugin_name = getattr(self, "name", "unknown")
        result = service.add_job(
            name=name,
            interval=interval,
            callback=wrapped,
            conditions=conditions,
            max_runs=max_runs,
            plugin_name=plugin_name,
        )

        if result:
            self._scheduled_task_names.append(name)

        return result

    @staticmethod
    def _wrap_task_callback(
        callback: Callable,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> Callable[[], None]:
        """将同步/异步回调包装为可在工作线程中安全调用的同步函数。"""

        def _sync_wrapper() -> None:
            result = callback()
            if not inspect.isawaitable(result):
                return

            coroutine = TimeTaskMixin._ensure_coroutine(result)

            if loop is not None and loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coroutine, loop)
                future.result()
                return

            asyncio.run(coroutine)

        return _sync_wrapper

    @staticmethod
    def _ensure_coroutine(result: Awaitable[Any]) -> Coroutine[Any, Any, Any]:
        """将任意 awaitable 规范化为 coroutine，便于跨线程调度。"""
        if inspect.iscoroutine(result):
            return cast(Coroutine[Any, Any, Any], result)

        async def _await_result() -> Any:
            return await result

        return _await_result()

    @final
    def remove_scheduled_task(self, name: str) -> bool:
        """移除定时任务。

        Args:
            name: 任务名称

        Returns:
            是否移除成功
        """
        service = self._time_task
        if service is None:
            return False

        result = service.remove_job(name=name)
        if result and hasattr(self, "_scheduled_task_names"):
            try:
                self._scheduled_task_names.remove(name)
            except ValueError:
                pass
        return result

    @final
    def get_task_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务状态。

        Returns:
            包含 name, next_run, run_count, max_runs 的字典，任务不存在返回 None
        """
        service = self._time_task
        if service is None:
            return None
        return service.get_job_status(name)

    @final
    def list_scheduled_tasks(self) -> List[str]:
        """列出本插件注册的所有定时任务名称。"""
        if hasattr(self, "_scheduled_task_names"):
            return list(self._scheduled_task_names)
        return []

    @final
    def cleanup_scheduled_tasks(self) -> None:
        """清理本插件的所有定时任务。"""
        if not hasattr(self, "_scheduled_task_names"):
            return
        for name in list(self._scheduled_task_names):
            self.remove_scheduled_task(name)

    # ------------------------------------------------------------------
    # Mixin 钩子
    # ------------------------------------------------------------------

    def _mixin_unload(self) -> None:
        """卸载时自动清理所有定时任务。"""
        self.cleanup_scheduled_tasks()
