"""函数执行器

负责函数执行、过滤器验证、插件上下文注入。
"""

import asyncio
import traceback
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from ncatbot.utils import get_log
from .filter_system.validator import FilterValidator

if TYPE_CHECKING:
    pass

LOG = get_log("FunctionExecutor")


class FunctionExecutor:
    """函数执行器

    负责：
    - 查找函数所属插件
    - 过滤器验证
    - 带上下文执行函数
    """

    def __init__(self, filter_validator: Optional[FilterValidator] = None):
        self._filter_validator = filter_validator or FilterValidator()
        self._func_plugin_map: Dict[Callable, object] = {}
        self._plugin_loader = None

    def set_plugin_loader(self, plugin_loader) -> None:
        """设置插件加载器"""
        self._plugin_loader = plugin_loader

    @property
    def plugins(self) -> List:
        """获取已加载的插件列表"""
        if self._plugin_loader:
            return list(self._plugin_loader.plugins.values())
        return []

    def find_plugin_for_function(self, func: Callable):
        """查找函数所属的插件"""
        if func in self._func_plugin_map:
            return self._func_plugin_map[func]

        for plugin in self.plugins:
            plugin_class = plugin.__class__
            if func in plugin_class.__dict__.values():
                self._func_plugin_map[func] = plugin
                return plugin

        return None

    async def execute(
        self,
        func: Callable,
        event,  # MessageEvent 或 BaseEvent
        *args,
        **kwargs,
    ):
        """执行函数（带过滤器验证和插件上下文）

        Args:
            func: 要执行的函数
            event: 事件对象
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值，验证失败返回 False
        """
        plugin = self.find_plugin_for_function(func)

        try:
            # 过滤器验证
            if hasattr(func, "__filters__") and self._filter_validator:
                if not self._filter_validator.validate_filters(func, event):
                    return False

            # 构建调用参数
            call_args = (plugin, event) + args if plugin else (event,) + args

            # 执行函数
            if asyncio.iscoroutinefunction(func):
                return await func(*call_args, **kwargs)
            else:
                return await asyncio.to_thread(func, *call_args, **kwargs)
        except Exception as e:
            LOG.error(f"执行函数 {func.__name__} 时发生错误: {e}")
            LOG.info(f"{traceback.format_exc()}")
            return False

    def clear_cache(self) -> None:
        """清理插件映射缓存"""
        self._func_plugin_map.clear()
