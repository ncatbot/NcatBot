"""参数绑定器

将解析后的消息元素绑定到命令函数参数。
"""

import inspect
from dataclasses import dataclass
from typing import Tuple, List, Any, Dict, Optional, TYPE_CHECKING

from ..command_system.utils import CommandSpec
from ncatbot.utils import get_log
from ..command_system.lexer.message_tokenizer import MessageTokenizer

if TYPE_CHECKING:
    from ncatbot.core import MessageEvent

LOG = get_log(__name__)


class InvalidOptionError(Exception):
    """无效选项错误"""

    def __init__(self, option_name: str):
        self.option_name = option_name
        super().__init__(f"选项 '{option_name}' 无效")


class InvalidParamError(Exception):
    """无效参数错误"""

    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"参数 '{param_name}' 无效")


class MissingArgumentError(Exception):
    """缺少参数错误"""

    def __init__(self, required: int, actual: int):
        self.required = required
        self.actual = actual
        super().__init__(f"参数不足：需要 {required} 个，实际传入 {actual} 个")


@dataclass
class BindResult:
    """绑定结果"""

    ok: bool
    args: Tuple  # 位置参数
    named_args: Dict[str, Any]  # 命名参数
    message: str = ""


class ArgumentBinder:
    """参数绑定器

    将解析后的消息元素绑定到命令函数参数。
    """

    def __init__(self):
        self._tokenizer = MessageTokenizer()

    def bind(
        self,
        spec: CommandSpec,
        event: "MessageEvent",
        path_words: Tuple[str, ...],
        prefixes: List[str],
    ) -> BindResult:
        """绑定参数

        Args:
            spec: 命令规格
            event: 消息事件
            path_words: 命令路径词
            prefixes: 命令前缀列表

        Returns:
            BindResult: 绑定结果

        Raises:
            InvalidOptionError: 选项无效
            InvalidParamError: 参数无效
            MissingArgumentError: 缺少必需参数
        """
        try:
            # 解析消息
            parsed = self._tokenizer.parse_message(event.message)
            elements = list(parsed.elements)

            # 跳过命令词
            skip_idx = self._skip_command_words(elements, path_words, prefixes)

            # 验证参数数量
            self._validate_arg_count(spec, elements, skip_idx)

            # 绑定命名参数和选项
            bound_kwargs = self._bind_named_args(spec, parsed.named_params)
            bound_kwargs.update(self._bind_options(spec, parsed.options))

            # 绑定位置参数
            remaining_elements = elements[skip_idx:]
            bound_args = self._bind_positional_args(spec, remaining_elements)

            return BindResult(True, tuple(bound_args), bound_kwargs, "")
        except Exception as e:
            LOG.debug(f"绑定异常: {e}")
            raise

    def _skip_command_words(
        self, elements: List, path_words: Tuple[str, ...], prefixes: List[str]
    ) -> int:
        """跳过命令词，返回跳过后的索引"""
        skip_idx = 0
        pw = list(path_words)
        pw_idx = 0

        while skip_idx < len(elements) and pw_idx < len(pw):
            el = elements[skip_idx]
            content_str = el.content

            if el.type in ("text", "plaintext"):
                # 完全匹配或带前缀匹配
                if content_str == pw[pw_idx]:
                    skip_idx += 1
                    pw_idx += 1
                elif (
                    len(content_str) > 0
                    and content_str[0] in prefixes
                    and content_str[1:].startswith(pw[pw_idx])
                ):
                    skip_idx += 1
                    pw_idx += 1
                else:
                    break
            else:
                break

        LOG.debug(f"跳过索引: {skip_idx}")
        return skip_idx

    def _validate_arg_count(
        self, spec: CommandSpec, elements: List, skip_idx: int
    ) -> None:
        """验证参数数量"""
        actual_args_count = len(elements[skip_idx:])
        sig = inspect.signature(spec.func)

        required_args = [
            name
            for name, param in sig.parameters.items()
            if param.default is inspect.Parameter.empty
            and param.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        # 减去 self/cls 和 event 参数
        required_args_count = len(required_args) - 2
        if actual_args_count < required_args_count:
            raise MissingArgumentError(required_args_count, actual_args_count)

    def _bind_named_args(
        self, spec: CommandSpec, named_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """绑定命名参数"""
        bound_kwargs = {}

        for name, value in named_params.items():
            result = self._get_param_binding(spec, name, value)
            if result is None:
                raise InvalidParamError(name)
            bound_kwargs.update(result)

        return bound_kwargs

    def _bind_options(
        self, spec: CommandSpec, options: Dict[str, bool]
    ) -> Dict[str, Any]:
        """绑定选项"""
        bound_kwargs = {}

        for option_name in options:
            result = self._get_option_binding(spec, option_name)
            if result is None:
                raise InvalidOptionError(option_name)
            bound_kwargs.update(result)

        return bound_kwargs

    def _bind_positional_args(self, spec: CommandSpec, elements: List) -> List[Any]:
        """绑定位置参数"""
        bound_args = []
        param_types = spec.param_types

        for idx, element in enumerate(elements):
            content = element.content

            # 超出参数类型范围
            if idx >= len(param_types):
                # 如果最后一个参数是 str，合并剩余内容
                if param_types and param_types[-1] is str and bound_args:
                    bound_args[-1] = f"{bound_args[-1]} {content}"
                continue

            # 类型转换
            arg_type = param_types[idx]
            bound_args.append(self._convert_value(content, arg_type))

        return bound_args

    def _get_option_binding(
        self, spec: CommandSpec, option_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取选项绑定结果"""
        # 查找普通选项
        opt = spec.find_option(option_name)
        if opt:
            return {opt.name: True}

        # 查找选项组
        group = spec.find_option_group(option_name)
        if group:
            return {group.name: option_name}

        return None

    def _get_param_binding(
        self, spec: CommandSpec, param_name: str, value: Any
    ) -> Optional[Dict[str, Any]]:
        """获取参数绑定结果"""
        param = spec.find_param(param_name)
        if param is None:
            return None

        target_type = spec.get_param_type(param.index)
        if target_type is None:
            return {param.name: value}

        return {param.name: self._convert_value(value, target_type)}

    def _convert_value(self, value: Any, target_type: type) -> Any:
        """转换值到目标类型"""
        if target_type is bool:
            if isinstance(value, str):
                return value.lower() not in ["false", "0"]
            return bool(value)
        elif target_type in (str, float, int):
            return target_type(value)
        else:
            return value
