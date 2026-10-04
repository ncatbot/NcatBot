"""
AI 适配器单元测试

规范:
  AI-03: AIBotAPI.chat() str 自动包装为 messages
  AI-04: AIBotAPI.chat() list[dict] 直接透传
  AI-05: AIBotAPI 未指定模型时抛出 ValueError
  AI-06: AIBotAPI 模型不存在时回退到默认模型
  AI-07: AIAdapter 生命周期（connect/disconnect/listen）
  AI-08: AIAdapter 未 connect 时 get_api 抛出 RuntimeError
  AI-09: chat_text() 直接返回文本字符串
  AI-10: generate_image() 返回 Image 消息段
  AI-11: MessageArray 纯文本转换
  AI-12: MessageArray 图片转多模态
  AI-13: At 段转可读文本 + nickname_map
  AI-14: 不支持段跳过并警告
  AI-15: 单个 MessageSegment 输入
  AI-16: transcription() 调用 litellm.atranscription
  AI-17: transcription() 未指定模型抛出 ValueError
  AI-18: transcription() 模型不存在时回退到默认 asr_model
  AI-19: transcription_text() 返回文本字符串
  AI-20: transcription() 透传 language/prompt/response_format/temperature
  AI-21: chat() 带 MCP 服务器时加载工具并传给 acompletion
  AI-22: chat() 无 mcp_servers 时不传 tools
  AI-23: chat() MCP 工具调用循环（请求工具 → 执行 → 回传 → 完成）
  AI-24: chat() MCP 工具调用达到 max_tool_calls 上限
  AI-25: MCP 传输类型自动判断
  AI-26: MCP 工具加载与命名空间化（{server}_{tool}）
  AI-27: MCP 工具调用返回文本结果
  AI-28: MCP 单个服务器连接失败不影响其他服务器
  AI-31: chat_text() 透传 mcp_servers / max_tool_calls 给 chat()
  AI-32: video_generation() 默认模型、参数覆盖和参考图像
  AI-33: video_generation() 未指定模型时抛出 ValueError
  AI-34: video_generation() 仅模型不存在时回退一次
  AI-35: video_status/content() 按任务 ID 调用，不回退模型
  AI-36: AIAdapter 启动验证 video_model，失败不阻止启动
"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from ncatbot.adapter.ai.config import AIConfig
from ncatbot.adapter.ai.api.bot_api import AIBotAPI
from ncatbot.adapter.ai.api.mcp import MCPSessionManager
from ncatbot.adapter.ai.adapter import AIAdapter
from ncatbot.types import Image


# ---- AI-03 ----


@pytest.mark.asyncio
async def test_chat_str_wraps_to_messages():
    """AI-03: chat() 接收 str 时自动包装为 messages 列表"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat("hello")

    # 验证 acompletion 被调用时 messages 格式正确
    call_kwargs = mock_fn.call_args
    assert call_kwargs.kwargs.get("messages") == [{"role": "user", "content": "hello"}]


# ---- AI-04 ----


@pytest.mark.asyncio
async def test_chat_list_passthrough():
    """AI-04: chat() 接收 list[dict] 时直接透传"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ]

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(messages)

    call_kwargs = mock_fn.call_args
    assert call_kwargs.kwargs.get("messages") == messages


# ---- AI-05 ----


@pytest.mark.asyncio
async def test_chat_no_model_raises():
    """AI-05: 未指定模型时 chat() 抛出 ValueError"""
    cfg = AIConfig()  # 无默认模型
    api = AIBotAPI(cfg)

    with pytest.raises(ValueError, match="未指定模型"):
        await api.chat("hello")


@pytest.mark.asyncio
async def test_embeddings_no_model_raises():
    """AI-05: 未指定模型时 embeddings() 抛出 ValueError"""
    cfg = AIConfig()
    api = AIBotAPI(cfg)

    with pytest.raises(ValueError, match="未指定模型"):
        await api.embeddings("hello")


@pytest.mark.asyncio
async def test_image_generation_no_model_raises():
    """AI-05: 未指定模型时 image_generation() 抛出 ValueError"""
    cfg = AIConfig()
    api = AIBotAPI(cfg)

    with pytest.raises(ValueError, match="未指定模型"):
        await api.image_generation("a cat")


# ---- AI-06 ----


@pytest.mark.asyncio
async def test_chat_model_fallback():
    """AI-06: 指定模型不存在时回退到默认模型"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    call_count = 0

    async def mock_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if kwargs.get("model") == "nonexistent-model":
            raise Exception("model_not_found: nonexistent-model")
        return mock_response

    with patch("litellm.acompletion", side_effect=mock_acompletion):
        result = await api.chat("hello", model="nonexistent-model")

    assert call_count == 2  # 第一次尝试失败，第二次回退成功
    assert result is mock_response


