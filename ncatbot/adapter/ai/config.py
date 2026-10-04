"""AI 适配器配置模型"""

from __future__ import annotations

from typing import Any, Dict, Optional

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
    video_model:
        视频生成默认模型（如 ``"openai/sora-2"``）。
    timeout:
        请求超时（秒）。
    max_tokens:
        默认最大 token 数，为 ``None`` 时由模型自行决定。
    mcp_servers:
        MCP 服务器配置（配置格式与 LiteLLM 兼容），``chat()`` 时自动加载
        其工具供模型调用。格式::

            mcp_servers:
              server_name:
                transport: "http" | "sse" | "stdio"  # 缺省自动判断
                url: "https://mcp.example.com/mcp"   # http / sse
                headers: {Authorization: "Bearer ..."}  # http / sse
                command: "npx"                        # stdio
                args: ["-y", "@mcp/server"]           # stdio
                env: {TOKEN: "..."}                   # stdio
    """

    api_key: str = ""
    base_url: str = ""
    completion_model: str = ""
    embedding_model: str = ""
    image_model: str = ""
    video_model: str = ""
    asr_model: str = ""
    timeout: float = 120.0
    max_tokens: Optional[int] = None
    mcp_servers: Dict[str, Any] = {}
