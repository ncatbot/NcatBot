"""
MockBotAPI — IBotAPI 的内存实现

记录所有 API 调用，返回可配置的模拟响应，不进行任何网络通信。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ncatbot.api.interface import IBotAPI


@dataclass
class APICall:
    """一次 API 调用的记录"""

    action: str
    args: tuple
    kwargs: dict


class MockBotAPI(IBotAPI):
    """IBotAPI 的完整 Mock 实现

    使用方式::

        api = MockBotAPI()

        # 设置特定 action 的返回值
        api.set_response("send_group_msg", {"message_id": "123"})

        # 执行调用
        result = await api.send_group_msg(12345, [{"type": "text", "data": {"text": "hi"}}])

        # 检查调用记录
        assert api.called("send_group_msg")
        assert api.call_count("send_group_msg") == 1
    """

    def __init__(self) -> None:
        self._calls: List[APICall] = []
        self._responses: Dict[str, Any] = {}
        self._default_response: dict = {}

    # ---- 调用记录与断言 ----

    def set_response(self, action: str, response: Any) -> None:
        """预设某个 action 的返回值"""
        self._responses[action] = response

    def _record(self, action: str, *args: Any, **kwargs: Any) -> Any:
        self._calls.append(APICall(action=action, args=args, kwargs=kwargs))
        return self._responses.get(action, self._default_response)

    @property
    def calls(self) -> List[APICall]:
        return list(self._calls)

    def called(self, action: str) -> bool:
        return any(c.action == action for c in self._calls)

    def call_count(self, action: str) -> int:
        return sum(1 for c in self._calls if c.action == action)

    def get_calls(self, action: str) -> List[APICall]:
        return [c for c in self._calls if c.action == action]

    def last_call(self, action: Optional[str] = None) -> Optional[APICall]:
        if action:
            matching = self.get_calls(action)
            return matching[-1] if matching else None
        return self._calls[-1] if self._calls else None

    def reset(self) -> None:
        self._calls.clear()

    # ---- IBotAPI 实现 ----

    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        return self._record("send_private_msg", user_id, message, **kwargs)

    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        return self._record("send_group_msg", group_id, message, **kwargs)

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        self._record("delete_msg", message_id)

    async def send_forward_msg(
        self, message_type: str, target_id: Union[str, int], messages: list, **kwargs
    ) -> dict:
        return self._record(
            "send_forward_msg", message_type, target_id, messages, **kwargs
        )

    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        self._record("set_group_kick", group_id, user_id, reject_add_request)

    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 1800,
    ) -> None:
        self._record("set_group_ban", group_id, user_id, duration)

    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        self._record("set_group_whole_ban", group_id, enable)

    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        self._record("set_group_admin", group_id, user_id, enable)

    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        self._record("set_group_card", group_id, user_id, card)

    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        self._record("set_group_name", group_id, name)

    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        self._record("set_group_leave", group_id, is_dismiss)

    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        self._record("set_group_special_title", group_id, user_id, special_title)

    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        self._record("set_friend_add_request", flag, approve, remark)

    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ) -> None:
        self._record("set_group_add_request", flag, sub_type, approve, reason)

    async def get_login_info(self) -> dict:
        return self._record("get_login_info")

    async def get_stranger_info(self, user_id: Union[str, int]) -> dict:
        return self._record("get_stranger_info", user_id)

    async def get_friend_list(self) -> list:
        return self._record("get_friend_list")

    async def get_group_info(self, group_id: Union[str, int]) -> dict:
        return self._record("get_group_info", group_id)

    async def get_group_list(self) -> list:
        return self._record("get_group_list")

    async def get_group_member_info(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> dict:
        return self._record("get_group_member_info", group_id, user_id)

    async def get_group_member_list(self, group_id: Union[str, int]) -> list:
        return self._record("get_group_member_list", group_id)

    async def get_msg(self, message_id: Union[str, int]) -> dict:
        return self._record("get_msg", message_id)

    async def get_forward_msg(self, message_id: Union[str, int]) -> dict:
        return self._record("get_forward_msg", message_id)

    async def upload_group_file(
        self, group_id: Union[str, int], file: str, name: str, folder_id: str = ""
    ) -> None:
        self._record("upload_group_file", group_id, file, name, folder_id)

    async def get_group_root_files(self, group_id: Union[str, int]) -> dict:
        return self._record("get_group_root_files", group_id)

    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        return self._record("get_group_file_url", group_id, file_id)

    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        self._record("delete_group_file", group_id, file_id)

    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        self._record("send_like", user_id, times)

    async def send_poke(
        self, group_id: Union[str, int], user_id: Union[str, int]
    ) -> None:
        self._record("send_poke", group_id, user_id)