# ---- AI-07 ----


@pytest.mark.asyncio
async def test_adapter_lifecycle():
    """AI-07: AIAdapter connect/disconnect/listen 生命周期"""
    adapter = AIAdapter(config={"completion_model": "gpt-4"})

    # setup 不应抛出
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        await adapter.setup()

    # connect
    with patch(
        "ncatbot.adapter.ai.adapter.AIAdapter._validate_models", new_callable=AsyncMock
    ):
        await adapter.connect()

    assert adapter.connected is True
    assert adapter.get_api() is not None
    assert adapter.get_api().platform == "ai"

    # disconnect 后 listen 应该完成
    async def disconnect_soon():
        await asyncio.sleep(0.05)
        await adapter.disconnect()

    task = asyncio.create_task(disconnect_soon())
    await adapter.listen()
    await task

    assert adapter.connected is False


# ---- AI-08 ----


def test_adapter_get_api_before_connect():
    """AI-08: 未 connect 时 get_api() 抛出 RuntimeError"""
    adapter = AIAdapter(config={"completion_model": "gpt-4"})
    with pytest.raises(RuntimeError, match="尚未 connect"):
        adapter.get_api()


# ---- AI-09 ----


@pytest.mark.asyncio
async def test_chat_text_returns_str():
    """AI-09: chat_text() 直接返回文本字符串"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    mock_message = MagicMock()
    mock_message.content = "你好！有什么可以帮你的？"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.chat_text("你好")

    assert isinstance(result, str)
    assert result == "你好！有什么可以帮你的？"


@pytest.mark.asyncio
async def test_chat_text_returns_empty_on_none():
    """AI-09: chat_text() content 为 None 时返回空字符串"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    mock_message = MagicMock()
    mock_message.content = None
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.chat_text("你好")

    assert result == ""


# ---- AI-10 ----


@pytest.mark.asyncio
async def test_generate_image_returns_url():
    """AI-10: generate_image() 有 url 时返回 Image(file=url)"""
    cfg = AIConfig(image_model="dall-e-3")
    api = AIBotAPI(cfg)

    mock_image = MagicMock()
    mock_image.url = "https://example.com/image.png"
    mock_image.b64_json = None
    mock_response = MagicMock()
    mock_response.data = [mock_image]

    with patch("litellm.aimage_generation", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.generate_image("一只猫")

    assert isinstance(result, Image)
    assert result.file == "https://example.com/image.png"
    assert result.url == "https://example.com/image.png"


@pytest.mark.asyncio
async def test_generate_image_returns_base64():
    """AI-10: generate_image() 无 url 时返回 Image(file=base64://...)"""
    cfg = AIConfig(image_model="dall-e-3")
    api = AIBotAPI(cfg)

    mock_image = MagicMock()
    mock_image.url = None
    mock_image.b64_json = "iVBORw0KGgo="
    mock_response = MagicMock()
    mock_response.data = [mock_image]

    with patch("litellm.aimage_generation", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.generate_image("一只猫")

    assert isinstance(result, Image)
    assert result.file == "base64://iVBORw0KGgo="


# ---- AI-11 ----


@pytest.mark.asyncio
async def test_chat_message_array_text_only():
    """AI-11: MessageArray 纯文本段拼接为普通字符串"""
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.text import PlainText

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray([PlainText(text="你好"), PlainText(text="世界")])

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr)

    msgs = mock_fn.call_args.kwargs["messages"]
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "你好世界"


# ---- AI-12 ----


@pytest.mark.asyncio
async def test_chat_message_array_with_image():
    """AI-12: MessageArray 含 Image 时转为多模态 content"""
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.text import PlainText

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray(
        [
            PlainText(text="描述图片"),
            Image(
                file="https://img.example.com/cat.png",
                url="https://img.example.com/cat.png",
            ),
        ]
    )

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr)

    msgs = mock_fn.call_args.kwargs["messages"]
    content = msgs[0]["content"]
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "描述图片"}
    assert content[1] == {
        "type": "image_url",
        "image_url": {"url": "https://img.example.com/cat.png"},
    }


