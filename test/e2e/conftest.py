"""
E2E 测试全局配置
"""

import pytest


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
