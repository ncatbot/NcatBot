"""AIBotAPI — AI 平台 API 实现（基于 litellm）"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ncatbot.api.base import IAPIClient

if TYPE_CHECKING:
    from ncatbot.types import Image
from ncatbot.utils import get_log

from ..config import AIConfig

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
        content_or_messages: Union[str, List[dict]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Chat Completion

        Parameters
        ----------
        content_or_messages:
            - ``str``: 自动包装为 ``[{"role": "user", "content": str}]``
            - ``list[dict]``: 直接作为 messages 参数
        model:
            模型名（覆盖 ``completion_model``）。
        temperature:
            采样温度。
        max_tokens:
            最大生成 token 数（覆盖 config 的 ``max_tokens``）。

        Returns
        -------
        litellm.ModelResponse
            包含 ``choices[0].message.content`` 等字段。
        """
        from litellm import acompletion

        if isinstance(content_or_messages, str):
            messages = [{"role": "user", "content": content_or_messages}]
        else:
            messages = content_or_messages

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

        return await self._call_with_fallback(
            acompletion,
            resolved_model,
            self._config.completion_model,
            messages=messages,
            **call_kwargs,
        )

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
        content_or_messages: Union[str, List[dict]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
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
            **kwargs,
        )
        return resp.choices[0].message.content or ""

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
        from ncatbot.types import Image

        resp = await self.image_generation(prompt, model=model, size=size, **kwargs)
        image = resp.data[0]
        if image.url:
            return Image(file=image.url, url=image.url)
        return Image(file=f"base64://{image.b64_json}")
