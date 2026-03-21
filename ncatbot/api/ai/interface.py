"""IAIAPIClient — AI 平台 API 接口

定义 AI 适配器所有可用 API 方法。
由 AIBotAPI 实现。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional, Union

from ncatbot.api.base import IAPIClient

if TYPE_CHECKING:
    from ncatbot.types import Image as ImageSegment


class IAIAPIClient(IAPIClient):
    """AI 平台 Bot API 接口"""

    # ---- Chat Completion ----

    @abstractmethod
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
            ``str`` 时自动包装为 ``[{"role": "user", "content": str}]``；
            ``list[dict]`` 直接作为 messages。
        model:
            覆盖 ``completion_model``。
        temperature:
            采样温度。
        max_tokens:
            最大生成 token 数。

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

    # ---- Sugar 便捷方法 ----

    @abstractmethod
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
