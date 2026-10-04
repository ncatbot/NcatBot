"""
AIAdapter — 基于 litellm 的 AI 平台适配器

不需要显式启动外部服务，仅提供 API 调用能力。
通过 ``api.ai.chat()`` / ``api.ai.embeddings()`` / ``api.ai.image_generation()``
/ ``api.ai.video_generation()`` / ``api.ai.transcription()`` 调用模型提供商。
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from ..base import BaseAdapter
from ncatbot.api import IAPIClient
from ncatbot.utils import get_log

from .config import AIConfig
from .api import AIBotAPI

LOG = get_log("AIAdapter")


def _parse_kv(text: str, sep: str = "=") -> Dict[str, str]:
    """解析 ``KEY=VALUE`` 逗号分隔文本为字典。"""
    result: Dict[str, str] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition(sep)
        key = key.strip()
        if key:
            result[key] = value.strip()
    return result


def _parse_headers(text: str) -> Dict[str, str]:
    """解析 ``Key:Value`` 逗号分隔文本为请求头字典。"""
    return _parse_kv(text, sep=":")


class AIAdapter(BaseAdapter):
    """AI 适配器 — 通过 litellm 统一调用 100+ LLM 提供商

    使用方式::

        # config.yaml
        adapters:
          - type: ai
            platform: ai
            config:
              api_key: "sk-xxx"
              completion_model: "gpt-4"
              embedding_model: "text-embedding-3-small"

        # 在插件中使用
        resp = await self.api.ai.chat("你好")
        print(resp.choices[0].message.content)
    """

    name = "ai"
    description = "AI 适配器（基于 litellm 的多模型统一接口）"
    supported_protocols: List[str] = ["litellm"]
    platform = "ai"
    pip_dependencies: Dict[str, str] = {
        "litellm": ">=1.83.0",
        "mcp": ">=1.25.0,<2.0.0",
    }

    @classmethod
    def cli_configure(cls) -> Dict[str, Any]:
        import click

        click.echo(click.style("\n— AI 适配器配置 —", fg="cyan", bold=True))
        click.echo(
            click.style(
                "  支持 OpenAI / DeepSeek / Qwen / Kimi 等，留空使用环境变量",
                dim=True,
            )
        )
        api_key = click.prompt("API Key", default="", show_default=False)
        base_url = click.prompt("API Base URL", default="", show_default=False)
        completion_model = click.prompt(
            "Completion Model", default="", show_default=False
        )

        cfg: Dict[str, Any] = {}
        if api_key:
            cfg["api_key"] = api_key
        if base_url:
            cfg["base_url"] = base_url
        if completion_model:
            cfg["completion_model"] = completion_model

        mcp_servers = cls._cli_configure_mcp()
        if mcp_servers:
            cfg["mcp_servers"] = mcp_servers
        return cfg

    @classmethod
    def _cli_configure_mcp(cls) -> Dict[str, Any]:
        """交互式收集 MCP 服务器配置（LiteLLM 兼容格式）。"""
        import click

        servers: Dict[str, Any] = {}
        if not click.confirm(
            "是否添加 MCP 服务器（让模型调用外部工具）?", default=False
        ):
            return servers

        while True:
            click.echo(
                click.style(
                    "\n  ── MCP 服务器 ──\n"
                    "  传输类型: http (Streamable HTTP) / sse / stdio\n"
                    "  http/sse 需 URL，stdio 需 command + args",
                    dim=True,
                )
            )
            name = click.prompt("服务器名称（如 deepwiki）").strip()
            if not name:
                click.echo(click.style("服务器名称不能为空，已跳过", fg="yellow"))
                continue

            transport = click.prompt(
                "传输类型", type=click.Choice(["http", "sse", "stdio"]), default="http"
            )

            entry: Dict[str, Any] = {"transport": transport}
            if transport == "stdio":
                command = click.prompt("启动命令（如 npx / uvx）")
                entry["command"] = command
                args = click.prompt(
                    "参数（空格分隔，可直接回车跳过）",
                    default="",
                    show_default=False,
                )
                if args:
                    entry["args"] = args.split()
                env = click.prompt(
                    "环境变量（逗号分隔 KEY=VALUE，可回车跳过）",
                    default="",
                    show_default=False,
                )
                parsed_env = _parse_kv(env)
                if parsed_env:
                    entry["env"] = parsed_env
            else:
                url = click.prompt("MCP 服务器 URL")
                entry["url"] = url
                headers = click.prompt(
                    "请求头（逗号分隔 Key:Value，可回车跳过）",
                    default="",
                    show_default=False,
                )
                parsed_headers = _parse_headers(headers)
                if parsed_headers:
                    entry["headers"] = parsed_headers

            servers[name] = entry
            if not click.confirm("继续添加 MCP 服务器?", default=False):
                break

        return servers

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._ai_config = AIConfig(**self._raw_config)
        self._bot_api: Optional[AIBotAPI] = None
        self._connected = False
        self._stop_event: Optional[asyncio.Event] = None

    # ---- 生命周期 ----

    async def setup(self) -> None:
        """验证配置：确保至少有 API Key 可用"""
        has_key = bool(self._ai_config.api_key)
        has_env = any(
            os.environ.get(k)
            for k in (
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
                "AZURE_API_KEY",
                "GEMINI_API_KEY",
                "DEEPSEEK_API_KEY",
            )
        )
        if not has_key and not has_env:
            LOG.warning(
                "AI 适配器未配置 api_key 且未检测到相关环境变量，API 调用可能失败"
            )

    async def connect(self) -> None:
        """创建 AIBotAPI 实例并验证模型可用性"""
        self._bot_api = AIBotAPI(self._ai_config)
        self._stop_event = asyncio.Event()
        self._connected = True

        # 验证模型可用性
        await self._validate_models()

        LOG.info("AI 适配器已就绪")

    async def disconnect(self) -> None:
        self._connected = False
        if self._stop_event:
            self._stop_event.set()

    async def listen(self) -> None:
        """阻塞直到 disconnect() 被调用（AI 适配器不产生事件）"""
        if self._stop_event is None:
            raise RuntimeError("AIAdapter 尚未 connect")
        await self._stop_event.wait()

    def get_api(self) -> IAPIClient:
        if self._bot_api is None:
            raise RuntimeError("AIAdapter 尚未 connect")
        return self._bot_api

    @property
    def connected(self) -> bool:
        return self._connected

    # ---- 模型验证 ----

    async def _validate_models(self) -> None:
        """启动时验证配置的默认模型是否存在"""
        from litellm import validate_environment

        models = {
            "completion_model": self._ai_config.completion_model,
            "embedding_model": self._ai_config.embedding_model,
            "image_model": self._ai_config.image_model,
            "video_model": self._ai_config.video_model,
            "asr_model": self._ai_config.asr_model,
        }
        for label, model_name in models.items():
            if not model_name:
                continue
            try:
                result = validate_environment(model_name)
                missing = result.get("missing_keys", [])
                if missing:
                    LOG.warning(
                        "%s (%s) 缺少环境变量: %s",
                        label,
                        model_name,
                        missing,
                    )
                else:
                    LOG.info("%s (%s) 验证通过", label, model_name)
            except Exception as exc:
                LOG.warning(
                    "%s (%s) 验证失败: %s",
                    label,
                    model_name,
                    exc,
                )
