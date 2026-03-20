"""
内置 Hook 扩展规范测试

规范:
  K-07: StartsWithHook 前缀匹配 (message.text)
  K-08: KeywordHook 关键词匹配
  K-09: RegexHook 正则匹配 + match 绑定
  K-10: NoticeTypeFilter 通知子类型过滤
  K-11: RequestTypeFilter 请求子类型过滤
  K-12: CommandHook 精确匹配 (无额外参数)
  K-13: CommandHook ignore_case
  K-14: CommandHook str 参数绑定
  K-15: CommandHook At 参数绑定
  K-16: CommandHook int/float 参数转换
  K-17: CommandHook 可选参数 (有默认值)
  K-18: CommandHook 必选参数缺失 → SKIP
  K-19: Registrar on_group_command 单装饰器
  K-20: Registrar on_group_increase 等便捷方法
  K-21: 文本匹配使用 message.text
"""

import re


from ncatbot.core.registry.hook import HookAction, HookContext
from ncatbot.core.registry.builtin_hooks import (
    StartsWithHook,
    KeywordHook,
    RegexHook,
    NoticeTypeFilter,
    RequestTypeFilter,
    startswith,
    keyword,
    regex,
)
from ncatbot.core.registry.command_hook import CommandHook
from ncatbot.core.registry.registrar import Registrar
from ncatbot.core.dispatcher.event import Event
from ncatbot.core.registry.dispatcher import HandlerEntry
from ncatbot.testing import factory
from ncatbot.types import At


def _make_ctx(event, func=None):
    """辅助: 构造 HookContext"""
    if func is None:

        async def func(e):
            pass

    entry = HandlerEntry(func=func, event_type="message")
    return HookContext(
        event=event,
        event_type=event.type,
        handler_entry=entry,
        api=None,
    )


def _msg_event(text: str, group_id: str = "100200", **kw):
    """辅助: 构造群消息 Event"""
    data = factory.group_message(text, group_id=group_id, **kw)
    return Event(type="message.group", data=data)


def _msg_event_with_at(text: str, at_qq: str, group_id: str = "100200"):
    """辅助: 构造含 At 段的群消息 Event"""
    message = [
        {"type": "text", "data": {"text": text}},
        {"type": "at", "data": {"qq": at_qq}},
    ]
    data = factory.group_message(
        text, group_id=group_id, message=message, raw_message=text
    )
    return Event(type="message.group", data=data)


def _msg_event_with_at_and_text(
    cmd: str, at_qq: str, extra: str = "", group_id: str = "100200"
):
    """辅助: 构造 '命令 @xxx 参数' 格式的消息"""
    message = [
        {"type": "text", "data": {"text": cmd + " "}},
        {"type": "at", "data": {"qq": at_qq}},
    ]
    if extra:
        message.append({"type": "text", "data": {"text": " " + extra}})
    raw = f"{cmd} @{at_qq}"
    if extra:
        raw += f" {extra}"
    data = factory.group_message(
        cmd, group_id=group_id, message=message, raw_message=raw
    )
    return Event(type="message.group", data=data)


# ======================= K-07: StartsWithHook =======================


async def test_startswith_match():
    """K-07: 前缀匹配通过"""
    hook = StartsWithHook("踢")
    event = _msg_event("踢 @张三")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_startswith_no_match():
    """K-07: 前缀不匹配 → SKIP"""
    hook = StartsWithHook("踢")
    event = _msg_event("禁言 @张三")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.SKIP


async def test_startswith_exact():
    """K-07: 精确等于前缀也通过"""
    hook = StartsWithHook("签到")
    event = _msg_event("签到")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_startswith_factory():
    """K-07: startswith() 工厂函数创建实例"""
    hook = startswith("踢")
    assert isinstance(hook, StartsWithHook)
    assert hook.prefix == "踢"


async def test_startswith_no_kwargs():
    """K-07: StartsWithHook 不修改 ctx.kwargs"""
    hook = StartsWithHook("echo ")
    event = _msg_event("echo hello world")
    ctx = _make_ctx(event)
    await hook.execute(ctx)
    assert ctx.kwargs == {}


# ======================= K-08: KeywordHook =======================


