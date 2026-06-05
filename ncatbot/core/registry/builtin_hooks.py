"""
内置 Hook 集合

提供常用的 BEFORE_CALL 过滤 Hook，用于事件类型筛选等。

事件字段通过 event.data 访问（Event.data: BaseEventData，extra="allow"）。
"""

import re
import time
from collections import deque
from typing import Callable, Optional, Union

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


class AtFilter(Hook):
    """仅当消息 @了机器人时才放行。

    通过 ``event.data.message`` 中的 ``At`` 段检测。
    仅对消息事件生效（无 message 字段时放行）。

    参数:
        include_at_all: 是否把 @全体成员 也算作 @机器人（默认 False）
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, *, include_at_all: bool = False, priority: int = 150):
        self.include_at_all = include_at_all
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        data = ctx.event.data
        message = getattr(data, "message", None)
        self_id = getattr(data, "self_id", None)

        # 非消息事件（无 message 字段），放行
        if message is None or self_id is None:
            return HookAction.CONTINUE

        if not hasattr(message, "filter_at"):
            return HookAction.CONTINUE

        for at in message.filter_at():
            if at.user_id == str(self_id):
                return HookAction.CONTINUE
            if self.include_at_all and at.user_id == "all":
                return HookAction.CONTINUE

        return HookAction.SKIP

    def __repr__(self) -> str:
        return f"<AtFilter(include_at_all={self.include_at_all})>"


class PlatformFilter(Hook):
    """过滤事件平台 (qq / telegram / ...)

    通过 event.platform 或 event.data.platform 判断。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, platform: str, *, priority: int = 200):
        self._platform = platform
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        p = getattr(ctx.event, "platform", None)
        if p is None:
            p = getattr(ctx.event.data, "platform", None)
        if p != self._platform:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<PlatformFilter(platform={self._platform})>"


# 预实例化常用 Hook
group_only = MessageTypeFilter("group")
private_only = MessageTypeFilter("private")
non_self = SelfFilter()
require_at = AtFilter()


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


# ==================== 速率限制 Hook ====================


class RateLimitHook(Hook):
    """滑动窗口速率限制

    在 ``period`` 秒内最多允许 ``max_calls`` 次调用，超限返回 SKIP。

    ``key`` 决定限流粒度:
    - ``"user"``        → 按 user_id 独立计数
    - ``"group"``       → 按 group_id 独立计数
    - ``"user_group"``  → 按 user_id:group_id 独立计数
    - ``"global"``      → 所有请求共享配额
    - ``Callable[[HookContext], Optional[str]]`` → 自定义 key 提取函数

    key 提取结果为 None 时放行（CONTINUE）。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(
        self,
        max_calls: int,
        period: float,
        *,
        key: Union[str, Callable[["HookContext"], Optional[str]]] = "user",
        priority: int = 80,
    ):
        self.max_calls = max_calls
        self.period = period
        self._key = key
        self.priority = priority
        self._windows: dict[str, deque[float]] = {}

    def _extract_key(self, ctx: "HookContext") -> Optional[str]:
        if callable(self._key):
            return self._key(ctx)
        data = ctx.event.data
        if self._key == "user":
            uid = getattr(data, "user_id", None)
            return str(uid) if uid is not None else None
        if self._key == "group":
            gid = getattr(data, "group_id", None)
            return str(gid) if gid is not None else None
        if self._key == "user_group":
            uid = getattr(data, "user_id", None)
            gid = getattr(data, "group_id", None)
            if uid is None or gid is None:
                return None
            return f"{uid}:{gid}"
        if self._key == "global":
            return "__global__"
        return None

    async def execute(self, ctx: "HookContext") -> HookAction:
        k = self._extract_key(ctx)
        if k is None:
            return HookAction.CONTINUE

        now = time.monotonic()
        window = self._windows.get(k)
        if window is None:
            window = deque()
            self._windows[k] = window

        # 清除过期时间戳
        cutoff = now - self.period
        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= self.max_calls:
            return HookAction.SKIP

        window.append(now)
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return (
            f"<RateLimitHook(max_calls={self.max_calls}, "
            f"period={self.period}, key={self._key!r})>"
        )


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


def rate_limit(
    max_calls: int,
    period: float,
    *,
    key: Union[str, Callable[["HookContext"], Optional[str]]] = "user",
    priority: int = 80,
) -> RateLimitHook:
    """创建速率限制 Hook"""
    return RateLimitHook(max_calls, period, key=key, priority=priority)
