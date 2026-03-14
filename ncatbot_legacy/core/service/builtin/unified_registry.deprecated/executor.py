"""函数执行器

负责函数执行、过滤器验证、插件上下文注入。
"""

import asyncio
import traceback
from typing import Callable, Optional, TYPE_CHECKING

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

    async def execute(
        self,
        func: Callable,
        plugin: Optional[object],
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
