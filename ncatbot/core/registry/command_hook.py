"""
CommandHook — 命令匹配 + 注解式参数绑定

高级 BEFORE_CALL Hook:
1. 使用 message.text 匹配命令名 (精确匹配或前缀匹配)
2. 通过 inspect.signature 检查 handler 函数的类型注解
3. 从 MessageArray 结构化提取参数 (At 段、文本 token)
4. 按类型注解自动转换 (str/int/float/At)
5. 写入 ctx.kwargs → dispatcher._execute(**ctx.kwargs) 自动注入
"""

import inspect
from typing import Any, Dict, List, Optional, Tuple, get_type_hints

from .hook import Hook, HookAction, HookContext, HookStage


class CommandHook(Hook):
    """命令匹配 + 注解式参数绑定

    匹配规则:
    - handler 无额外参数 → 精确匹配命令名
    - handler 有额外参数 → 前缀匹配 + 自动绑定

    参数绑定规则:
    - At 注解 → 从 message.filter_at() 按序提取 At 对象
    - int/float → 从文本 token 提取并转换
    - str → 单 token 或剩余全部文本 (最后一个 str 参数)
    - 有默认值 → 可选; 必选参数缺失 → SKIP
    """

    stage = HookStage.BEFORE_CALL

    def __init__(
        self,
        *names: str,
        ignore_case: bool = False,
        priority: int = 95,
    ):
        if not names:
            raise ValueError("CommandHook 至少需要一个命令名")
        self.names = names
        self.ignore_case = ignore_case
        self.priority = priority
        self._sig_cache: Dict[int, Optional["_ParamSpec"]] = {}

    async def execute(self, ctx: HookContext) -> HookAction:
        # 获取消息文本
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP
        text = message.text.strip() if hasattr(message, "text") else ""
        if not text:
            return HookAction.SKIP

        compare_text = text.lower() if self.ignore_case else text

        # 解析 handler 参数规格 (缓存)
        func = ctx.handler_entry.func
        spec = self._get_param_spec(func)

        if spec is None or not spec.params:
            # 无额外参数 → 精确匹配
            for name in self.names:
                compare_name = name.lower() if self.ignore_case else name
                if compare_text == compare_name:
                    return HookAction.CONTINUE
            return HookAction.SKIP

        # 有额外参数 → 前缀匹配
        matched_name = None
        for name in self.names:
            compare_name = name.lower() if self.ignore_case else name
            if compare_text == compare_name or compare_text.startswith(
                compare_name + " "
            ):
                matched_name = name
                break

        if matched_name is None:
            return HookAction.SKIP

        # 提取命令后的文本
        if len(text) > len(matched_name):
            rest = text[len(matched_name) :].strip()
        else:
            rest = ""

        # 绑定参数
        kwargs = self._bind_params(spec, rest, message)
        if kwargs is None:
            return HookAction.SKIP  # 必选参数缺失

        ctx.kwargs.update(kwargs)
        return HookAction.CONTINUE

    def _get_param_spec(self, func) -> Optional["_ParamSpec"]:
        """解析并缓存 handler 的参数规格"""
        func_id = id(func)
        if func_id in self._sig_cache:
            return self._sig_cache[func_id]

        try:
            sig = inspect.signature(func)
            # 尝试获取类型提示 (处理 from __future__ import annotations)
            try:
                hints = get_type_hints(func)
            except Exception:
                hints = {}

            params_list = list(sig.parameters.values())

            # 跳过 self 和 event 参数
            skip = 0
            for p in params_list:
                if p.name in ("self", "cls"):
                    skip += 1
                    continue
                # 第一个非 self 参数是 event
                skip += 1
                break

            extra_params = params_list[skip:]
            if not extra_params:
                spec = _ParamSpec(params=[])
                self._sig_cache[func_id] = spec
                return spec

            params = []
            for p in extra_params:
                annotation = hints.get(p.name, p.annotation)
                has_default = p.default is not inspect.Parameter.empty
                params.append(
                    _ParamInfo(
                        name=p.name,
                        annotation=annotation,
                        has_default=has_default,
                        default=p.default if has_default else None,
                    )
                )

            spec = _ParamSpec(params=params)
            self._sig_cache[func_id] = spec
            return spec

        except (ValueError, TypeError):
            self._sig_cache[func_id] = _ParamSpec(params=[])
            return self._sig_cache[func_id]

    def _bind_params(
        self,
        spec: "_ParamSpec",
        rest: str,
        message: Any,
    ) -> Optional[Dict[str, Any]]:
        """根据参数规格绑定实际值，失败返回 None"""
        from ncatbot.types import At

        # 提取 At 列表和文本 token
        at_list: List[Any] = []
        if hasattr(message, "filter_at"):
            at_list = list(message.filter_at())

        text_tokens = rest.split() if rest else []

        kwargs: Dict[str, Any] = {}
        at_idx = 0
        token_idx = 0

        for i, param in enumerate(spec.params):
            anno = param.annotation
            is_last_str = i == len(spec.params) - 1 and _is_type(anno, str)

            if _is_type(anno, At):
                # At 参数 → 从 At 列表中按序提取
                if at_idx < len(at_list):
                    kwargs[param.name] = at_list[at_idx]
                    at_idx += 1
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None  # 必选 At 缺失

            elif _is_type(anno, int):
                # int → 从文本 token 提取
                value = self._extract_typed_token(text_tokens, token_idx, int)
                if value is not None:
                    kwargs[param.name] = value[0]
                    token_idx = value[1]
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

            elif _is_type(anno, float):
                value = self._extract_typed_token(text_tokens, token_idx, float)
                if value is not None:
                    kwargs[param.name] = value[0]
                    token_idx = value[1]
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

            elif _is_type(anno, str) or anno is inspect.Parameter.empty:
                if is_last_str:
                    # 最后一个 str 参数消费剩余全部文本
                    remaining = " ".join(text_tokens[token_idx:])
                    if remaining:
                        kwargs[param.name] = remaining
                        token_idx = len(text_tokens)
                    elif param.has_default:
                        kwargs[param.name] = param.default
                    else:
                        return None
                else:
                    # 非最后: 消费单个 token
                    if token_idx < len(text_tokens):
                        kwargs[param.name] = text_tokens[token_idx]
                        token_idx += 1
                    elif param.has_default:
                        kwargs[param.name] = param.default
                    else:
                        return None

            else:
                # 未识别类型，尝试 str
                if token_idx < len(text_tokens):
                    kwargs[param.name] = text_tokens[token_idx]
                    token_idx += 1
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

        return kwargs

    @staticmethod
    def _extract_typed_token(
        tokens: List[str], start_idx: int, target_type: type
    ) -> Optional[Tuple[Any, int]]:
        """从 tokens[start_idx:] 找到第一个可转换为 target_type 的 token"""
        for i in range(start_idx, len(tokens)):
            try:
                return (target_type(tokens[i]), i + 1)
            except (ValueError, TypeError):
                continue
        return None

    def __repr__(self) -> str:
        return f"<CommandHook(names={self.names!r}, ignore_case={self.ignore_case})>"


class _ParamInfo:
    """单个参数信息"""

    __slots__ = ("name", "annotation", "has_default", "default")

    def __init__(self, name: str, annotation: Any, has_default: bool, default: Any):
        self.name = name
        self.annotation = annotation
        self.has_default = has_default
        self.default = default


class _ParamSpec:
    """handler 的参数规格"""

    __slots__ = ("params",)

    def __init__(self, params: List[_ParamInfo]):
        self.params = params


def _is_type(annotation: Any, target: type) -> bool:
    """检查注解是否为指定类型 (处理字符串注解)"""
    if annotation is inspect.Parameter.empty:
        return False
    if annotation is target:
        return True
    if isinstance(annotation, type) and issubclass(annotation, target):
        return True
    if isinstance(annotation, str):
        return annotation == target.__name__
    return False