@pytest.mark.asyncio
async def test_chat_message_array_base64_image():
    """AI-12: base64:// 前缀的 Image 转为 data URI"""
    from ncatbot.types.common.segment.array import MessageArray

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray(
        [
            Image(file="base64://iVBORw0KGgo="),
        ]
    )

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr)

    content = mock_fn.call_args.kwargs["messages"][0]["content"]
    assert content[0]["image_url"]["url"] == "data:image/png;base64,iVBORw0KGgo="


# ---- AI-13 ----


@pytest.mark.asyncio
async def test_chat_at_segment_default():
    """AI-13: At 段默认渲染为 @{user_id}"""
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.text import At, PlainText

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray([PlainText(text="你好 "), At(user_id="12345")])

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr)

    content = mock_fn.call_args.kwargs["messages"][0]["content"]
    assert content == "你好 @12345"


@pytest.mark.asyncio
async def test_chat_at_segment_with_nickname_map():
    """AI-13: 提供 nickname_map 时 At 渲染为 @昵称"""
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.text import At, PlainText

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray([PlainText(text="你好 "), At(user_id="12345")])

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr, nickname_map={"12345": "小明"})

    content = mock_fn.call_args.kwargs["messages"][0]["content"]
    assert content == "你好 @小明"


# ---- AI-14 ----


@pytest.mark.asyncio
async def test_chat_unsupported_segment_skipped(caplog):
    """AI-14: 不支持的媒体段跳过并记录警告"""
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.media import Video
    from ncatbot.types.common.segment.text import PlainText

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    arr = MessageArray(
        [
            PlainText(text="看这个"),
            Video(file="video.mp4"),
        ]
    )

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(arr)

    # 文本部分正常传递，视频被跳过
    content = mock_fn.call_args.kwargs["messages"][0]["content"]
    assert content == "看这个"


# ---- AI-15 ----


