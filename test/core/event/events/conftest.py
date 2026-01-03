"""
events 子模块专用 pytest fixtures
"""

import pytest
from typing import Any, Dict, List


class MockBotAPI:
    """用于测试的 Mock Bot API，实现 IBotAPI 协议"""

    def __init__(self):
        self.calls: List[tuple] = []  # 记录所有 API 调用

    async def post_group_msg(self, group_id: str, text: str, **kwargs):
        self.calls.append(("post_group_msg", group_id, text, kwargs))
        return {"message_id": "mock_group_msg_123"}

    async def post_private_msg(self, user_id: str, text: str, **kwargs):
        self.calls.append(("post_private_msg", user_id, text, kwargs))
        return {"message_id": "mock_private_msg_123"}

    async def delete_msg(self, message_id: str):
        self.calls.append(("delete_msg", message_id))
        return {}

    async def set_group_kick(
        self, group_id: str, user_id: str, reject_add_request: bool = False
    ):
        self.calls.append(("set_group_kick", group_id, user_id, reject_add_request))
        return {}

    async def set_group_ban(self, group_id: str, user_id: str, duration: int = 30 * 60):
        self.calls.append(("set_group_ban", group_id, user_id, duration))
        return {}

    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ):
        self.calls.append(("set_friend_add_request", flag, approve, remark))
        return {}

    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ):
        self.calls.append(("set_group_add_request", flag, sub_type, approve, reason))
        return {}

    def clear_calls(self):
        """清空调用记录"""
        self.calls.clear()

    def get_last_call(self):
        """获取最后一次调用"""
        return self.calls[-1] if self.calls else None


@pytest.fixture
def mock_api() -> MockBotAPI:
    """提供 Mock Bot API 实例"""
    return MockBotAPI()


@pytest.fixture
def private_message_events(data_provider) -> List[Dict[str, Any]]:
    """私聊消息事件数据"""
    events = data_provider.get_events_by_type("message", "private")
    if not events:
        pytest.skip("测试数据不可用 - 无私聊消息事件")
    return events


@pytest.fixture
def group_message_events(data_provider) -> List[Dict[str, Any]]:
    """群消息事件数据"""
    events = data_provider.get_events_by_type("message", "group")
    if not events:
        pytest.skip("测试数据不可用 - 无群消息事件")
    return events


@pytest.fixture
def heartbeat_events(data_provider) -> List[Dict[str, Any]]:
    """心跳元事件数据"""
    events = data_provider.get_events_by_type("meta_event", "heartbeat")
    if not events:
        pytest.skip("测试数据不可用 - 无心跳事件")
    return events


@pytest.fixture
def lifecycle_events(data_provider) -> List[Dict[str, Any]]:
    """生命周期元事件数据"""
    events = data_provider.get_events_by_type("meta_event", "lifecycle")
    if not events:
        pytest.skip("测试数据不可用 - 无生命周期事件")
    return events


@pytest.fixture
def poke_events(data_provider) -> List[Dict[str, Any]]:
    """戳一戳通知事件数据"""
    events = data_provider.get_notice_events_by_subtype("poke")
    if not events:
        pytest.skip("测试数据不可用 - 无戳一戳事件")
    return events


@pytest.fixture
def notice_events(data_provider) -> List[Dict[str, Any]]:
    """所有通知事件数据"""
    events = data_provider.get_events_by_post_type("notice")
    if not events:
        pytest.skip("测试数据不可用 - 无通知事件")
    return events
