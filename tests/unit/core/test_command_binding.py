"""
命令参数绑定核心逻辑测试

测试 _command_binding.py 中的纯函数:
  K-12b: 前缀匹配无参数 handler (新行为)
  K-14b: 引号感知 (双引号)
  K-14c: 引号感知 (单引号)
  K-14d: 不平衡引号 fallback
  K-20b: 消息预处理 (首个 PlainText 移到最前)
  K-20c: 段跳过 (Image 等非匹配段跳过)
  K-20d: 段跳过=消耗 (被跳过的段不参与后续参数匹配)
  K-20e: 混合段顺序 (多段混合正确绑定)
  K-20f: 最后 str 收集剩余 token (跳过非 token 项)
  K-20g: 必选参数缺失 → None
  K-20h: CommandHook.execute 预处理+前缀匹配集成
  K-20i: CommandHook.execute Reply 开头消息
"""

from ncatbot.core.registry.hook import HookAction, HookContext
from ncatbot.core.registry.command_hook import CommandHook
from ncatbot.core.registry.dispatcher import HandlerEntry
from ncatbot.core.dispatcher.event import Event
from ncatbot.testing import factory
from ncatbot.types import At
from ncatbot.types.common.segment.text import PlainText
from ncatbot.types.common.segment.media import Image
from ncatbot.types.common.segment.array import MessageArray
from ncatbot.core.registry._command_binding import (
    preprocess_segments,
    tokenize_text,
    build_binding_stream,
    bind_params,
    get_param_spec,
    format_usage,
    match_command_prefix,
    _ParamSpec,
    _ParamInfo,
)


# ======================= 辅助函数 =======================


def _make_ctx(event, func=None):
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


def _msg_event_segments(segments_dicts, group_id="100200"):
    """构造任意段列表的群消息 Event"""
    # 拼接纯文本作为 raw_message
    raw = ""
    for s in segments_dicts:
        if s["type"] == "text":
            raw += s["data"]["text"]
        elif s["type"] == "at":
            raw += f"@{s['data'].get('qq', '')}"
    data = factory.group_message(
        raw.strip() or "test",
        group_id=group_id,
        message=segments_dicts,
        raw_message=raw,
    )
    return Event(type="message.group", data=data)


# ======================= tokenize_text =======================


class TestTokenizeText:
    def test_simple_split(self):
        assert tokenize_text("hello world") == ["hello", "world"]

    def test_double_quotes(self):
        """K-14b: 双引号包裹的部分作为单个 token"""
        assert tokenize_text('"hello world" foo') == ["hello world", "foo"]

    def test_single_quotes(self):
        """K-14c: 单引号包裹的部分作为单个 token"""
        assert tokenize_text("'hello world' bar") == ["hello world", "bar"]

    def test_unbalanced_quotes_fallback(self):
        """K-14d: 不平衡引号 fallback 到 str.split()"""
        result = tokenize_text('"hello world')
        # fallback 到 split, 所以得到两个 token
        assert result == ['"hello', "world"]

    def test_empty(self):
        assert tokenize_text("") == []

    def test_mixed_quotes(self):
        assert tokenize_text("echo \"hello world\" 'foo bar' baz") == [
            "echo",
            "hello world",
            "foo bar",
            "baz",
        ]


# ======================= preprocess_segments =======================


class TestPreprocessSegments:
    def test_text_already_first(self):
        """Text 已在首位 → 不变"""
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": "/ban"}},
                {"type": "at", "data": {"qq": "12345"}},
            ]
        )
        result = preprocess_segments(msg)
        assert isinstance(result[0], PlainText)
        assert result[0].text == "/ban"
        assert len(result) == 2

    def test_text_not_first(self):
        """K-20b: Reply/At 开头，Text 移到最前"""
        msg = MessageArray.from_list(
            [
                {"type": "reply", "data": {"id": "999"}},
                {"type": "at", "data": {"qq": "10001"}},
                {"type": "text", "data": {"text": "/ban "}},
                {"type": "at", "data": {"qq": "12345"}},
            ]
        )
        result = preprocess_segments(msg)
        assert isinstance(result[0], PlainText)
        assert result[0].text == "/ban "
        # Reply 和 At(bot) 仍在列表中，但排在后面
        assert len(result) == 4  # 所有段都保留，只是 Text 移到了首位

    def test_no_text(self):
        """无 PlainText → 原样返回"""
        msg = MessageArray.from_list(
            [
                {"type": "at", "data": {"qq": "12345"}},
                {"type": "image", "data": {"file": "pic.jpg"}},
            ]
        )
        result = preprocess_segments(msg)
        assert len(result) == 2
        assert not isinstance(result[0], PlainText)

    def test_empty_message(self):
        msg = MessageArray()
        result = preprocess_segments(msg)
        assert result == []


