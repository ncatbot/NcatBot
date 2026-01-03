"""
message_segments 子模块专用 pytest fixtures
"""

import pytest
from typing import Any, Dict, List


@pytest.fixture
def text_segments(data_provider) -> List[Dict[str, Any]]:
    """文本消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("text")
    if not segments:
        pytest.skip("测试数据不可用 - 无 text 类型消息段")
    return segments


@pytest.fixture
def image_segments(data_provider) -> List[Dict[str, Any]]:
    """图片消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("image")
    if not segments:
        pytest.skip("测试数据不可用 - 无 image 类型消息段")
    return segments


@pytest.fixture
def face_segments(data_provider) -> List[Dict[str, Any]]:
    """表情消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("face")
    if not segments:
        pytest.skip("测试数据不可用 - 无 face 类型消息段")
    return segments


@pytest.fixture
def at_segments(data_provider) -> List[Dict[str, Any]]:
    """@消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("at")
    if not segments:
        pytest.skip("测试数据不可用 - 无 at 类型消息段")
    return segments


@pytest.fixture
def reply_segments(data_provider) -> List[Dict[str, Any]]:
    """引用回复消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("reply")
    if not segments:
        pytest.skip("测试数据不可用 - 无 reply 类型消息段")
    return segments


@pytest.fixture
def forward_segments(data_provider) -> List[Dict[str, Any]]:
    """转发消息段数据（无数据时自动跳过测试）"""
    segments = data_provider.get_segments_by_type("forward")
    if not segments:
        pytest.skip("测试数据不可用 - 无 forward 类型消息段")
    return segments