@pytest.mark.asyncio
async def test_chat_single_image_segment():
    """AI-15: 直接传入单个 Image 段"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    img = Image(
        file="https://img.example.com/cat.png", url="https://img.example.com/cat.png"
    )

    mock_response = MagicMock()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.chat(img)

    content = mock_fn.call_args.kwargs["messages"][0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "image_url"


# ---- AI-16 ----


@pytest.mark.asyncio
async def test_transcription_calls_atranscription():
    """AI-16: transcription() 正确调用 litellm.atranscription"""
    cfg = AIConfig(asr_model="whisper-1")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    mock_response.text = "你好世界"

    with patch("litellm.atranscription", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.transcription("audio.mp3")

    assert result is mock_response
    call_kwargs = mock_fn.call_args
    assert call_kwargs.kwargs["model"] == "whisper-1"
    assert call_kwargs.kwargs["file"] == "audio.mp3"


# ---- AI-17 ----


@pytest.mark.asyncio
async def test_transcription_no_model_raises():
    """AI-17: 未指定模型时 transcription() 抛出 ValueError"""
    cfg = AIConfig()  # 无 asr_model
    api = AIBotAPI(cfg)

    with pytest.raises(ValueError, match="未指定模型"):
        await api.transcription("audio.mp3")


# ---- AI-18 ----


@pytest.mark.asyncio
async def test_transcription_model_fallback():
    """AI-18: 指定模型不存在时回退到默认 asr_model"""
    cfg = AIConfig(asr_model="whisper-1")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    call_count = 0

    async def mock_atranscription(**kwargs):
        nonlocal call_count
        call_count += 1
        if kwargs.get("model") == "nonexistent-asr":
            raise Exception("model_not_found: nonexistent-asr")
        return mock_response

    with patch("litellm.atranscription", side_effect=mock_atranscription):
        result = await api.transcription("audio.mp3", model="nonexistent-asr")

    assert call_count == 2
    assert result is mock_response


# ---- AI-19 ----


@pytest.mark.asyncio
async def test_transcription_text_returns_str():
    """AI-19: transcription_text() 直接返回文本字符串"""
    cfg = AIConfig(asr_model="whisper-1")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    mock_response.text = "识别出的文本内容"

    with patch("litellm.atranscription", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.transcription_text("audio.mp3")

    assert isinstance(result, str)
    assert result == "识别出的文本内容"


@pytest.mark.asyncio
async def test_transcription_text_returns_empty_on_none():
    """AI-19: transcription_text() text 为 None 时返回空字符串"""
    cfg = AIConfig(asr_model="whisper-1")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()
    mock_response.text = None

    with patch("litellm.atranscription", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        result = await api.transcription_text("audio.mp3")

    assert result == ""


# ---- AI-20 ----


@pytest.mark.asyncio
async def test_transcription_kwargs_passthrough():
    """AI-20: transcription() 透传 language/prompt/response_format/temperature"""
    cfg = AIConfig(asr_model="whisper-1")
    api = AIBotAPI(cfg)

    mock_response = MagicMock()

    with patch("litellm.atranscription", new_callable=AsyncMock) as mock_fn:
        mock_fn.return_value = mock_response
        await api.transcription(
            "audio.mp3",
            language="zh",
            prompt="这是一段中文语音",
            response_format="json",
            temperature=0.2,
        )

    call_kwargs = mock_fn.call_args.kwargs
    assert call_kwargs["language"] == "zh"
    assert call_kwargs["prompt"] == "这是一段中文语音"
    assert call_kwargs["response_format"] == "json"
    assert call_kwargs["temperature"] == 0.2


# ---- MCP 支持（AI-21 ~ AI-30） ----


class FakeMCPManager:
    """MCPSessionManager 的替身，供 chat() 工具调用测试使用。"""

    def __init__(self, tools=None):
        self.tools = tools or [
            {
                "type": "function",
                "function": {
                    "name": "weather_get_weather",
                    "description": "查询天气",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
        self.called_tools: list = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def load_tools(self):
        return self.tools

    async def call_openai_tool(self, tool_call):
        self.called_tools.append(tool_call)
        return "北京天气晴朗"


def _make_response(content=None, tool_calls=None):
    """构造 litellm ModelResponse 风格的 mock 响应。"""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls
    choice = MagicMock()
    choice.message = message
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---- AI-21 ----


@pytest.mark.asyncio
async def test_chat_mcp_loads_tools_param():
    """AI-21: chat() 传 mcp_servers 时加载工具并传给 acompletion"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    resp = _make_response(content="回答", tool_calls=None)
    with (
        patch(
            "ncatbot.adapter.ai.api.bot_api.MCPSessionManager",
            return_value=FakeMCPManager(),
        ),
        patch("litellm.acompletion", AsyncMock(return_value=resp)) as mock_fn,
    ):
        await api.chat("北京天气如何?", mcp_servers={"weather": {"url": "http://x"}})

    call_kwargs = mock_fn.call_args.kwargs
    assert call_kwargs.get("tools") == FakeMCPManager().tools
    assert call_kwargs["tools"][0]["function"]["name"] == "weather_get_weather"


@pytest.mark.asyncio
async def test_chat_mcp_uses_config_default():
    """AI-21: chat() 未显式传 mcp_servers 时使用 config 默认值"""
    cfg = AIConfig(
        completion_model="gpt-4",
        mcp_servers={"weather": {"url": "http://x"}},
    )
    api = AIBotAPI(cfg)

    resp = _make_response(content="回答", tool_calls=None)
    with (
        patch(
            "ncatbot.adapter.ai.api.bot_api.MCPSessionManager",
            return_value=FakeMCPManager(),
        ),
        patch("litellm.acompletion", AsyncMock(return_value=resp)) as mock_fn,
    ):
        await api.chat("北京天气如何?")

    assert "tools" in mock_fn.call_args.kwargs


# ---- AI-22 ----