# ======================= match_command_prefix =======================


class TestMatchCommandPrefix:
    def test_exact_match(self):
        assert match_command_prefix("签到", ("签到",), False) == "签到"

    def test_prefix_match(self):
        assert match_command_prefix("ban 123", ("ban",), False) == "ban"

    def test_no_match(self):
        assert match_command_prefix("签到啦", ("签到",), False) is None

    def test_ignore_case(self):
        assert match_command_prefix("HELLO", ("hello",), True) == "hello"

    def test_multi_alias(self):
        assert match_command_prefix("help", ("帮助", "help", "?"), False) == "help"

    def test_quoted_token(self):
        """命令名不应该从引号中提取"""
        assert match_command_prefix('"ban" 123', ("ban",), False) == "ban"


# ======================= build_binding_stream =======================


class TestBuildBindingStream:
    def test_basic_tokens(self):
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": "/ban "}},
                {"type": "text", "data": {"text": "60"}},
            ]
        )
        segments = list(msg)
        stream = build_binding_stream(segments, "")
        # rest_text="" 产生 0 个 token, 第二个 Text("60") 产生 token("60")
        assert stream == [("token", "60")]

    def test_at_in_stream(self):
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": "/kick "}},
                {"type": "at", "data": {"qq": "12345"}},
            ]
        )
        segments = list(msg)
        stream = build_binding_stream(segments, "")
        assert len(stream) == 1
        assert stream[0][0] == "at"
        assert stream[0][1].user_id == "12345"

    def test_rest_text_tokens(self):
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": "/ban 60 hello"}},
            ]
        )
        segments = list(msg)
        stream = build_binding_stream(segments, "60 hello")
        assert stream == [("token", "60"), ("token", "hello")]

    def test_image_in_stream(self):
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": "/kick "}},
                {"type": "image", "data": {"file": "pic.jpg"}},
                {"type": "at", "data": {"qq": "12345"}},
            ]
        )
        segments = list(msg)
        stream = build_binding_stream(segments, "")
        assert len(stream) == 2
        assert stream[0][0] == "image"
        assert stream[1][0] == "at"

    def test_quoted_rest_text(self):
        """引号在 rest_text 中被正确处理"""
        msg = MessageArray.from_list(
            [
                {"type": "text", "data": {"text": 'echo "hello world" foo'}},
            ]
        )
        segments = list(msg)
        stream = build_binding_stream(segments, '"hello world" foo')
        assert stream == [("token", "hello world"), ("token", "foo")]


# ======================= bind_params =======================


