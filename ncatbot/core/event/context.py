from typing import Protocol, Any, Optional
from pydantic import BaseModel, PrivateAttr


class IBotAPI(Protocol):
    """定义 Bot API 的必要接口"""

    async def post_group_msg(self, group_id: str, text: str, **kwargs) -> Any: ...
    async def post_private_msg(self, user_id: str, text: str, **kwargs) -> Any: ...
    async def delete_msg(self, message_id: str) -> Any: ...
    async def set_group_kick(
        self, group_id: str, user_id: str, reject_add_request: bool = False
    ) -> Any: ...
    async def set_group_ban(
        self, group_id: str, user_id: str, duration: int = 30 * 60
    ) -> Any: ...
    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> Any: ...
    async def set_group_add_request(
        self, flag: str, sub_type: str, approve: bool = True, reason: str = ""
    ) -> Any: ...


class ContextMixin(BaseModel):
    """依赖注入混入类"""

    _api: Optional[IBotAPI] = PrivateAttr(default=None)

    def bind_api(self, api: IBotAPI):
        self._api = api

    @property
    def api(self) -> IBotAPI:
        if self._api is None:
            raise RuntimeError("API context not initialized.")
        return self._api