async def test_keyword_single_match():
    """K-08: 单关键词匹配"""
    hook = KeywordHook("帮助")
    event = _msg_event("我需要帮助")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_keyword_multi_match():
    """K-08: 多关键词任一匹配"""
    hook = KeywordHook("帮助", "help")
    event = _msg_event("need help")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_keyword_no_match():
    """K-08: 无关键词匹配 → SKIP"""
    hook = KeywordHook("帮助", "help")
    event = _msg_event("你好世界")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.SKIP


async def test_keyword_factory():
    """K-08: keyword() 工厂函数"""
    hook = keyword("a", "b")
    assert isinstance(hook, KeywordHook)
    assert hook.words == ("a", "b")


# ======================= K-09: RegexHook =======================


async def test_regex_match():
    """K-09: 正则匹配"""
    hook = RegexHook(r"roll (\d+)d(\d+)")
    event = _msg_event("roll 3d6")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE
    assert "match" in ctx.kwargs
    assert ctx.kwargs["match"].group(1) == "3"
    assert ctx.kwargs["match"].group(2) == "6"


async def test_regex_no_match():
    """K-09: 正则不匹配 → SKIP"""
    hook = RegexHook(r"^roll \d+d\d+$")
    event = _msg_event("hello world")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.SKIP
    assert "match" not in ctx.kwargs


async def test_regex_flags():
    """K-09: 正则 flags 参数"""
    hook = RegexHook(r"hello", re.IGNORECASE)
    event = _msg_event("HELLO world")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_regex_factory():
    """K-09: regex() 工厂函数"""
    hook = regex(r"\d+")
    assert isinstance(hook, RegexHook)


# ======================= K-10: NoticeTypeFilter =======================


async def test_notice_type_filter_match():
    """K-10: 通知类型匹配"""
    hook = NoticeTypeFilter("group_increase")
    data = factory.group_increase(user_id="99", group_id="100")
    event = Event(type="notice.group_increase", data=data)
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_notice_type_filter_no_match():
    """K-10: 通知类型不匹配 → SKIP"""
    hook = NoticeTypeFilter("group_decrease")
    data = factory.group_increase(user_id="99", group_id="100")
    event = Event(type="notice.group_increase", data=data)
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.SKIP


# ======================= K-11: RequestTypeFilter =======================


async def test_request_type_filter_match():
    """K-11: 请求类型匹配"""
    hook = RequestTypeFilter("friend")
    data = factory.friend_request(user_id="99")
    event = Event(type="request.friend", data=data)
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_request_type_filter_no_match():
    """K-11: 请求类型不匹配 → SKIP"""
    hook = RequestTypeFilter("group")
    data = factory.friend_request(user_id="99")
    event = Event(type="request.friend", data=data)
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.SKIP


# ======================= K-12: CommandHook 精确匹配 =======================


async def test_command_exact_match():
    """K-12: 无额外参数 → 精确匹配"""
    hook = CommandHook("签到")
    event = _msg_event("签到")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_command_exact_no_match():
    """K-12: 精确匹配不一致 → SKIP"""
    hook = CommandHook("签到")
    event = _msg_event("签到啦")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.SKIP


async def test_command_multi_alias():
    """K-12: 多别名匹配"""
    hook = CommandHook("帮助", "help", "?")
    event = _msg_event("help")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE


# ======================= K-13: CommandHook ignore_case =======================


async def test_command_ignore_case():
    """K-13: 大小写不敏感匹配"""
    hook = CommandHook("hello", ignore_case=True)
    event = _msg_event("HELLO")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_command_case_sensitive():
    """K-13: 默认大小写敏感"""
    hook = CommandHook("hello")
    event = _msg_event("HELLO")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.SKIP


# ======================= K-14: CommandHook str 参数绑定 =======================


async def test_command_str_binding():
    """K-14: str 参数绑定"""
    hook = CommandHook("echo")
    event = _msg_event("echo hello world")

    async def handler(self, event, content: str):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs["content"] == "hello world"


async def test_command_str_empty():
    """K-14: str 必选参数缺失 → SKIP"""
    hook = CommandHook("echo")
    event = _msg_event("echo")

    async def handler(self, event, content: str):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.SKIP


# ======================= K-15: CommandHook At 参数绑定 =======================


async def test_command_at_binding():
    """K-15: At 参数从 message.filter_at() 提取"""
    hook = CommandHook("踢")
    event = _msg_event_with_at("踢", "12345")

    async def handler(self, event, target: At):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert isinstance(ctx.kwargs["target"], At)
    assert ctx.kwargs["target"].user_id == "12345"


# ======================= K-16: CommandHook int 参数转换 =======================


