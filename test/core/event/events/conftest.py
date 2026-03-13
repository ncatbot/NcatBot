"""
events 子模块专用 pytest fixtures
"""

import pytest
from typing import Any, Dict, List


class MockBotAPI:
    """用于测试的 Mock Bot API，实现 IBotAPI 接口"""

    def __init__(self):
        self.calls: List[tuple] = []  # 记录所有 API 调用

    async def send_group_msg(self, group_id, message, **kwargs):
        self.calls.append(("send_group_msg", group_id, message, kwargs))
        return {"message_id": "mock_group_msg_123"}

    async def send_private_msg(self, user_id, message, **kwargs):
        self.calls.append(("send_private_msg", user_id, message, kwargs))
        return {"message_id": "mock_private_msg_123"}

    async def delete_msg(self, message_id):
        self.calls.append(("delete_msg", message_id))
        return {}

    async def send_forward_msg(self, message_type, target_id, messages, **kwargs):
        self.calls.append(
            ("send_forward_msg", message_type, target_id, messages, kwargs)
        )
        return {}

    async def set_group_kick(self, group_id, user_id, reject_add_request=False):
        self.calls.append(("set_group_kick", group_id, user_id, reject_add_request))
        return {}

    async def set_group_ban(self, group_id, user_id, duration=30 * 60):
        self.calls.append(("set_group_ban", group_id, user_id, duration))
        return {}

    async def set_group_whole_ban(self, group_id, enable=True):
        self.calls.append(("set_group_whole_ban", group_id, enable))
        return {}

    async def set_group_admin(self, group_id, user_id, enable=True):
        self.calls.append(("set_group_admin", group_id, user_id, enable))
        return {}

    async def set_group_card(self, group_id, user_id, card=""):
        self.calls.append(("set_group_card", group_id, user_id, card))
        return {}

    async def set_group_name(self, group_id, name):
        self.calls.append(("set_group_name", group_id, name))
        return {}

    async def set_group_leave(self, group_id, is_dismiss=False):
        self.calls.append(("set_group_leave", group_id, is_dismiss))
        return {}

    async def set_group_special_title(self, group_id, user_id, special_title=""):
        self.calls.append(("set_group_special_title", group_id, user_id, special_title))
        return {}

    async def set_friend_add_request(self, flag, approve=True, remark=""):
        self.calls.append(("set_friend_add_request", flag, approve, remark))
        return {}

    async def set_group_add_request(self, flag, sub_type, approve=True, reason=""):
        self.calls.append(("set_group_add_request", flag, sub_type, approve, reason))
        return {}

    async def get_login_info(self):
        return {"user_id": 12345, "nickname": "test"}

    async def get_stranger_info(self, user_id):
        return {}

    async def get_friend_list(self):
        return []

    async def get_group_info(self, group_id):
        return {}

    async def get_group_list(self):
        return []

    async def get_group_member_info(self, group_id, user_id):
        return {}

    async def get_group_member_list(self, group_id):
        return []

    async def get_msg(self, message_id):
        return {}

    async def get_forward_msg(self, message_id):
        return {}

    async def upload_group_file(self, group_id, file, name, folder_id=""):
        return {}

    async def get_group_root_files(self, group_id):
        return {}

    async def get_group_file_url(self, group_id, file_id):
        return ""

    async def delete_group_file(self, group_id, file_id):
        return {}

    async def send_like(self, user_id, times=1):
        return {}

    async def send_poke(self, group_id, user_id):
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
