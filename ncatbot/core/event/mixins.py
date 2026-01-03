from typing import Any, Optional
from .context import ContextMixin


class MessageActionMixin(ContextMixin):
    message_type: Any
    group_id: Optional[str] = None  # 私聊消息无 group_id
    user_id: Any
    message_id: Any

    async def reply(self, text: str, **kwargs):
        if getattr(self, "message_type", "") == "group" and hasattr(self, "group_id"):
            return await self.api.post_group_msg(
                group_id=self.group_id, text=text, **kwargs
            )
        elif getattr(self, "message_type", "") == "private" and hasattr(
            self, "user_id"
        ):
            return await self.api.post_private_msg(
                user_id=self.user_id, text=text, **kwargs
            )
        raise ValueError("Cannot reply to this event type")

    async def delete(self):
        if hasattr(self, "message_id"):
            return await self.api.delete_msg(message_id=self.message_id)


class GroupAdminMixin(ContextMixin):
    group_id: Any
    user_id: Any

    async def kick(self, reject_add_request: bool = False):
        if hasattr(self, "group_id") and hasattr(self, "user_id"):
            return await self.api.set_group_kick(
                self.group_id, self.user_id, reject_add_request
            )

    async def ban(self, duration: int = 30 * 60):
        if hasattr(self, "group_id") and hasattr(self, "user_id"):
            return await self.api.set_group_ban(self.group_id, self.user_id, duration)


class RequestActionMixin(ContextMixin):
    request_type: Any
    flag: Any
    sub_type: Optional[Any] = None  # FriendRequest 无 sub_type

    async def approve(self, remark: str = "", reason: str = ""):
        """统一处理请求同意"""
        request_type = getattr(self, "request_type", "")
        flag = getattr(self, "flag", "")

        if request_type == "friend":
            return await self.api.set_friend_add_request(
                flag=flag, approve=True, remark=remark
            )
        elif request_type == "group":
            sub_type = getattr(self, "sub_type", "")
            return await self.api.set_group_add_request(
                flag=flag, sub_type=sub_type, approve=True, reason=""
            )

    async def reject(self, reason: str = ""):
        """统一处理请求拒绝"""
        request_type = getattr(self, "request_type", "")
        flag = getattr(self, "flag", "")

        if request_type == "friend":
            return await self.api.set_friend_add_request(flag=flag, approve=False)
        elif request_type == "group":
            sub_type = getattr(self, "sub_type", "")
            return await self.api.set_group_add_request(
                flag=flag, sub_type=sub_type, approve=False, reason=reason
            )
