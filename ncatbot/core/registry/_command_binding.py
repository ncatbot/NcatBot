"""
命令参数绑定共享模块 — CommandHook / CommandGroupHook 共用

核心流程:
1. preprocess_segments: 将消息段列表重排（首个 PlainText 移到最前）
2. tokenize_text: shlex 分词，支持引号（双引号/单引号包裹的部分作为单个 token）
3. build_binding_stream: 将 segments + rest_text 转为有序的 (kind, value) 流
4. bind_params: 对 handler 的参数规格逐一从 stream 中匹配绑定
5. get_param_spec: 从函数签名解析参数规格
6. format_usage: 生成用法说明字符串
"""

from __future__ import annotations

import inspect
import shlex
from typing import Any, Dict, List, Optional, Tuple, get_type_hints

from ncatbot.utils import get_log

LOG = get_log("CommandBinding")


# ======================= 数据结构 =======================


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


# ======================= 类型判断 =======================


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


# ======================= 消息预处理 =======================


def preprocess_segments(message: Any) -> List[Any]:
    """将消息段列表重排: 找到第一个 PlainText 段移到 index 0, 其余保持原序。

    解决 Reply 开头的消息（如 ``[Reply, At(bot), Text("/ban"), ...]``）
    导致命令匹配失败的问题。

    返回段列表的副本，不修改原消息。
    """
    from ncatbot.types.common.segment.text import PlainText

    segments = list(message)  # MessageArray 支持 __iter__
    if not segments:
        return segments

    # 如果首段已是 PlainText，无需重排
    if isinstance(segments[0], PlainText):
        return segments

    # 找到第一个 PlainText
    for i, seg in enumerate(segments):
        if isinstance(seg, PlainText):
            first_text = segments.pop(i)
            return [first_text] + segments

    # 无 PlainText，原样返回
    return segments


# ======================= 分词 =======================


def tokenize_text(text: str) -> List[str]:
    """对文本进行分词，支持引号。

    使用 ``shlex.split(posix=True)``：
    - ``"hello world"`` → 单个 token ``hello world``
    - ``'hello world'`` → 单个 token ``hello world``

    shlex 解析异常（如未闭合引号）时 fallback 到 ``str.split()``。
    """
    if not text:
        return []
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


# ======================= Binding Stream =======================

# Stream 条目: (kind, value)
# kind = "token" | "at" | 其他段类型名（如 "image", "reply" 等）
StreamItem = Tuple[str, Any]


def build_binding_stream(
    segments: List[Any],
    rest_text: str,
) -> List[StreamItem]:
    """将预处理后的段列表（跳过首个已匹配命令的 PlainText）转为 binding stream。

    Args:
        segments: 预处理后的段列表（首段为已匹配命令的 PlainText，已跳过）
        rest_text: 首个 PlainText 中命令名之后的剩余文本

    返回有序的 ``(kind, value)`` 列表:
    - PlainText 段 → tokenize 后每个 token 产生 ``("token", str)``
    - At 段 → ``("at", At)``
    - 其他段 → ``(segment._type, segment)``
    """
    from ncatbot.types.common.segment.text import PlainText, At

    stream: List[StreamItem] = []

    # 1) 首段 PlainText 的剩余文本
    for token in tokenize_text(rest_text):
        stream.append(("token", token))

    # 2) 后续段（从 index 1 开始，因为 index 0 是已匹配命令的 PlainText）
    for seg in segments[1:]:
        if isinstance(seg, PlainText):
            for token in tokenize_text(seg.text):
                stream.append(("token", token))
        elif isinstance(seg, At):
            stream.append(("at", seg))
        else:
            seg_type = getattr(seg, "_type", type(seg).__name__)
            stream.append((seg_type, seg))

    return stream


# ======================= 参数绑定 =======================