async def test_command_int_binding():
    """K-16: int 参数从文本 token 转换"""
    hook = CommandHook("禁言")
    event = _msg_event_with_at_and_text("禁言", "12345", "120")

    async def handler(self, event, target: At, duration: int = 60):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs["duration"] == 120


# ======================= K-17: CommandHook 可选参数默认值 =======================


async def test_command_optional_param_default():
    """K-17: 可选参数使用默认值"""
    hook = CommandHook("禁言")
    event = _msg_event_with_at("禁言", "12345")

    async def handler(self, event, target: At, duration: int = 60):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE
    assert ctx.kwargs["duration"] == 60


# ======================= K-18: CommandHook 必选参数缺失 =======================


async def test_command_required_param_missing():
    """K-18: 必选 At 参数缺失 → SKIP"""
    hook = CommandHook("踢")
    event = _msg_event("踢")  # 无 At 段

    async def handler(self, event, target: At):
        pass

    ctx = _make_ctx(event, func=handler)
    result = await hook.execute(ctx)
    assert result == HookAction.SKIP


# ======================= K-19: Registrar on_group_command =======================


def test_registrar_on_group_command_creates_hooks():
    """K-19: on_group_command 创建 MessageTypeFilter + CommandHook"""

    r = Registrar()

    @r.on_group_command("test")
    async def handler(event):
        pass

    hooks = handler.__hooks__
    type_names = [type(h).__name__ for h in hooks]
    assert "MessageTypeFilter" in type_names
    assert "CommandHook" in type_names


def test_registrar_on_private_command():
    """K-19: on_private_command 创建 private MessageTypeFilter + CommandHook"""
    from ncatbot.core.registry.builtin_hooks import MessageTypeFilter

    r = Registrar()

    @r.on_private_command("test")
    async def handler(event):
        pass

    hooks = handler.__hooks__
    # 检查 MessageTypeFilter 是 private 类型
    msg_filter = [h for h in hooks if isinstance(h, MessageTypeFilter)][0]
    assert msg_filter.message_type == "private"


def test_registrar_on_command():
    """K-19: on_command 只创建 CommandHook（无 MessageTypeFilter）"""

    r = Registrar()

    @r.on_command("test")
    async def handler(event):
        pass

    hooks = handler.__hooks__
    type_names = [type(h).__name__ for h in hooks]
    assert "CommandHook" in type_names
    assert "MessageTypeFilter" not in type_names


# ======================= K-20: QQ 平台子注册器 通知/请求便捷方法 =======================


def test_registrar_qq_on_group_increase():
    """K-20: registrar.qq.on_group_increase 注册事件类型"""
    r = Registrar()

    @r.qq.on_group_increase()
    async def handler(event):
        pass

    assert handler.__handler_meta__["event_type"] == "notice.group_increase"


def test_registrar_qq_on_friend_request():
    """K-20: registrar.qq.on_friend_request 注册事件类型"""
    r = Registrar()

    @r.qq.on_friend_request()
    async def handler(event):
        pass

    assert handler.__handler_meta__["event_type"] == "request.friend"


def test_registrar_qq_on_poke():
    """K-20: registrar.qq.on_poke 注册事件类型"""
    r = Registrar()

    @r.qq.on_poke()
    async def handler(event):
        pass

    assert handler.__handler_meta__["event_type"] == "notice.poke"


# ======================= K-21: message.text 而非 raw_message =======================


async def test_startswith_uses_message_text():
    """K-21: StartsWithHook 使用 message.text"""
    hook = StartsWithHook("踢")
    # 构造 message 含 At 段的情况:
    # message.text 只包含 PlainText 部分
    event = _msg_event_with_at("踢", "12345")
    ctx = _make_ctx(event)
    result = await hook.execute(ctx)
    assert result == HookAction.CONTINUE


async def test_keyword_uses_message_text():
    """K-21: KeywordHook 使用 message.text"""
    hook = KeywordHook("帮助")
    event = _msg_event("请给我帮助")
    ctx = _make_ctx(event)
    assert await hook.execute(ctx) == HookAction.CONTINUE


async def test_command_uses_message_text():
    """K-21: CommandHook 使用 message.text"""
    hook = CommandHook("签到")
    event = _msg_event("签到")

    async def handler(self, event):
        pass

    ctx = _make_ctx(event, func=handler)
    assert await hook.execute(ctx) == HookAction.CONTINUE
