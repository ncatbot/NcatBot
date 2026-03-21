"""AI 适配器配置模型"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AIConfig(BaseModel):
    """AI 适配器配置

    Parameters
    ----------
    api_key:
        API Key，为空时由 litellm 自动从环境变量读取
        （如 ``OPENAI_API_KEY``、``ANTHROPIC_API_KEY`` 等）。
    base_url:
        自定义 API 端点（兼容 DeepSeek / 通义千问 / Kimi 等国内 LLM）。
    completion_model:
        Chat Completion 默认模型（如 ``"gpt-4"``、``"deepseek-chat"``）。
    embedding_model:
        Embedding 默认模型（如 ``"text-embedding-3-small"``）。
    image_model:
        图像生成默认模型（如 ``"dall-e-3"``）。
    timeout:
        请求超时（秒）。
    max_tokens:
        默认最大 token 数，为 ``None`` 时由模型自行决定。
    """

    api_key: str = ""
    base_url: str = ""
    completion_model: str = ""
    embedding_model: str = ""
    image_model: str = ""
    timeout: float = 120.0
    max_tokens: Optional[int] = None
