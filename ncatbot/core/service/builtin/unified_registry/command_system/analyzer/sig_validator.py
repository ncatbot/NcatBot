"""签名验证器

验证命令函数签名是否符合要求。
"""

import inspect
from ncatbot.utils import get_log
from ..utils import FuncSpec

LOG = get_log(__name__)


class SigValidator:
    """函数签名验证器"""

    def __init__(self, descriptor: FuncSpec):
        self.descriptor = descriptor
        self.event_param_index = 0

    def analyze_signature(self):
        """分析函数签名，获取实际参数列表。

        Returns:
            tuple: (实际参数起始索引, 实际参数列表)

        Raises:
            ValueError: 当签名不符合要求时
        """
        # 延迟导入避免循环引用
        from ncatbot.core.event import MessageEvent

        if len(self.descriptor.param_list) < 1:
            self._raise_error("函数参数不足", "需要至少包含 event 参数")

        first_param = self.descriptor.param_list[0]

        # 形态一：实例方法 (self, event: MessageEvent, ...)
        if first_param.name == "self":
            if len(self.descriptor.param_list) < 2:
                self._raise_error("函数参数不足", "需要包含 event 参数")
            event_param = self.descriptor.param_list[1]
            self.event_param_index = 1
        else:
            # 形态二：普通/静态方法 (event: MessageEvent, ...)
            event_param = first_param
            self.event_param_index = 0

        # 验证 event 参数
        self._validate_event_param(event_param, MessageEvent)

        # 返回实际参数的起始索引与切片
        return (
            self.event_param_index + 1,
            self.descriptor.param_list[self.event_param_index + 1 :],
        )

    def _validate_event_param(self, event_param: inspect.Parameter, expected_type):
        """验证 event 参数的类型注解"""
        param_name = event_param.name

        # 检查是否有注解
        if event_param.annotation == inspect.Parameter.empty:
            self._raise_error(
                "event 参数缺少类型注解",
                f"参数 '{param_name}' 需要 MessageEvent 或其子类注解",
            )

        # 检查注解是否正确
        annotation = event_param.annotation
        if not (isinstance(annotation, type) and issubclass(annotation, expected_type)):
            self._raise_error(
                "event 参数类型注解错误",
                f"参数 '{param_name}' 注解为 {annotation}，需要 MessageEvent 或其子类",
            )

    def _raise_error(self, error_type: str, detail: str):
        """统一的错误处理"""
        func_qualname = self.descriptor.func_qualname
        func_location = f"{self.descriptor.func_module}.{func_qualname}"
        message = f"{error_type}: {func_qualname} {detail}"

        LOG.error(message)
        LOG.info(f"函数来自 {func_location}")
        raise ValueError(message)
