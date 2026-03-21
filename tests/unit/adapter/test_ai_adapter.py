"""
AI 适配器单元测试

规范:
  AI-01: AIConfig 默认值正确
  AI-02: AIConfig 分功能默认模型独立设置
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
"""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from ncatbot.adapter.ai.config import AIConfig
from ncatbot.adapter.ai.api.bot_api import AIBotAPI
from ncatbot.adapter.ai.adapter import AIAdapter
from ncatbot.types import Image


# ---- AI-01 ----


def test_ai_config_defaults():
    """AI-01: AIConfig 默认值正确"""
    cfg = AIConfig()
    assert cfg.api_key == ""
    assert cfg.base_url == ""
    assert cfg.completion_model == ""
    assert cfg.embedding_model == ""
    assert cfg.image_model == ""
    assert cfg.timeout == 120.0
    assert cfg.max_tokens is None


# ---- AI-02 ----


def test_ai_config_per_capability_models():
    """AI-02: 各功能默认模型可独立设置"""
    cfg = AIConfig(
        completion_model="gpt-4",
        embedding_model="text-embedding-3-small",
        image_model="dall-e-3",
    )
    assert cfg.completion_model == "gpt-4"
    assert cfg.embedding_model == "text-embedding-3-small"
    assert cfg.image_model == "dall-e-3"


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