def bind_params(
    spec: _ParamSpec,
    stream: List[StreamItem],
    *,
    skip_names: Optional[set] = None,
) -> Optional[Dict[str, Any]]:
    """根据参数规格从 binding stream 中逐项绑定。

    对每个 handler 参数，从当前 stream 位置向前扫描:
    - At 注解 → 匹配 kind="at" 的项
    - int/float → 匹配 kind="token" 的项，尝试类型转换
    - str (非最后) → 匹配 kind="token" 的项
    - str (最后) → 收集剩余所有 kind="token" 的项

    不匹配的 stream 项被跳过（永久消耗）。

    Args:
        spec: 参数规格
        stream: binding stream
        skip_names: 跳过的参数名集合（如 "subcommand"）

    Returns:
        成功 → kwargs dict; 必选参数缺失 → None
    """
    from ncatbot.types import At

    kwargs: Dict[str, Any] = {}
    pos = 0  # stream 当前位置

    for i, param in enumerate(spec.params):
        if skip_names and param.name in skip_names:
            if param.has_default:
                kwargs[param.name] = param.default
            continue

        anno = param.annotation
        is_last_str = i == len(spec.params) - 1 and _is_type(anno, str)

        if _is_type(anno, At):
            # At 参数 → 扫描 stream 找 kind="at"
            found = False
            while pos < len(stream):
                kind, value = stream[pos]
                pos += 1
                if kind == "at":
                    kwargs[param.name] = value
                    found = True
                    break
                # 跳过非 at 项（永久消耗）
            if not found:
                if param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

        elif _is_type(anno, int) or _is_type(anno, float):
            target_type = int if _is_type(anno, int) else float
            found = False
            while pos < len(stream):
                kind, value = stream[pos]
                pos += 1
                if kind == "token":
                    try:
                        kwargs[param.name] = target_type(value)
                        found = True
                        break
                    except (ValueError, TypeError):
                        pass  # 跳过不可转换的 token（永久消耗）
                # 跳过非 token 项（永久消耗）
            if not found:
                if param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

        elif _is_type(anno, str) or anno is inspect.Parameter.empty:
            if is_last_str:
                # 最后一个 str 参数 → 收集剩余所有 token
                collected: List[str] = []
                while pos < len(stream):
                    kind, value = stream[pos]
                    pos += 1
                    if kind == "token":
                        collected.append(value)
                    # 跳过非 token 项
                if collected:
                    kwargs[param.name] = " ".join(collected)
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None
            else:
                # 非最后 str → 扫描找第一个 token
                found = False
                while pos < len(stream):
                    kind, value = stream[pos]
                    pos += 1
                    if kind == "token":
                        kwargs[param.name] = value
                        found = True
                        break
                    # 跳过非 token 项
                if not found:
                    if param.has_default:
                        kwargs[param.name] = param.default
                    else:
                        return None

        else:
            # 未识别类型，尝试作为 str 处理
            found = False
            while pos < len(stream):
                kind, value = stream[pos]
                pos += 1
                if kind == "token":
                    kwargs[param.name] = value
                    found = True
                    break
            if not found:
                if param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

    return kwargs


# ======================= 参数规格解析 =======================


def get_param_spec(func: Any) -> _ParamSpec:
    """从函数签名解析参数规格（跳过 self/cls + event 参数）。

    不含缓存逻辑，调用方自行缓存。
    """
    try:
        sig = inspect.signature(func)
        try:
            hints = get_type_hints(func)
        except Exception:
            hints = {}

        params_list = list(sig.parameters.values())

        # 跳过 self/cls 和 event 参数
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
            return _ParamSpec(params=[])

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

        return _ParamSpec(params=params)

    except (ValueError, TypeError):
        return _ParamSpec(params=[])


# ======================= Usage 格式化 =======================

_TYPE_DISPLAY = {
    "At": "@用户",
    "int": "整数",
    "float": "小数",
    "str": "文本",
}


def format_usage(names: tuple, spec: _ParamSpec) -> str:
    """生成命令用法说明字符串。

    示例: ``用法: /ban <target: @用户> [duration: 整数 = 60]``
    """
    cmd = names[0]
    parts = [f"用法: {cmd}"]
    for param in spec.params:
        anno = param.annotation
        if anno is inspect.Parameter.empty:
            type_name = "文本"
        elif isinstance(anno, type):
            type_name = _TYPE_DISPLAY.get(anno.__name__, anno.__name__)
        elif isinstance(anno, str):
            type_name = _TYPE_DISPLAY.get(anno, anno)
        else:
            type_name = str(anno)

        if param.has_default:
            parts.append(f"[{param.name}: {type_name} = {param.default!r}]")
        else:
            parts.append(f"<{param.name}: {type_name}>")

    return " ".join(parts)


# ======================= Usage 回复 =======================


async def reply_usage(ctx: Any, names: tuple, spec: _ParamSpec) -> None:
    """尝试通过平台 API 回复命令用法说明。

    静默处理: api 不可用或调用失败时仅记录 WARNING。
    """
    usage = format_usage(names, spec)
    api = getattr(ctx, "api", None)
    if api is None:
        return

    try:
        data = ctx.event.data
        message_type = getattr(data, "message_type", None)
        msg_payload = [{"type": "text", "data": {"text": usage}}]

        if message_type == "group":
            group_id = getattr(data, "group_id", None)
            if group_id and hasattr(api, "qq"):
                await api.qq.send_group_msg(group_id, msg_payload)
        elif message_type == "private":
            user_id = getattr(data, "user_id", None)
            if user_id and hasattr(api, "qq"):
                await api.qq.send_private_msg(user_id, msg_payload)
    except Exception as e:
        LOG.warning("回复命令用法失败: %s", e)


# ======================= 命令匹配 =======================


def match_command_prefix(
    text: str,
    names: tuple,
    ignore_case: bool,
) -> Optional[str]:
    """统一前缀匹配: 对 text 进行 tokenize, 首 token 匹配命令名即触发。

    Returns:
        匹配的命令名, 或 None
    """
    tokens = tokenize_text(text)
    if not tokens:
        return None

    first_token = tokens[0].lower() if ignore_case else tokens[0]
    for name in names:
        compare_name = name.lower() if ignore_case else name
        if first_token == compare_name:
            return name
    return None
