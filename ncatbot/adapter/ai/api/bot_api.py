"""AIBotAPI — AI 平台 API 实现（基于 litellm）"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from ncatbot.api.base import IAPIClient
from ncatbot.types import (
    At,
    DownloadableSegment,
    Image,
    MessageArray,
    MessageSegment,
    PlainText,
    Reply,
)
from ncatbot.utils import get_log

from ..config import AIConfig
from .mcp import MCPSessionManager

# 接受的输入类型：str / list[dict] / MessageArray / 单个 MessageSegment
ChatInput = Union[str, List[dict], "MessageArray", "MessageSegment"]

LOG = get_log("AIBotAPI")


class AIBotAPI(IAPIClient):
    """AI 平台 API 实现

    通过 litellm 统一接口调用 100+ LLM 提供商。
    每个方法合并 config 默认值与调用时参数（调用时参数优先）。
    当指定的模型不存在时，自动回退到配置中的默认模型。
    """

    def __init__(self, config: AIConfig) -> None:
        self._config = config
        self._common_kwargs: Dict[str, Any] = {}
        if config.api_key:
            self._common_kwargs["api_key"] = config.api_key
        if config.base_url:
            self._common_kwargs["api_base"] = config.base_url
        if config.timeout:
            self._common_kwargs["timeout"] = config.timeout

    @property
    def platform(self) -> str:
        return "ai"

    async def call(self, action: str, params: Optional[dict] = None) -> Any:
        """通用 API 调用入口 — 按 action 名分派到对应方法"""
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"未知的 AI API action: {action}")
        if params:
            return await method(**params)
        return await method()

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
            模型名（覆盖 ``completion_model``）。
        temperature:
            采样温度。
        max_tokens:
            最大生成 token 数（覆盖 config 的 ``max_tokens``）。
        nickname_map:
            ``{user_id: 昵称}`` 映射，用于将 ``At`` 段转为可读文本。
            缺省时 At 段渲染为 ``@{user_id}``。
        mcp_servers:
            MCP 服务器配置字典（格式见 ``AIConfig.mcp_servers``）。
            缺省使用配置中的 ``mcp_servers``；为空则不启用 MCP 工具。
            启用后模型可调用 MCP 工具，工具名按 ``{server}_{tool}`` 命名空间区分。
        max_tool_calls:
            单轮对话中允许的最多工具调用轮数（默认 10），防止死循环。

        Returns
        -------
        litellm.ModelResponse
            包含 ``choices[0].message.content`` 等字段。
        """
        from litellm import acompletion

        messages = self._normalize_messages(content_or_messages, nickname_map)

        resolved_model = model or self._config.completion_model
        if not resolved_model:
            raise ValueError(
                "未指定模型：请通过参数 model= 或配置 completion_model 设置"
            )

        call_kwargs = {**self._common_kwargs, **kwargs}
        if temperature is not None:
            call_kwargs["temperature"] = temperature
        resolved_max_tokens = max_tokens or self._config.max_tokens
        if resolved_max_tokens is not None:
            call_kwargs["max_tokens"] = resolved_max_tokens

        merged_mcp_servers = (
            mcp_servers if mcp_servers is not None else self._config.mcp_servers
        )
        if not merged_mcp_servers:
            return await self._call_with_fallback(
                acompletion,
                resolved_model,
                self._config.completion_model,
                messages=messages,
                **call_kwargs,
            )

        return await self._chat_with_tools(
            acompletion,
            resolved_model,
            self._config.completion_model,
            messages,
            merged_mcp_servers,
            max_tool_calls,
            call_kwargs,
        )

    async def _chat_with_tools(
        self,
        acompletion: Any,
        model: str,
        default_model: str,
        messages: List[dict],
        mcp_servers: Dict[str, dict],
        max_tool_calls: int,
        call_kwargs: Dict[str, Any],
    ) -> Any:
        """带 MCP 工具调用循环的 Chat Completion。

        模型请求工具 → 执行 MCP 工具 → 回传结果 → 继续对话，
        直到模型不再请求工具或达到 ``max_tool_calls`` 上限。
        """
        async with MCPSessionManager(mcp_servers) as mcp:
            tools = await mcp.load_tools()
            if not tools:
                LOG.warning("MCP 服务器未加载到任何工具，按普通对话处理（无 tools）")
                return await self._call_with_fallback(
                    acompletion,
                    model,
                    default_model,
                    messages=messages,
                    **call_kwargs,
                )

            msgs = list(messages)
            resp: Any = None
            for _ in range(max_tool_calls):
                resp = await self._call_with_fallback(
                    acompletion,
                    model,
                    default_model,
                    messages=msgs,
                    tools=tools,
                    **call_kwargs,
                )
                message = resp.choices[0].message
                tool_calls = getattr(message, "tool_calls", None)
                if not tool_calls:
                    return resp

                msgs.append(self._assistant_tool_message(message, tool_calls))
                for tool_call in tool_calls:
                    try:
                        result_text = await mcp.call_openai_tool(tool_call)
                    except Exception as exc:  # noqa: BLE001
                        LOG.error("MCP 工具调用失败: %s", exc)
                        result_text = f"[MCP 工具调用失败: {exc}]"
                    msgs.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text,
                        }
                    )

            LOG.warning("MCP 工具调用达到上限 %d 轮，返回最后一次响应", max_tool_calls)
            return resp

    @staticmethod
    def _assistant_tool_message(message: Any, tool_calls: List[Any]) -> dict:
        """构造带 tool_calls 的 assistant 消息，供下一轮请求使用。"""
        dumped = []
        for tc in tool_calls:
            if hasattr(tc, "model_dump"):
                dumped.append(tc.model_dump())
            else:
                dumped.append(dict(tc))
        return {
            "role": "assistant",
            "content": getattr(message, "content", None),
            "tool_calls": dumped,
        }

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
            模型名（覆盖 ``embedding_model``）。

        Returns
        -------
        litellm.EmbeddingResponse
            包含 ``data[i].embedding`` 向量列表。
        """
        from litellm import aembedding

        resolved_model = model or self._config.embedding_model
        if not resolved_model:
            raise ValueError(
                "未指定模型：请通过参数 model= 或配置 embedding_model 设置"
            )

        call_kwargs = {**self._common_kwargs, **kwargs}

        return await self._call_with_fallback(
            aembedding,
            resolved_model,
            self._config.embedding_model,
            input=input_text,
            **call_kwargs,
        )

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
            模型名（覆盖 ``image_model``）。
        size:
            图像尺寸（如 ``"1024x1024"``）。

        Returns
        -------
        litellm.ImageResponse
            包含 ``data[i].url`` 或 ``data[i].b64_json``。
        """
        from litellm import aimage_generation

        resolved_model = model or self._config.image_model
        if not resolved_model:
            raise ValueError("未指定模型：请通过参数 model= 或配置 image_model 设置")

        call_kwargs = {**self._common_kwargs, **kwargs}
        if size is not None:
            call_kwargs["size"] = size

        return await self._call_with_fallback(
            aimage_generation,
            resolved_model,
            self._config.image_model,
            prompt=prompt,
            **call_kwargs,
        )

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

        ``model`` 覆盖 ``video_model``；``seconds`` 为时长字符串（如 ``"8"``），
        ``size`` 为尺寸，``input_reference`` 为参考图像文件对象或字节。
        返回任务的 ``id`` 和 ``status``，用 ``video_status()`` 查询完成状态，
        完成后用 ``video_content()`` 下载。提供商参数通过 ``kwargs`` 透传。
        """
        from litellm import avideo_generation

        resolved_model = model or self._config.video_model
        if not resolved_model:
            raise ValueError("未指定模型：请通过参数 model= 或配置 video_model 设置")

        call_kwargs: Dict[str, Any] = {**self._common_kwargs, **kwargs}
        if seconds is not None:
            call_kwargs["seconds"] = seconds
        if size is not None:
            call_kwargs["size"] = size
        if input_reference is not None:
            call_kwargs["input_reference"] = input_reference

        return await self._call_with_fallback(
            avideo_generation,
            resolved_model,
            self._config.video_model,
            prompt=prompt,
            **call_kwargs,
        )

    async def video_status(self, video_id: str, **kwargs: Any) -> Any:
        """查询视频任务，返回 LiteLLM VideoObject（status/progress/error）。

        保留原始任务 ID，让 LiteLLM 路由到原提供商，不使用默认模型回退。
        """
        from litellm import avideo_status

        return await avideo_status(
            video_id=video_id, **{**self._common_kwargs, **kwargs}
        )

    async def video_content(self, video_id: str, **kwargs: Any) -> bytes:
        """下载已完成的视频字节，不写入文件；variant 等参数透传给 LiteLLM。"""
        from litellm import avideo_content

        return await avideo_content(
            video_id=video_id, **{**self._common_kwargs, **kwargs}
        )

    async def _call_with_fallback(
        self,
        func: Any,
        model: str,
        default_model: str,
        **kwargs: Any,
    ) -> Any:
        """调用 litellm 函数，模型不存在时回退到默认模型"""
        try:
            return await func(model=model, **kwargs)
        except Exception as exc:
            if not self._is_model_not_found(exc):
                raise
            if not default_model or model == default_model:
                raise
            LOG.warning("模型 %s 不存在，回退到默认模型 %s", model, default_model)
            return await func(model=default_model, **kwargs)

    @staticmethod
    def _is_model_not_found(exc: Exception) -> bool:
        """判断异常是否为模型不存在错误"""
        msg = str(exc).lower()
        return any(
            keyword in msg
            for keyword in ("model_not_found", "model not found", "does not exist")
        )

    # ---- Sugar 便捷方法 ----

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

        参数与 ``chat()`` 相同，返回 ``choices[0].message.content``。
        """
        resp = await self.chat(
            content_or_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            nickname_map=nickname_map,
            mcp_servers=mcp_servers,
            max_tool_calls=max_tool_calls,
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    # ---- 输入归一化 ----

    def _normalize_messages(
        self,
        content_or_messages: ChatInput,
        nickname_map: Optional[Dict[str, str]] = None,
    ) -> List[dict]:
        """将各种输入格式统一为 ``list[dict]`` (OpenAI messages 格式)"""
        if isinstance(content_or_messages, str):
            return [{"role": "user", "content": content_or_messages}]

        if isinstance(content_or_messages, list):
            return content_or_messages  # list[dict] 透传

        if isinstance(content_or_messages, MessageSegment):
            # 单个消息段 → 包装为 MessageArray 再转
            arr = MessageArray([content_or_messages])
            content = self._convert_message_array(arr, nickname_map)
            return [{"role": "user", "content": content}]

        if isinstance(content_or_messages, MessageArray):
            content = self._convert_message_array(content_or_messages, nickname_map)
            return [{"role": "user", "content": content}]

        raise TypeError(
            f"不支持的输入类型: {type(content_or_messages).__name__}，"
            "请传入 str / list[dict] / MessageArray / MessageSegment"
        )

    def _convert_message_array(
        self,
        msg_array: MessageArray,
        nickname_map: Optional[Dict[str, str]] = None,
    ) -> Union[str, List[dict]]:
        """将 MessageArray 转为 OpenAI content 格式

        纯文本时返回 str；包含图片时返回多模态 content list。
        """
        parts: list[dict] = []
        has_image = False

        for seg in msg_array:
            if isinstance(seg, PlainText):
                parts.append({"type": "text", "text": seg.text})

            elif isinstance(seg, Image):
                has_image = True
                url = seg.url or seg.file
                # base64:// 前缀转为 data URI
                if url.startswith("base64://"):
                    url = f"data:image/png;base64,{url[9:]}"
                parts.append({"type": "image_url", "image_url": {"url": url}})

            elif isinstance(seg, At):
                nick = nickname_map.get(seg.user_id) if nickname_map else None
                display = f"@{nick}" if nick else f"@{seg.user_id}"
                parts.append({"type": "text", "text": display})

            elif isinstance(seg, Reply):
                parts.append({"type": "text", "text": f"[回复消息 id={seg.id}]"})

            elif isinstance(seg, DownloadableSegment):
                # Video / File / Record — 不可序列化给 LLM
                LOG.warning(
                    "AI chat: 跳过不支持的媒体段 %s (file=%s)",
                    type(seg).__name__,
                    getattr(seg, "file", "?"),
                )

            else:
                # Face / Share / Location / Forward / Json / Markdown 等
                LOG.warning(
                    "AI chat: 跳过不支持的消息段 %s",
                    type(seg).__name__,
                )

        if not parts:
            return ""

        # 纯文本优化：拼成普通字符串，避免不必要的多模态格式
        if not has_image:
            return "".join(p["text"] for p in parts)

        return parts

    async def generate_image(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        size: Optional[str] = None,
        **kwargs: Any,
    ) -> Image:
        """图像生成 — 直接返回 Image 消息段

        参数与 ``image_generation()`` 相同，返回 ``ncatbot.types.Image``。
        URL 响应设为 ``file``，b64_json 响应使用 ``base64://`` 前缀。
        """
        resp = await self.image_generation(prompt, model=model, size=size, **kwargs)
        image = resp.data[0]
        if image.url:
            return Image(file=image.url, url=image.url)
        return Image(file=f"base64://{image.b64_json}")

    # ---- ASR (语音转文字) ----

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
            模型名（覆盖 ``asr_model``）。
        language:
            音频语言（ISO-639-1 格式，如 ``"zh"``、``"en"``）。
        prompt:
            可选提示文本，用于引导模型识别。
        response_format:
            响应格式。
        temperature:
            采样温度。

        Returns
        -------
        litellm.TranscriptionResponse
            包含 ``text`` 字段。
        """
        from litellm import atranscription

        resolved_model = model or self._config.asr_model
        if not resolved_model:
            raise ValueError("未指定模型：请通过参数 model= 或配置 asr_model 设置")

        call_kwargs: Dict[str, Any] = {**self._common_kwargs, **kwargs}
        if language is not None:
            call_kwargs["language"] = language
        if prompt is not None:
            call_kwargs["prompt"] = prompt
        if response_format is not None:
            call_kwargs["response_format"] = response_format
        if temperature is not None:
            call_kwargs["temperature"] = temperature

        return await self._call_with_fallback(
            atranscription,
            resolved_model,
            self._config.asr_model,
            file=file,
            **call_kwargs,
        )

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

        参数与 ``transcription()`` 相同，返回识别出的纯文本。
        """
        resp = await self.transcription(
            file,
            model=model,
            language=language,
            prompt=prompt,
            temperature=temperature,
            **kwargs,
        )
        return resp.text or ""
