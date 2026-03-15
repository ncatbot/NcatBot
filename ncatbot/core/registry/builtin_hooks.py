"""
内置 Hook 集合

提供常用的 BEFORE_CALL 过滤 Hook，用于事件类型筛选等。

事件字段通过 event.data 访问（Event.data: BaseEventData，extra="allow"）。
"""

from .hook import Hook, HookAction, HookContext, HookStage


class MessageTypeFilter(Hook):
    """过滤消息类型 (group / private)

    通过 event.data.message_type 判断。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, message_type: str, *, priority: int = 100):
        self.message_type = message_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        mt = getattr(ctx.event.data, "message_type", None)
        if mt is not None and hasattr(mt, "value"):
            mt = mt.value
        if mt != self.message_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<MessageTypeFilter(type={self.message_type})>"


class PostTypeFilter(Hook):
    """过滤 post_type (message / notice / request / meta_event)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, post_type: str, *, priority: int = 100):
        self.post_type = post_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        pt = getattr(ctx.event.data, "post_type", None)
        if pt is not None and hasattr(pt, "value"):
            pt = pt.value
        if pt != self.post_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<PostTypeFilter(type={self.post_type})>"


class SubTypeFilter(Hook):
    """过滤 sub_type"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, sub_type: str, *, priority: int = 100):
        self.sub_type = sub_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        st = getattr(ctx.event.data, "sub_type", None)
        if st is not None and hasattr(st, "value"):
            st = st.value
        if st != self.sub_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<SubTypeFilter(type={self.sub_type})>"


class SelfFilter(Hook):
    """跳过 bot 自身发出的消息 (self_id == user_id)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, *, priority: int = 200):
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        data = ctx.event.data
        self_id = getattr(data, "self_id", None)
        user_id = getattr(data, "user_id", None)
        if self_id and user_id and str(self_id) == str(user_id):
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return "<SelfFilter>"


# 预实例化常用 Hook
group_only = MessageTypeFilter("group")
private_only = MessageTypeFilter("private")
non_self = SelfFilter()


# ==================== 文本匹配 Hook ====================
# 所有文本匹配类 Hook 使用 event.data.message.text (MessageArray 结构化文本)


class StartsWithHook(Hook):
    """前缀匹配 (纯过滤，不做参数绑定)

    使用 message.text 而非 raw_message。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, prefix: str, *, priority: int = 90):
        self.prefix = prefix
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP
        text = message.text.strip() if hasattr(message, "text") else ""
        if not text.startswith(self.prefix):
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<StartsWithHook(prefix={self.prefix!r})>"


class KeywordHook(Hook):
    """关键词包含匹配 (任一关键词命中即通过)

    使用 message.text 而非 raw_message。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, *words: str, priority: int = 90):
        self.words = words
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP
        text = message.text if hasattr(message, "text") else ""
        for word in self.words:
            if word in text:
                return HookAction.CONTINUE
        return HookAction.SKIP

    def __repr__(self) -> str:
        return f"<KeywordHook(words={self.words!r})>"


class RegexHook(Hook):
    """正则匹配 + 绑定 match 对象到 ctx.kwargs['match']

    使用 message.text 而非 raw_message。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, pattern: str, flags: int = 0, *, priority: int = 90):
        import re

        self.pattern = re.compile(pattern, flags)
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP
        text = message.text if hasattr(message, "text") else ""
        m = self.pattern.search(text)
        if m is None:
            return HookAction.SKIP
        ctx.kwargs["match"] = m
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<RegexHook(pattern={self.pattern.pattern!r})>"


class NoticeTypeFilter(Hook):
    """过滤通知子类型 (notice_type)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, notice_type: str, *, priority: int = 100):
        self.notice_type = notice_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        nt = getattr(ctx.event.data, "notice_type", None)
        if nt is not None and hasattr(nt, "value"):
            nt = nt.value
        if nt != self.notice_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<NoticeTypeFilter(type={self.notice_type})>"


class RequestTypeFilter(Hook):
    """过滤请求子类型 (request_type)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, request_type: str, *, priority: int = 100):
        self.request_type = request_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        rt = getattr(ctx.event.data, "request_type", None)
        if rt is not None and hasattr(rt, "value"):
            rt = rt.value
        if rt != self.request_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<RequestTypeFilter(type={self.request_type})>"


# 工厂函数 (小写，方便用户使用)


def startswith(prefix: str, *, priority: int = 90) -> StartsWithHook:
    """创建前缀匹配 Hook"""
    return StartsWithHook(prefix, priority=priority)


def keyword(*words: str, priority: int = 90) -> KeywordHook:
    """创建关键词匹配 Hook"""
    return KeywordHook(*words, priority=priority)


def regex(pattern: str, flags: int = 0, *, priority: int = 90) -> RegexHook:
    """创建正则匹配 Hook"""
    return RegexHook(pattern, flags, priority=priority)