class TestBindParams:
    def _make_spec(self, params):
        """构造 _ParamSpec"""

        infos = []
        for name, anno, has_default, default in params:
            infos.append(_ParamInfo(name, anno, has_default, default))
        return _ParamSpec(infos)

    def test_at_binding(self):
        """At 参数从 stream 中匹配 at 项"""
        at_obj = At(user_id="12345")
        stream = [("at", at_obj)]
        spec = self._make_spec([("target", At, False, None)])
        result = bind_params(spec, stream)
        assert result == {"target": at_obj}

    def test_int_binding(self):
        """int 参数从 token 转换"""
        stream = [("token", "42")]
        spec = self._make_spec([("count", int, False, None)])
        result = bind_params(spec, stream)
        assert result == {"count": 42}

    def test_float_binding(self):
        """float 参数从 token 转换"""
        stream = [("token", "3.14")]
        spec = self._make_spec([("amount", float, False, None)])
        result = bind_params(spec, stream)
        assert result == {"amount": 3.14}

    def test_str_single_token(self):
        """非最后 str 消费单个 token"""
        stream = [("token", "hello"), ("token", "world")]
        spec = self._make_spec(
            [
                ("first", str, False, None),
                ("second", str, False, None),
            ]
        )
        result = bind_params(spec, stream)
        assert result == {"first": "hello", "second": "world"}

    def test_str_last_collects_remaining(self):
        """K-20f: 最后 str 收集剩余所有 token"""
        stream = [("token", "hello"), ("token", "world"), ("token", "foo")]
        spec = self._make_spec([("content", str, False, None)])
        result = bind_params(spec, stream)
        assert result == {"content": "hello world foo"}

    def test_skip_non_matching_segment(self):
        """K-20c: 段跳过 — Image 被跳过，At 绑定到 target"""
        at_obj = At(user_id="12345")
        img = Image(file="pic.jpg")
        stream = [("image", img), ("at", at_obj)]
        spec = self._make_spec([("target", At, False, None)])
        result = bind_params(spec, stream)
        assert result == {"target": at_obj}

    def test_skip_is_permanent(self):
        """K-20d: 段跳过=消耗 — 被跳过的 token 不参与后续参数"""
        stream = [("token", "hello"), ("at", At(user_id="12345"))]
        spec = self._make_spec(
            [
                ("target", At, False, None),
                ("msg", str, False, None),
            ]
        )
        result = bind_params(spec, stream)
        # target(At): token("hello") 跳过(消耗), at → 匹配
        # msg(str): 无更多 token → 缺失 → None
        assert result is None

    def test_skip_is_permanent_with_default(self):
        """段跳过=消耗，但有默认值不报错"""
        stream = [("token", "hello"), ("at", At(user_id="12345"))]
        spec = self._make_spec(
            [
                ("target", At, False, None),
                ("msg", str, True, "默认"),
            ]
        )
        result = bind_params(spec, stream)
        assert result["target"].user_id == "12345"
        assert result["msg"] == "默认"

    def test_mixed_segments(self):
        """K-20e: 混合段顺序正确绑定"""
        at1 = At(user_id="111")
        at2 = At(user_id="222")
        stream = [
            ("token", "60"),
            ("at", at1),
            ("image", Image(file="x.jpg")),
            ("at", at2),
            ("token", "hello"),
        ]
        spec = self._make_spec(
            [
                ("target", At, False, None),
                ("duration", int, True, 30),
                ("note", str, True, ""),
            ]
        )
        result = bind_params(spec, stream)
        # target(At): token("60")跳过, at1 匹配
        # duration(int): image跳过, at2跳过, token("hello")不是int → 无匹配 → default=30
        # 注意: token("hello")被int扫描时尝试转换失败,但被消耗了
        # 所以这里需要思考:对int,非token项跳过,token("hello")转换失败也跳过
        # 最终duration使用默认值30, note也用默认值""
        assert result["target"].user_id == "111"
        assert result["duration"] == 30
        assert result["note"] == ""

    def test_required_missing_returns_none(self):
        """K-20g: 必选参数无匹配 + 无默认值 → None"""
        stream = []
        spec = self._make_spec([("target", At, False, None)])
        result = bind_params(spec, stream)
        assert result is None

    def test_optional_default(self):
        """有默认值 → 使用默认值"""
        stream = []
        spec = self._make_spec([("duration", int, True, 60)])
        result = bind_params(spec, stream)
        assert result == {"duration": 60}

    def test_last_str_skips_non_token(self):
        """K-20f: 最后 str 只收集 token，跳过非 token 项"""
        stream = [
            ("at", At(user_id="12345")),
            ("token", "hello"),
            ("image", Image(file="x.jpg")),
            ("token", "world"),
        ]
        spec = self._make_spec([("content", str, False, None)])
        result = bind_params(spec, stream)
        # 最后 str 收集: at 跳过, "hello" 收集, image 跳过, "world" 收集
        assert result == {"content": "hello world"}

    def test_skip_names(self):
        """skip_names 跳过指定参数"""
        stream = [("token", "hello")]
        spec = self._make_spec(
            [
                ("subcommand", str, True, ""),
                ("content", str, False, None),
            ]
        )
        result = bind_params(spec, stream, skip_names={"subcommand"})
        assert result == {"subcommand": "", "content": "hello"}


# ======================= get_param_spec =======================


