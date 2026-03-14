"""
服务管理器

负责服务的注册、加载、卸载，按依赖拓扑排序加载。
"""

from collections import deque
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING
from ncatbot.utils import get_log
from .base import BaseService, EventCallback

if TYPE_CHECKING:
    from .builtin.rbac import RBACService
    from .builtin.file_watcher import FileWatcherService
    from .builtin.schedule import TimeTaskService

LOG = get_log("ServiceManager")


class ServiceManager:
    """
    服务管理器

    管理所有服务的生命周期，提供服务的注册、加载、卸载、获取等功能。

    使用示例：
        ```python
        manager = ServiceManager()
        manager.register(RBACService, storage_path="data/rbac.json")
        manager.register(FileWatcherService)
        manager.register(TimeTaskService)
        await manager.load_all()
        ```
    """

    _debug_mode: bool = False
    _test_mode: bool = False

    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_classes: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._event_callback: Optional[EventCallback] = None

    def set_event_callback(self, callback: EventCallback) -> None:
        """注入事件发布回调，load 时会传递给服务实例。"""
        self._event_callback = callback

    def set_debug_mode(self, enable: bool = True) -> None:
        """设置调试模式"""
        self._debug_mode = enable

    def set_test_mode(self, enable: bool = True) -> None:
        """设置测试模式"""
        self._test_mode = enable

    # -------------------------------------------------------------------------
    # 内置服务属性（IDE 类型提示）
    # -------------------------------------------------------------------------

    @property
    def rbac(self) -> "RBACService":
        """RBAC 服务"""
        return self._services.get("rbac")  # type: ignore

    @property
    def file_watcher(self) -> "FileWatcherService":
        """文件监视服务"""
        return self._services.get("file_watcher")  # type: ignore

    @property
    def time_task(self) -> "TimeTaskService":
        """定时任务服务"""
        return self._services.get("time_task")  # type: ignore

    # -------------------------------------------------------------------------
    # 服务管理方法
    # -------------------------------------------------------------------------

    def register(self, service_class: Type[BaseService], **config: Any) -> None:
        """注册服务类"""
        temp = service_class(**config)
        name = temp.name

        self._service_classes[name] = service_class
        self._service_configs[name] = config

    async def load(self, service_name: str) -> BaseService:
        """加载服务"""
        if service_name in self._services:
            return self._services[service_name]

        if service_name not in self._service_classes:
            raise KeyError(f"服务 {service_name} 未注册")

        service = self._service_classes[service_name](
            **self._service_configs[service_name]
        )
        service.emit_event = self._event_callback
        await service._load()
        self._services[service_name] = service
        return service

    async def unload(self, service_name: str) -> None:
        """卸载服务"""
        if service_name not in self._services:
            return

        await self._services[service_name]._close()
        del self._services[service_name]

    async def load_all(self) -> None:
        """按依赖顺序加载所有已注册的服务"""
        order = self._topological_sort()
        for name in order:
            if name not in self._services:
                await self.load(name)

    async def close_all(self) -> None:
        """关闭所有已加载的服务"""
        for name in list(self._services.keys()):
            await self.unload(name)

    def get(self, service_name: str) -> Optional[BaseService]:
        """获取服务实例"""
        return self._services.get(service_name)

    def has(self, service_name: str) -> bool:
        """检查服务是否已加载"""
        return service_name in self._services

    def list_services(self) -> List[str]:
        """列出所有已加载的服务名称"""
        return list(self._services.keys())

    # -------------------------------------------------------------------------
    # 依赖排序
    # -------------------------------------------------------------------------

    def _topological_sort(self) -> List[str]:
        """按依赖关系拓扑排序服务加载顺序（Kahn 算法）"""
        in_degree: Dict[str, int] = {}
        graph: Dict[str, List[str]] = {}

        for name in self._service_classes:
            in_degree.setdefault(name, 0)
            graph.setdefault(name, [])

            cls = self._service_classes[name]
            deps = getattr(cls, "dependencies", []) or []
            for dep in deps:
                if dep in self._service_classes:
                    graph.setdefault(dep, []).append(name)
                    in_degree[name] = in_degree.get(name, 0) + 1

        queue: deque = deque(n for n, d in in_degree.items() if d == 0)
        result: List[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._service_classes):
            missing = set(self._service_classes) - set(result)
            raise ValueError(f"检测到服务循环依赖: {missing}")

        return result
