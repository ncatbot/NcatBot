"""
Hook 系统

Hook 绑定在 handler 函数上 (func.__hooks__)，实例既是执行器又是装饰器。
Dispatcher 中调用: await hook.execute(ctx)
装饰器使用: @hook_instance 或 @add_hooks(hook1, hook2)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .dispatcher import HandlerEntry
    from ncatbot.api import IBotAPI
    from ncatbot.core.dispatcher.event import Event
    from ncatbot.service import ServiceManager


class HookStage(Enum):
    """Hook 执行阶段"""

    BEFORE_CALL = "before_call"
    AFTER_CALL = "after_call"
    ON_ERROR = "on_error"


class HookAction(Enum):
    """Hook 执行结果"""

    CONTINUE = "continue"
    SKIP = "skip"  # 仅 BEFORE_CALL: 跳过当前 handler


@dataclass
class HookContext:
    """Hook 执行上下文"""

    event: "Event"
    event_type: str
    handler_entry: "HandlerEntry"
    api: "IBotAPI"
    services: Optional["ServiceManager"] = None
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None


class Hook(ABC):
    """
    Hook 基类

    Hook 实例既是执行器又是装饰器:
    - 装饰器: @hook_instance → 同步 __call__(func) → setattr func.__hooks__
    - 执行器: await hook.execute(ctx) → 异步执行 hook 逻辑

    子类必须:
    - 设置 stage 类属性
    - 实现 execute 方法
    """

    name: str = ""
    stage: HookStage = HookStage.BEFORE_CALL
    priority: int = 0  # 同 stage 内越大越先执行

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "stage", None) and cls is not Hook:
            raise TypeError(f"{cls.__name__} 必须定义 stage 属性")

    def __call__(self, func: Callable) -> Callable:
        """装饰器模式: 将自身绑定到 func.__hooks__"""
        if not callable(func):
            raise TypeError(
                f"Hook.__call__ 仅用于装饰器模式，传入参数必须是 callable，"
                f"收到 {type(func)}"
            )
        if not hasattr(func, "__hooks__"):
            func.__hooks__ = []
        func.__hooks__.append(self)
        return func

    @abstractmethod
    async def execute(self, ctx: HookContext) -> HookAction:
        """Hook 执行逻辑 (异步)，子类必须实现"""
        ...

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}"
            f"(stage={self.stage.value}, priority={self.priority})>"
        )


def add_hooks(*hooks: Hook) -> Callable:
    """批量为 handler 添加多个 Hook"""

    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "__hooks__"):
            func.__hooks__ = []
        for hook in hooks:
            func.__hooks__.append(hook)
        return func

    return decorator


def get_hooks(func: Callable, stage: Optional[HookStage] = None) -> List[Hook]:
    """获取函数上绑定的 hooks，按 priority 降序排列"""
    hooks: List[Hook] = getattr(func, "__hooks__", [])
    if stage is not None:
        hooks = [h for h in hooks if h.stage == stage]
    return sorted(hooks, key=lambda h: -h.priority)
