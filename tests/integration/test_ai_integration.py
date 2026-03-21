"""
AI 适配器集成测试

规范:
  AI-I-01: AI 适配器注册到 BotAPIClient 后 api.ai 可访问
  AI-I-02: AI 适配器 platform 属性为 "ai"
  AI-I-03: AI 适配器 adapter_registry 发现
"""

from ncatbot.adapter.ai.adapter import AIAdapter
from ncatbot.adapter.ai.api.bot_api import AIBotAPI
from ncatbot.api.client import BotAPIClient


# ---- AI-I-01 ----


async def test_ai_registered_in_bot_api_client():
    """AI-I-01: AI 适配器的 API 注册到 BotAPIClient 后可通过 api.ai 访问"""
    from ncatbot.adapter.ai.config import AIConfig

    cfg = AIConfig(completion_model="gpt-4")
    ai_api = AIBotAPI(cfg)

    client = BotAPIClient()
    client.register_platform("ai", ai_api)

    assert client.ai is ai_api
    assert client.ai.platform == "ai"


# ---- AI-I-02 ----


async def test_ai_adapter_provides_correct_platform():
    """AI-I-02: AIAdapter.platform 和 AIBotAPI.platform 都返回 'ai'"""
    from unittest.mock import AsyncMock, patch

    adapter = AIAdapter(config={"completion_model": "gpt-4"})
    assert adapter.platform == "ai"

    with patch.object(adapter, "_validate_models", new_callable=AsyncMock):
        await adapter.connect()

    api = adapter.get_api()
    assert api.platform == "ai"

    await adapter.disconnect()


# ---- AI-I-03 ----


def test_ai_adapter_in_registry():
    """AI-I-03: AI 适配器在 adapter_registry 中可发现"""
    from ncatbot.adapter import adapter_registry

    available = adapter_registry.list_available()
    assert "ai" in available

    discovered = adapter_registry.discover()
    assert "ai" in discovered
    assert discovered["ai"] is AIAdapter
