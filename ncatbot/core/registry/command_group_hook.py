"""
CommandGroupHook — 命令组匹配与自动路由

高级 BEFORE_CALL Hook:
1. 预处理消息段：将首个 PlainText 移到 index 0
2. 支持多命令名，命令后可跟子命令和参数（格式：command subcommand [args...]）
3. 使用 shlex 分词后的首 token 统一前缀匹配命令名
4. 支持子命令管理：handler 参数中包含 subcommand 参数，自动提取并路由
5. 构建 binding stream: 命令/子命令后剩余文本 + 后续段
6. 从 binding stream 中按类型注解逐项绑定 (str/int/float/At)
7. 支持引号（双引号/单引号包裹部分作为单个 token）
8. 不匹配的段被跳过（永久消耗）
9. 写入 ctx.kwargs → dispatcher._execute(**ctx.kwargs) 自动注入

使用示例（与 CommandHook 一致）:

    # 定义处理器，声明子命令参数
    hook = CommandGroupHook("admin", "/admin", "a")

    @hook.subcommand("ban", "禁言")
    async def admin_ban(event: GroupMessageEvent, user_id: int, minutes: int = 60):
        # 处理 "/admin ban 12345", "/admin ban 12345 120"
        pass

    @hook.subcommand("kick")
    async def admin_kick(event: GroupMessageEvent, user_id: int):
        # 处理 "/admin kick 12345"
        pass

    @registrar.on_message("message.group")
    @hook
    @group_only
    async def handle_admin(event: GroupMessageEvent, subcommand: str = ""):
        # 当命令匹配时，subcommand 自动填充对应的子命令名
        # 如果有对应的 @hook.subcommand() 处理，该处理器先被调用
        pass
"""

from typing import Any, Dict, List, Optional

from .hook import Hook, HookAction, HookContext, HookStage
from ._command_binding import (
    _ParamSpec,
    preprocess_segments,
    tokenize_text,
    build_binding_stream,
    bind_params,
    get_param_spec,
    match_command_prefix,
)


class CommandGroup:
    """命令组 — 为向后兼容而保留（建议改用 CommandGroupHook 的 @subcommand()）

    管理子命令/子命令组的容器。
    """

    def __init__(self, names: List[str]):
        """
        Args:
            names: 该命令组的名称列表 (别名), e.g. ["help", "h"]
        """
        if not names:
            raise ValueError("CommandGroup 至少需要一个名称")
        self.names = names
        self.subcommands: Dict[str, Any] = {}  # 子命令名 → handler
        self.subgroups: Dict[str, "CommandGroup"] = {}  # 子命令组名 → CommandGroup

    def command(self, *names: str):
        """子命令注册装饰器"""

        def decorator(func):
            for name in names:
                self.subcommands[name.lower()] = func
            return func

        return decorator

    def subgroup(self, group: "CommandGroup"):
        """注册子命令组"""
        for name in group.names:
            self.subgroups[name.lower()] = group
        return group

    def __repr__(self) -> str:
        return f"<CommandGroup(names={self.names!r})>"


class CommandGroupHook(Hook):
    """命令匹配 + 子命令路由 Hook

    与 CommandHook 基本一致，额外支持子命令注册和自动路由。

    使用示例:

        hook = CommandGroupHook("admin", "/admin", "a")

        @hook.subcommand("ban")
        async def admin_ban(event: GroupMessageEvent, user_id: int, minutes: int = 60):
            pass

        @hook.subcommand("kick", "remove")
        async def admin_kick(event: GroupMessageEvent, user_id: int):
            pass

        @registrar.on_message("message.group")
        @hook
        @group_only
        async def handle_admin(event: GroupMessageEvent, subcommand: str = ""):
            pass

    用法:
        /admin ban 12345       → 调用 admin_ban(event, 12345, 60)
        /admin ban 12345 120   → 调用 admin_ban(event, 12345, 120)
        /admin kick 12345      → 调用 admin_kick(event, 12345)
    """

    stage = HookStage.BEFORE_CALL

    def __init__(
        self,
        *names: str,
        ignore_case: bool = False,
        priority: int = 95,
    ):
        """
        Args:
            *names: 命令名列表（支持别名), e.g. "admin", "/admin", "a"
            ignore_case: 是否忽略大小写匹配
            priority: hook 优先级
        """
        if not names:
            raise ValueError("CommandGroupHook 至少需要一个命令名")
        self.names = names
        self.ignore_case = ignore_case
        self.priority = priority
        self._subcommands: Dict[str, Any] = {}  # 子命令名 → handler
        self._sig_cache: Dict[int, Optional[_ParamSpec]] = {}

    def subcommand(self, *subcommand_names: str):
        """子命令注册装饰器

        Args:
            *subcommand_names: 子命令名称（支持别名）
        """

        def decorator(func):
            for name in subcommand_names:
                compare_name = name.lower() if self.ignore_case else name
                self._subcommands[compare_name] = func
            return func

        return decorator

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

        # 解析 handler 参数规格 (缓存)
        func = ctx.handler_entry.func
        spec = self._get_param_spec(func)

        # 提取命令后的剩余文本
        compare_text = text.lower() if self.ignore_case else text
        compare_name = matched_name.lower() if self.ignore_case else matched_name
        if compare_text.startswith(compare_name):
            rest = text[len(matched_name) :].strip()
        else:
            rest = ""

        # 尝试匹配子命令
        if rest:
            rest_tokens = tokenize_text(rest)
            if rest_tokens:
                first_token = rest_tokens[0]
                compare_first = first_token.lower() if self.ignore_case else first_token

                # 查找注册的子命令
                if compare_first in self._subcommands:
                    subcommand_handler = self._subcommands[compare_first]
                    # 绑定子命令处理器的参数
                    subcommand_spec = self._get_param_spec(subcommand_handler)
                    if subcommand_spec:
                        # 子命令后的剩余文本
                        # 从原始 rest 中跳过子命令 token
                        sub_rest = rest
                        if (
                            sub_rest.lower().startswith(first_token.lower())
                            if self.ignore_case
                            else sub_rest.startswith(first_token)
                        ):
                            sub_rest = sub_rest[len(first_token) :].strip()
                        else:
                            sub_rest = ""
                        stream = build_binding_stream(segments, sub_rest)
                        kwargs = bind_params(
                            subcommand_spec, stream, skip_names={"subcommand"}
                        )
                        if kwargs is not None:
                            ctx.kwargs.update(kwargs)
                            return HookAction.CONTINUE

        # 没有子命令匹配，检查是否是精确命令匹配（无rest）
        if not rest:
            return HookAction.CONTINUE

        # 如果有rest但没有子命令，尝试绑定主handler的参数
        if spec and spec.params:
            stream = build_binding_stream(segments, rest)
            kwargs = bind_params(spec, stream, skip_names={"subcommand"})
            if kwargs is None:
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
        return (
            f"<CommandGroupHook(names={self.names!r}, "
            f"subcommands={list(self._subcommands.keys())!r}, "
            f"ignore_case={self.ignore_case})>"
        )
