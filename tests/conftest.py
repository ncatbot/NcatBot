"""
pytest fixtures — 提供 MockAdapter / TestHarness 等公共 fixture
"""

import pytest
import pytest_asyncio

from ncatbot.adapter.mock import MockAdapter
from ncatbot.testing import TestHarness


@pytest.fixture
def mock_adapter():
    """独立的 MockAdapter 实例（不启动 BotClient）"""
    return MockAdapter()


@pytest_asyncio.fixture
async def harness():
    """完整的 TestHarness：后台运行 BotClient + MockAdapter

    自动启动与停止，测试函数直接使用::

        async def test_xxx(harness):
            await harness.inject(...)
    """
    h = TestHarness()
    async with h:
        yield h