class TestGetParamSpec:
    def test_basic(self):
        async def handler(self, event, target: At, duration: int = 60):
            pass

        spec = get_param_spec(handler)
        assert len(spec.params) == 2
        assert spec.params[0].name == "target"
        assert spec.params[0].annotation is At
        assert not spec.params[0].has_default
        assert spec.params[1].name == "duration"
        assert spec.params[1].annotation is int
        assert spec.params[1].has_default
        assert spec.params[1].default == 60

    def test_no_extra_params(self):
        async def handler(self, event):
            pass

        spec = get_param_spec(handler)
        assert len(spec.params) == 0

    def test_no_self(self):
        async def handler(event, content: str):
            pass

        spec = get_param_spec(handler)
        assert len(spec.params) == 1
        assert spec.params[0].name == "content"


# ======================= format_usage =======================


class TestFormatUsage:
    def test_basic(self):
        spec = _ParamSpec(
            [
                _ParamInfo("target", At, False, None),
                _ParamInfo("duration", int, True, 60),
            ]
        )
        usage = format_usage(("/ban",), spec)
        assert "/ban" in usage
        assert "<target:" in usage
        assert "[duration:" in usage
        assert "60" in usage


# ======================= CommandHook.execute 集成测试 =======================


class TestCommandHookExecuteIntegration:
    """测试 CommandHook.execute 的完整流程（预处理+匹配+绑定）"""

    async def test_prefix_match_no_params(self):
        """K-12b: 无参数 handler + 前缀匹配 → CONTINUE"""
        hook = CommandHook("签到")

        async def handler(self, event):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "签到 额外文本"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        assert await hook.execute(ctx) == HookAction.CONTINUE

    async def test_exact_match_still_works(self):
        """精确输入仍然兼容"""
        hook = CommandHook("签到")

        async def handler(self, event):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "签到"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        assert await hook.execute(ctx) == HookAction.CONTINUE

    async def test_no_match(self):
        """不匹配 → SKIP"""
        hook = CommandHook("签到")

        async def handler(self, event):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "签到啦"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        assert await hook.execute(ctx) == HookAction.SKIP

    async def test_reply_prefix_message(self):
        """K-20i: Reply 开头的消息, Text 被预处理移到最前"""
        hook = CommandHook("/ban")

        async def handler(self, event, target: At, duration: int = 60):
            pass

        event = _msg_event_segments(
            [
                {"type": "reply", "data": {"id": "999"}},
                {"type": "at", "data": {"qq": "10001"}},
                {"type": "text", "data": {"text": "/ban "}},
                {"type": "at", "data": {"qq": "12345"}},
                {"type": "text", "data": {"text": " 120"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        result = await hook.execute(ctx)
        assert result == HookAction.CONTINUE
        # Reply 被跳过, At(10001) 匹配 target, "120" 匹配 duration
        assert ctx.kwargs["target"].user_id == "10001"
        assert ctx.kwargs["duration"] == 120

    async def test_quote_handling_integration(self):
        """引号在完整流程中正确处理"""
        hook = CommandHook("echo")

        async def handler(self, event, content: str):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": 'echo "hello world" foo'}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        result = await hook.execute(ctx)
        assert result == HookAction.CONTINUE
        assert ctx.kwargs["content"] == "hello world foo"

    async def test_missing_required_param_skips(self):
        """必选参数缺失 → SKIP"""
        hook = CommandHook("/kick")

        async def handler(self, event, target: At):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "/kick"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        result = await hook.execute(ctx)
        assert result == HookAction.SKIP

    async def test_image_skipped_at_bound(self):
        """K-20c 集成: Image 跳过, At 绑定"""
        hook = CommandHook("/kick")

        async def handler(self, event, target: At):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "/kick "}},
                {"type": "image", "data": {"file": "pic.jpg"}},
                {"type": "at", "data": {"qq": "12345"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        result = await hook.execute(ctx)
        assert result == HookAction.CONTINUE
        assert ctx.kwargs["target"].user_id == "12345"

    async def test_ignore_case(self):
        """ignore_case 集成"""
        hook = CommandHook("hello", ignore_case=True)

        async def handler(self, event):
            pass

        event = _msg_event_segments(
            [
                {"type": "text", "data": {"text": "HELLO"}},
            ]
        )
        ctx = _make_ctx(event, func=handler)
        assert await hook.execute(ctx) == HookAction.CONTINUE
