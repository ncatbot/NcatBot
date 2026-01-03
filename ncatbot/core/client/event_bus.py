"""
事件总线

统一的事件分发中心，支持精确匹配、前缀匹配和正则匹配。
"""

import asyncio
import re
import uuid
import traceback
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin

from .ncatbot_event import NcatBotEvent

LOG = get_log("EventBus")


class HandlerTimeoutError(Exception):
    """处理器超时异常"""

    def __init__(self, meta_data: dict, handler: str, time: float):
        super().__init__()
        self.meta_data = meta_data
        self.handler = handler
        self.time = time

    def __str__(self):
        return f"来自 {self.meta_data['name']} 的处理器 {self.handler} 执行超时 {self.time}"


class EventBus:
    """
    事件总线

    统一的事件分发中心，支持：
    - 精确匹配：event_type 完全匹配
    - 前缀匹配：如 ncatbot.notice.group_increase 也触发 ncatbot.notice
    - 正则匹配：使用 "re:" 前缀
    - 优先级控制：数值越大优先级越高
    """

    def __init__(self, default_timeout: float = 120) -> None:
        """
        初始化事件总线

        Args:
            default_timeout: 默认处理器超时时间（秒）
        """
        self._exact: Dict[str, List[Tuple]] = {}
        self._regex: List[Tuple] = []
        self.default_timeout = default_timeout
        self._handler_meta: Dict[uuid.UUID, Dict] = {}

    # ==================== 订阅管理 ====================

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[NcatBotEvent], Any],
        priority: int = 0,
        timeout: Optional[float] = None,
        plugin: Optional["BasePlugin"] = None,
    ) -> uuid.UUID:
        """
        订阅事件处理程序

        Args:
            event_type: 事件类型，支持精确匹配或 "re:" 前缀的正则表达式
            handler: 事件处理函数（支持同步和异步）
            priority: 处理优先级，数值越大优先级越高
            timeout: 处理器超时时间（秒），None 则使用默认值
            plugin: 插件实例，用于记录元数据

        Returns:
            处理器唯一标识符
        """
        hid = uuid.uuid4()
        timeout_val = timeout if timeout is not None else self.default_timeout

        if plugin:
            self._handler_meta[hid] = plugin.meta_data

        if event_type.startswith("re:"):
            pattern = _compile_regex(event_type[3:])
            self._regex.append((pattern, priority, handler, hid, timeout_val))
            self._regex.sort(key=lambda t: (-t[1], t[2].__name__))
        else:
            bucket = self._exact.setdefault(event_type, [])
            bucket.append((None, priority, handler, hid, timeout_val))
            bucket.sort(key=lambda t: (-t[1], t[2].__name__))

        return hid

    def unsubscribe(self, handler_id: uuid.UUID) -> bool:
        """
        取消订阅事件处理程序

        Args:
            handler_id: subscribe() 返回的处理器标识符

        Returns:
            是否成功移除处理器
        """
        removed = False

        if handler_id in self._handler_meta:
            del self._handler_meta[handler_id]

        for typ in list(self._exact.keys()):
            original_len = len(self._exact[typ])
            self._exact[typ] = [h for h in self._exact[typ] if h[3] != handler_id]
            removed |= len(self._exact[typ]) != original_len
            if not self._exact[typ]:
                del self._exact[typ]

        original_len = len(self._regex)
        self._regex = [h for h in self._regex if h[3] != handler_id]
        removed |= len(self._regex) != original_len

        return removed

    # ==================== 事件发布 ====================

    async def publish(self, event: NcatBotEvent) -> List[Any]:
        """
        发布事件并执行所有匹配的处理器

        Args:
            event: 要发布的事件

        Returns:
            所有处理器的返回结果列表
        """
        LOG.debug(
            f"发布事件: {event.type} 数据: {str(event.data)[:50]}{'...' if len(str(event.data)) > 50 else ''}"
        )
        handlers = self._collect_handlers(event.type)

        for _, priority, handler, hid, timeout in handlers:
            if event._propagation_stopped:
                break

            try:
                result = await asyncio.wait_for(
                    self._run_handler(handler, event), timeout=timeout
                )
                event._results.append(result)
            except asyncio.TimeoutError:
                LOG.error(f"处理器 {handler.__name__} (ID: {hid}) 超时({timeout}秒)")
                meta_data = self._handler_meta.get(hid, {"name": "Unknown"})
                event.add_exception(
                    HandlerTimeoutError(
                        meta_data=meta_data, handler=handler.__name__, time=timeout
                    )
                )
            except Exception as e:
                event.add_exception(e)

        return event._results.copy()

    async def _run_handler(self, handler: Callable, event: NcatBotEvent) -> Any:
        """
        执行处理器

        对于异步处理器：直接 await
        对于同步处理器：使用 asyncio.to_thread() 避免阻塞
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(event)
            else:
                return await asyncio.to_thread(handler, event)
        except Exception as e:
            LOG.error(f"执行处理程序 {handler.__name__} 时发生错误: {e}")
            LOG.debug(f"错误堆栈: {traceback.format_exc()}")
            raise e

    def _collect_handlers(self, event_type: str) -> List[Tuple]:
        """
        收集匹配的事件处理程序

        Args:
            event_type: 事件类型

        Returns:
            匹配的处理器列表（已按优先级排序）
        """
        # 精确匹配
        exact_handlers = self._exact.get(event_type, [])[:]

        # 前缀匹配（如 ncatbot.notice.group_increase 也触发 ncatbot.notice）
        prefix_handlers = []
        parts = event_type.split(".")
        for i in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in self._exact:
                prefix_handlers.extend(self._exact[prefix])

        # 正则匹配
        regex_handlers = []
        for pattern, priority, handler, hid, timeout in self._regex:
            if pattern and pattern.match(event_type):
                regex_handlers.append((pattern, priority, handler, hid, timeout))

        # 合并并排序（按优先级降序）
        all_handlers = exact_handlers + prefix_handlers + regex_handlers
        all_handlers.sort(key=lambda t: (-t[1], t[2].__name__))
        return all_handlers

    # ==================== 生命周期 ====================

    def shutdown(self):
        """关闭事件总线并清理资源"""
        self._exact.clear()
        self._regex.clear()
        self._handler_meta.clear()
        LOG.info("EventBus 已关闭，所有处理器已清理")


@lru_cache(maxsize=128)
def _compile_regex(pattern: str) -> re.Pattern:
    """编译正则表达式并缓存"""
    try:
        return re.compile(pattern)
    except re.error as e:
        raise ValueError(f"无效正则表达式: {pattern}") from e
