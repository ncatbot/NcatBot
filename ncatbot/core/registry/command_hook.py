"""
CommandHook — 命令匹配 + 注解式参数绑定

高级 BEFORE_CALL Hook:
1. 预处理消息段：将首个 PlainText 移到 index 0
2. 使用 shlex 分词后的首 token 统一前缀匹配命令名
3. 构建 binding stream：命令后剩余文本 + 后续段
4. 从 binding stream 中按类型注解逐项绑定 (str/int/float/At)
5. 支持引号（双引号/单引号包裹部分作为单个 token）
6. 不匹配的段被跳过（永久消耗）
7. 必选参数缺失时 WARNING + 回复 usage + SKIP
8. 写入 ctx.kwargs → dispatcher._execute(**ctx.kwargs) 自动注入
"""

from typing import Dict, Optional

from ncatbot.utils import get_log

from .hook import Hook, HookAction, HookContext, HookStage
from ._command_binding import (
    _ParamSpec,
    preprocess_segments,
    build_binding_stream,
    bind_params,
    get_param_spec,
    reply_usage,
    match_command_prefix,
)

LOG = get_log("CommandHook")


class CommandHook(Hook):
    """命令匹配 + 注解式参数绑定

    匹配规则:
    - 统一前缀匹配 — 对消息预处理后首段 PlainText 分词,
      首 token 匹配命令名即触发（无论 handler 有无额外参数）

    参数绑定规则:
    - 消息段预处理: 首个 PlainText 移到最前, 解决 Reply 开头的消息
    - 引号支持: ``"hello world"`` 作为单个 token
    - At 注解 → 从 binding stream 中匹配 kind="at" 的项
    - int/float → 从 binding stream 中匹配 kind="token" 并转换
    - str → 单 token 或剩余全部文本 (最后一个 str 参数)
    - 不匹配的段被跳过（永久消耗, 不再参与后续参数匹配）
    - 有默认值 → 可选; 必选参数缺失 → WARNING + 回复 usage + SKIP
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
        self._sig_cache: Dict[int, Optional[_ParamSpec]] = {}

    async def execute(self, ctx: HookContext) -> HookAction:
        # 获取消息
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP

        # 1) 预处理: 首个 PlainText 移到最前
        segments = preprocess_segments(message)
        if not segments:
            return HookAction.SKIP

        # 2) 从首段 PlainText 取文本
        from ncatbot.types.common.segment.text import PlainText

        first_seg = segments[0]
        if not isinstance(first_seg, PlainText):
            return HookAction.SKIP

        text = first_seg.text.strip()
        if not text:
            return HookAction.SKIP

        # 3) 统一前缀匹配: tokenize 后首 token 匹配命令名
        matched_name = match_command_prefix(text, self.names, self.ignore_case)
        if matched_name is None:
            return HookAction.SKIP

        # 4) 解析 handler 参数规格 (缓存)
        func = ctx.handler_entry.func
        spec = self._get_param_spec(func)

        if spec is None or not spec.params:
            # 无额外参数 → 命令已匹配, 直接 CONTINUE
            return HookAction.CONTINUE

        # 5) 提取命令后的剩余文本
        # 从原文中跳过命令名部分
        # 因为 shlex 可能改变 token 内容（去掉引号），这里用原文尝试匹配
        rest_text = text
        compare_text = text.lower() if self.ignore_case else text
        compare_name = matched_name.lower() if self.ignore_case else matched_name
        if compare_text.startswith(compare_name):
            rest_text = text[len(matched_name) :].strip()
        else:
            rest_text = ""

        # 6) 构建 binding stream
        stream = build_binding_stream(segments, rest_text)

        # 7) 绑定参数
        kwargs = bind_params(spec, stream)
        if kwargs is None:
            # 必选参数缺失 → WARNING + 回复 usage + SKIP
            LOG.warning(
                "命令 %s 必选参数未绑定 (handler=%s)",
                matched_name,
                func.__name__,
            )
            await reply_usage(ctx, self.names, spec)
            return HookAction.SKIP

        ctx.kwargs.update(kwargs)
        return HookAction.CONTINUE

    def _get_param_spec(self, func) -> Optional[_ParamSpec]:
        """解析并缓存 handler 的参数规格"""
        func_id = id(func)
        if func_id in self._sig_cache:
            return self._sig_cache[func_id]

        spec = get_param_spec(func)
        self._sig_cache[func_id] = spec
        return spec

    def __repr__(self) -> str:
        return f"<CommandHook(names={self.names!r}, ignore_case={self.ignore_case})>"
