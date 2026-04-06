"""
插件混入模块

提供插件的便捷代理接口：事件消费、定时任务、配置管理、数据持久化、权限管理。
每个 Mixin 通过 _mixin_load / _mixin_unload 钩子自动参与插件生命周期。
"""

from .config_mixin import ConfigMixin
from .data_mixin import DataMixin
from .dispatch_filter_mixin import DispatchFilterMixin
from .event_mixin import EventMixin
from .rbac_mixin import RBACMixin
from .session_types import SessionCancelled, SessionResult
from .time_task_mixin import TimeTaskMixin

__all__ = [
    "ConfigMixin",
    "DataMixin",
    "DispatchFilterMixin",
    "EventMixin",
    "RBACMixin",
    "SessionCancelled",
    "SessionResult",
    "TimeTaskMixin",
]