@pytest.mark.asyncio
async def test_chat_no_mcp_no_tools():
    """AI-22: 未配置 MCP 时不传 tools 参数（回归保护）"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    resp = _make_response(content="回答", tool_calls=None)
    with patch("litellm.acompletion", AsyncMock(return_value=resp)) as mock_fn:
        await api.chat("hello")

    assert "tools" not in mock_fn.call_args.kwargs


# ---- AI-23 ----


@pytest.mark.asyncio
async def test_chat_mcp_tool_call_loop():
    """AI-23: chat() 模型请求工具 → 执行 MCP 工具 → 回传结果 → 完成"""
    from litellm.types.utils import ChatCompletionMessageToolCall

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    first = _make_response(
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id="call_1",
                type="function",
                function={
                    "name": "weather_get_weather",
                    "arguments": '{"city": "北京"}',
                },
            )
        ],
    )
    second = _make_response(content="北京今天天气晴朗", tool_calls=None)

    manager = FakeMCPManager()
    with (
        patch("ncatbot.adapter.ai.api.bot_api.MCPSessionManager", return_value=manager),
        patch("litellm.acompletion", AsyncMock(side_effect=[first, second])) as mock_fn,
    ):
        result = await api.chat(
            "北京天气如何?", mcp_servers={"weather": {"url": "http://x"}}
        )

    assert result is second
    assert mock_fn.await_count == 2
    assert len(manager.called_tools) == 1
    assert manager.called_tools[0].id == "call_1"

    # 第二次调用应包含 assistant 工具请求 + tool 结果消息
    msgs = mock_fn.await_args.kwargs["messages"]
    assert msgs[-2]["role"] == "assistant"
    assert msgs[-2]["tool_calls"][0]["id"] == "call_1"
    assert msgs[-1] == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "北京天气晴朗",
    }


# ---- AI-24 ----


@pytest.mark.asyncio
async def test_chat_mcp_max_tool_calls():
    """AI-24: chat() 工具调用达到 max_tool_calls 上限时返回最后一次响应"""
    from litellm.types.utils import ChatCompletionMessageToolCall

    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    always_tools = _make_response(
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id="call_1",
                type="function",
                function={"name": "weather_get_weather", "arguments": "{}"},
            )
        ],
    )

    manager = FakeMCPManager()
    with (
        patch("ncatbot.adapter.ai.api.bot_api.MCPSessionManager", return_value=manager),
        patch("litellm.acompletion", AsyncMock(return_value=always_tools)) as mock_fn,
    ):
        result = await api.chat(
            "hi", mcp_servers={"weather": {"url": "http://x"}}, max_tool_calls=3
        )

    assert mock_fn.await_count == 3
    assert result is always_tools


# ---- AI-25 ----


def test_mcp_transport_resolution():
    """AI-25: MCP 传输类型缺省自动判断"""
    assert MCPSessionManager._resolve_transport({"url": "https://x/mcp"}) == "http"
    assert MCPSessionManager._resolve_transport({"command": "npx"}) == "stdio"
    assert (
        MCPSessionManager._resolve_transport({"transport": "sse", "url": "https://x"})
        == "sse"
    )
    assert (
        MCPSessionManager._resolve_transport({"transport": "http", "url": "https://x"})
        == "http"
    )
    assert MCPSessionManager._resolve_transport({}) == "stdio"


# ---- AI-26 ----


@pytest.mark.asyncio
async def test_mcp_load_tools_namespace():
    """AI-26: MCP 工具加载并按 {server}_{tool} 命名空间化"""
    from mcp.types import ListToolsResult, Tool

    class FakeSession:
        def __init__(self, tools):
            self._tools = tools

        async def list_tools(self):
            return ListToolsResult(tools=self._tools)

    tool = Tool(
        name="get_weather",
        description="查询天气",
        inputSchema={"type": "object", "properties": {}},
    )
    mgr = MCPSessionManager({})
    mgr._sessions = {"weather": FakeSession([tool])}

    tools = await mgr.load_tools()

    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "weather_get_weather"
    assert mgr._tool_map["weather_get_weather"] == ("weather", "get_weather")


# ---- AI-27 ----


@pytest.mark.asyncio
async def test_mcp_call_tool_returns_text():
    """AI-27: MCP 工具调用返回文本结果"""
    from mcp.types import CallToolResult, TextContent

    class FakeSession:
        def __init__(self, result):
            self._result = result
            self.called = None

        async def call_tool(self, name, arguments):
            self.called = (name, arguments)
            return self._result

    result = CallToolResult(
        content=[TextContent(type="text", text="sunny")], isError=False
    )
    session = FakeSession(result)
    mgr = MCPSessionManager({})
    mgr._sessions = {"weather": session}
    mgr._tool_map = {"weather_get_weather": ("weather", "get_weather")}

    text = await mgr.call_tool("weather_get_weather", {"city": "Beijing"})

    assert text == "sunny"
    assert session.called == ("get_weather", {"city": "Beijing"})


@pytest.mark.asyncio
async def test_mcp_call_tool_error_marked():
    """AI-27: MCP 工具 isError 时返回错误标注"""
    from mcp.types import CallToolResult, TextContent

    class FakeSession:
        async def call_tool(self, name, arguments):
            return CallToolResult(
                content=[TextContent(type="text", text="no permission")],
                isError=True,
            )

    mgr = MCPSessionManager({})
    mgr._sessions = {"srv": FakeSession()}
    mgr._tool_map = {"srv_tool": ("srv", "tool")}

    text = await mgr.call_tool("srv_tool", {})

    assert text == "[MCP 工具调用错误]\nno permission"


# ---- AI-28 ----


@pytest.mark.asyncio
async def test_mcp_connect_tolerates_single_failure():
    """AI-28: 单个 MCP 服务器连接失败不影响其他服务器"""
    import contextlib

    mgr = MCPSessionManager({"ok": {}, "bad": {"fail": True}})

    def _fake_build(name, cfg):
        @contextlib.asynccontextmanager
        async def _cm():
            session = MagicMock()
            session.initialize = AsyncMock()
            if cfg.get("fail"):
                session.initialize.side_effect = RuntimeError("connect failed")
            yield session

        return _cm()

    with patch.object(mgr, "_build_session_cm", side_effect=_fake_build):
        await mgr.connect()

    assert "ok" in mgr._sessions
    assert "bad" not in mgr._sessions
    assert mgr.connected is True
    await mgr.close()


# ---- AI-29 ----


def test_cli_configure_mcp_http(monkeypatch):
    """AI-29: cli_configure() 交互收集 http MCP 服务器"""
    responses = iter(
        [
            "yes",  # 是否添加 MCP
            "deepwiki",  # 服务器名称
            "http",  # 传输类型
            "https://mcp.deepwiki.com/mcp",  # url
            "Authorization:Bearer abc",  # headers
            "no",  # 继续添加?
        ]
    )
    monkeypatch.setattr(
        "click.confirm",
        lambda msg, *a, **k: next(responses).lower().startswith("y"),
    )
    monkeypatch.setattr("click.prompt", lambda msg, *a, **k: next(responses))

    servers = AIAdapter._cli_configure_mcp()

    assert servers == {
        "deepwiki": {
            "transport": "http",
            "url": "https://mcp.deepwiki.com/mcp",
            "headers": {"Authorization": "Bearer abc"},
        }
    }


def test_cli_configure_mcp_stdio(monkeypatch):
    """AI-29: cli_configure() 交互收集 stdio MCP 服务器"""
    responses = iter(
        [
            "yes",  # 是否添加 MCP
            "mcp",  # 服务器名称
            "stdio",  # 传输类型
            "npx",  # command
            "-y @mcp/server",  # args
            "TOKEN=abc",  # env
            "no",  # 继续添加?
        ]
    )
    monkeypatch.setattr(
        "click.confirm",
        lambda msg, *a, **k: next(responses).lower().startswith("y"),
    )
    monkeypatch.setattr("click.prompt", lambda msg, *a, **k: next(responses))

    servers = AIAdapter._cli_configure_mcp()

    assert servers == {
        "mcp": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@mcp/server"],
            "env": {"TOKEN": "abc"},
        }
    }


# ---- AI-31 ----


@pytest.mark.asyncio
async def test_chat_text_forwards_mcp_params():
    """AI-31: chat_text() 透传 mcp_servers / max_tool_calls 给 chat()"""
    cfg = AIConfig(completion_model="gpt-4")
    api = AIBotAPI(cfg)

    mock_resp = _make_response(content="北京天气晴朗", tool_calls=None)

    with patch.object(api, "chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_resp
        result = await api.chat_text(
            "北京天气如何?",
            mcp_servers={"weather": {"url": "http://x"}},
            max_tool_calls=5,
        )

    assert result == "北京天气晴朗"
    call_kwargs = mock_chat.call_args.kwargs
    assert call_kwargs["mcp_servers"] == {"weather": {"url": "http://x"}}
    assert call_kwargs["max_tool_calls"] == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("model", [None, "gemini/veo-test"])
async def test_video_generation_parameters(model):
    """AI-32: 视频生成使用默认模型或覆盖模型，并合并通用参数与参考图像。"""
    api = AIBotAPI(
        AIConfig(
            video_model="openai/sora-2",
            api_key="config-key",
            base_url="https://config.example/v1",
            timeout=45,
        )
    )
    reference = b"reference-image"
    response = MagicMock(id="video_test", status="queued")
    with patch("litellm.avideo_generation", AsyncMock(return_value=response)) as fn:
        result = await api.video_generation(
            "a cat",
            model=model,
            seconds="8",
            size="1280x720",
            input_reference=reference,
            api_key="override-key",
            api_base="https://override.example/v1",
            timeout=90,
            user="user-1",
        )

    assert result is response
    fn.assert_awaited_once_with(
        model=model or "openai/sora-2",
        prompt="a cat",
        seconds="8",
        size="1280x720",
        input_reference=reference,
        api_key="override-key",
        api_base="https://override.example/v1",
        timeout=90,
        user="user-1",
    )


@pytest.mark.asyncio
async def test_video_generation_no_model():
    """AI-33: 没有指定 video_model 时不请求提供商，提示如何配置模型。"""
    api = AIBotAPI(AIConfig())
    with patch("litellm.avideo_generation", AsyncMock()) as fn:
        with pytest.raises(ValueError, match="video_model"):
            await api.video_generation("a cat")
    fn.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "requested, default, message, expected_models",
    [
        ("missing", "openai/sora-2", "model_not_found", ["missing", "openai/sora-2"]),
        ("missing", "", "model_not_found", ["missing"]),
        (None, "openai/sora-2", "model_not_found", ["openai/sora-2"]),
        ("missing", "openai/sora-2", "invalid api key", ["missing"]),
    ],
)
async def test_video_generation_fallback(requested, default, message, expected_models):
    """AI-34: 模型不存在且默认模型不同才回退一次，其他错误原样传播。"""
    api = AIBotAPI(AIConfig(video_model=default))
    error = RuntimeError(message)
    response = MagicMock(id="video_test", status="queued")
    side_effect = [error, response] if len(expected_models) == 2 else error
    with patch("litellm.avideo_generation", AsyncMock(side_effect=side_effect)) as fn:
        if len(expected_models) == 2:
            assert await api.video_generation("a cat", model=requested) is response
        else:
            with pytest.raises(RuntimeError) as caught:
                await api.video_generation("a cat", model=requested)
            assert caught.value is error

    assert [c.kwargs["model"] for c in fn.await_args_list] == expected_models
    assert all(c.kwargs["prompt"] == "a cat" for c in fn.await_args_list)
    assert all("seconds" not in c.kwargs for c in fn.await_args_list)


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["video_status", "video_content"])
@pytest.mark.parametrize("fails", [False, True])
async def test_video_task_parameters_and_errors(action, fails):
    """AI-35: 查询/下载合并通用参数，保留完整 ID，无默认模型也可调用且不回退。"""
    api = AIBotAPI(
        AIConfig(api_key="config-key", base_url="https://config.example/v1", timeout=45)
    )
    response = (
        b"video-data" if action == "video_content" else MagicMock(status="failed")
    )
    error = RuntimeError("video does not exist")
    with patch(
        f"litellm.a{action}",
        AsyncMock(return_value=response, side_effect=error if fails else None),
    ) as fn:
        params = {
            "video_id": "encoded-provider-video-id",
            "api_key": "override-key",
            "custom_llm_provider": "gemini",
            "timeout": 90,
        }
        if fails:
            with pytest.raises(RuntimeError) as caught:
                await api.call(action, params)
            assert caught.value is error
        else:
            assert await api.call(action, params) is response
    fn.assert_awaited_once_with(api_base="https://config.example/v1", **params)


@pytest.mark.asyncio
@pytest.mark.parametrize("validation_fails", [False, True])
async def test_adapter_validates_video_model(validation_fails):
    """AI-36: 连接时验证视频默认模型；验证失败只记录警告，仍可连接。"""
    adapter = AIAdapter(config={"video_model": "openai/sora-2", "api_key": "test-key"})
    with patch(
        "litellm.validate_environment",
        return_value={"missing_keys": []},
        side_effect=RuntimeError("validation failed") if validation_fails else None,
    ) as validate:
        try:
            await adapter.connect()
            assert adapter.connected
            validate.assert_called_once_with("openai/sora-2")
        finally:
            await adapter.disconnect()
