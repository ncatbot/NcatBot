"""过滤器注册器 v2.0"""

from typing import Dict, List, Callable, Optional, Union, Any
from dataclasses import dataclass
from .base import BaseFilter
from .decorators import group_filter, private_filter
from ncatbot.utils import get_log

LOG = get_log(__name__)


@dataclass
class FilterEntry:
    """过滤器条目"""

    name: str
    filter_instance: BaseFilter
    metadata: Dict[str, Any]


class FilterRegistry:
    """统一过滤器注册器
    可以用字符串索引 filter 实例
    支持两种注册方式：
    1. filter_registry.register_filter(name, filter_instance)
    """

    _current_plugin_name: str = ""

    def __init__(self):
        self._filters: Dict[str, FilterEntry] = {}
        self._function_filters: Dict[str, Callable] = {}

    @classmethod
    def set_current_plugin_name(cls, plugin_name: str):
        cls._current_plugin_name = plugin_name

    def register_filter(
        self,
        name: str,
        filter_instance: BaseFilter,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """注册过滤器实例

        Args:
            name: 过滤器名称
            filter_instance: 过滤器实例
            metadata: 元数据
        """
        if name in self._filters:
            LOG.warning(f"过滤器 {name} 已存在，将被覆盖")

        self._filters[name] = FilterEntry(
            name=name, filter_instance=filter_instance, metadata=metadata or {}
        )
        LOG.debug(f"注册过滤器实例: {name} -> {filter_instance}")

    # 为函数添加过滤器
    def add_filter_to_function(
        self, func: Callable, *filters: Union[BaseFilter, str]
    ) -> Callable:
        """为函数添加过滤器

        Args:
            func: 目标函数
            *filters: 过滤器实例或名称

        Returns:
            修改后的函数
        """
        if not hasattr(func, "__filters__"):
            setattr(func, "__filters__", [])
            function_name = f"{self._current_plugin_name}::{func.__name__}"
            self._function_filters[function_name] = func

        filter_list: List[BaseFilter] = getattr(func, "__filters__")

        for filter_item in filters:
            if isinstance(filter_item, str):
                # 按名称查找过滤器
                if filter_item in self._filters:
                    filter_list.append(self._filters[filter_item].filter_instance)
                else:
                    LOG.error(f"未找到名为 {filter_item} 的过滤器")
            elif isinstance(filter_item, BaseFilter):
                filter_list.append(filter_item)
            else:
                LOG.error(f"不支持的过滤器类型: {type(filter_item)}")

        LOG.debug(f"为函数 {func.__name__} 添加了 {len(filters)} 个过滤器")
        return func

    # 查询方法
    def get_filter(self, name: str) -> Optional[FilterEntry]:
        """获取过滤器条目"""
        return self._filters.get(name)

    def get_filter_instance(self, name: str) -> Optional[BaseFilter]:
        """获取过滤器实例"""
        entry = self.get_filter(name)
        return entry.filter_instance if entry else None

    def filters(self, *filters: Union[BaseFilter, str]):
        """为函数添加多个过滤器"""

        def wrapper(func: Callable):
            self.add_filter_to_function(func, *filters)
            return func

        return wrapper

    def clear(self):
        """清除所有注册的过滤器"""
        self._filters.clear()
        self._function_filters.clear()

    def revoke_plugin(self, plugin_name: str):
        """撤销插件的过滤器"""
        deleted_filters = [
            name
            for name in self._function_filters.keys()
            if name.split("::")[0] == plugin_name
        ]
        for name in deleted_filters:
            del self._function_filters[name]

    group_filter = group_filter
    private_filter = private_filter

# 全局单例
filter_registry = FilterRegistry()
