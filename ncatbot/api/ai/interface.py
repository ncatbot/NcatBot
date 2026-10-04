"""IAIAPIClient — AI 平台 API 接口

定义 AI 适配器所有可用 API 方法。
由 AIBotAPI 实现。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union

from ..base import IAPIClient

if TYPE_CHECKING:
    from ncatbot.types import Image as ImageSegment
    from ncatbot.types.common.segment.array import MessageArray
    from ncatbot.types.common.segment.base import MessageSegment

ChatInput = Union[str, List[dict], "MessageArray", "MessageSegment"]


class IAIAPIClient(IAPIClient):
    """AI 平台 Bot API 接口"""

    # ---- Chat Completion ----

    @abstractmethod
    async def chat(
        self,
        content_or_messages: ChatInput,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        nickname_map: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[Dict[str, dict]] = None,
        max_tool_calls: int = 10,
        **kwargs: Any,
    ) -> Any:
        """Chat Completion

        Parameters
        ----------
        content_or_messages:
            - ``str``: 自动包装为 ``[{"role": "user", "content": str}]``
            - ``list[dict]``: 直接作为 messages 参数
            - ``MessageArray``: 自动转为多模态 content（文本 + 图片）
            - ``MessageSegment``: 单个消息段（Image / PlainText 等）
        model:
            覆盖 ``completion_model``。
        temperature:
            采样温度。
        max_tokens:
            最大生成 token 数。
        nickname_map:
            ``{user_id: 昵称}`` 映射，At 段转为可读文本。
        mcp_servers:
            MCP 服务器配置字典（格式见 ``AIConfig.mcp_servers``）。
            缺省使用配置中的 ``mcp_servers``；为空则不启用 MCP 工具。
        max_tool_calls:
            单轮对话中最多工具调用轮数（默认 10），防止死循环。

        Returns
        -------
        litellm.ModelResponse
        """

    # ---- Embeddings ----

    @abstractmethod
    async def embeddings(
        self,
        input_text: Union[str, List[str]],
        *,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """文本向量化

        Parameters
        ----------
        input_text:
            待嵌入的文本或文本列表。
        model:
            覆盖 ``embedding_model``。

        Returns
        -------
        litellm.EmbeddingResponse
        """

    # ---- Image Generation ----

    @abstractmethod
    async def image_generation(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """图像生成

        Parameters
        ----------
        prompt:
            图像描述文本。
        model:
            覆盖 ``image_model``。
        size:
            图像尺寸（如 ``"1024x1024"``）。

        Returns
        -------
        litellm.ImageResponse
        """

    # ---- Video Generation ----

    @abstractmethod
    async def video_generation(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        seconds: Optional[str] = None,
        size: Optional[str] = None,
        input_reference: Any = None,
        **kwargs: Any,
    ) -> Any:
        """提交视频生成任务，返回 LiteLLM VideoObject。

        ``model`` 覆盖 ``video_model``，模型不存在时回退到默认模型。
        ``seconds`` 是时长字符串（如 ``"8"``），``size`` 是尺寸（如
        ``"1280x720"``），``input_reference`` 是参考图像文件对象或字节。
        其他参数透传给 ``litellm.avideo_generation()``。
        用返回的 ``id`` 调用 ``video_status()``，完成后用 ``video_content()`` 下载。
        """

    @abstractmethod
    async def video_status(self, video_id: str, **kwargs: Any) -> Any:
        """查询视频任务，返回包含 status/progress/error 的 LiteLLM VideoObject。

        ``video_id`` 应保留生成响应的完整 ID，LiteLLM 据此路由到原提供商。
        不使用默认模型回退；其他参数透传给 ``litellm.avideo_status()``。
        """

    @abstractmethod
    async def video_content(self, video_id: str, **kwargs: Any) -> bytes:
        """下载已完成的视频，返回字节，不写入文件。

        ``video_id`` 应保留生成响应的完整 ID；其他参数（如 ``variant``）
        透传给 ``litellm.avideo_content()``。
        """

    # ---- Sugar 便捷方法 ----

    @abstractmethod
    async def chat_text(
        self,
        content_or_messages: ChatInput,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        nickname_map: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[Dict[str, dict]] = None,
        max_tool_calls: int = 10,
        **kwargs: Any,
    ) -> str:
        """Chat Completion — 直接返回文本

        与 ``chat()`` 参数相同，返回 ``choices[0].message.content``。
        """

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        **kwargs: Any,
    ) -> "ImageSegment":
        """图像生成 — 直接返回 Image 消息段

        与 ``image_generation()`` 参数相同，返回 ``ncatbot.types.Image``。
        """

    # ---- ASR (语音转文字) ----

    @abstractmethod
    async def transcription(
        self,
        file: Any,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: Optional[
            Literal["json", "text", "srt", "verbose_json", "vtt"]
        ] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Any:
        """语音转文字（ASR）

        Parameters
        ----------
        file:
            音频文件，支持文件路径 (``str`` / ``PathLike``)、
            字节 (``bytes``)、文件对象 (``IO[bytes]``) 等。
        model:
            覆盖 ``asr_model``。
        language:
            音频语言（ISO-639-1 格式，如 ``"zh"``、``"en"``）。
        prompt:
            可选提示文本，用于引导模型识别风格或补充上下文。
        response_format:
            响应格式：``"json"`` / ``"text"`` / ``"srt"`` / ``"verbose_json"`` / ``"vtt"``。
        temperature:
            采样温度。

        Returns
        -------
        litellm.TranscriptionResponse
            包含 ``text`` 字段。
        """

    @abstractmethod
    async def transcription_text(
        self,
        file: Any,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """语音转文字 — 直接返回文本

        与 ``transcription()`` 参数相同，返回识别出的纯文本。
        """
