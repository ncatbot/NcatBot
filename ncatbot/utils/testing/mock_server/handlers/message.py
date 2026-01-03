"""
消息相关 API 处理器
"""
# pyright: reportAttributeAccessIssue=false

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database import MockDatabase


class MessageHandlerMixin:
    """消息相关处理器"""

    # 以下属性/方法由 MockApiHandler 提供
    db: "MockDatabase"
    _handlers: dict

    def _register_message_handlers(self) -> None:
        """注册消息相关处理器"""
        handlers = {
            "send_group_msg": self._handle_send_group_msg,
            "send_private_msg": self._handle_send_private_msg,
            "send_msg": self._handle_send_msg,
            "delete_msg": self._handle_delete_msg,
            "get_msg": self._handle_get_msg,
            "get_group_msg_history": self._handle_get_group_msg_history,
            "get_friend_msg_history": self._handle_get_friend_msg_history,
            "get_forward_msg": self._handle_get_forward_msg,
            "send_forward_msg": self._handle_send_forward_msg,
            "set_msg_emoji_like": self._handle_set_msg_emoji_like,
            "fetch_emoji_like": self._handle_fetch_emoji_like,
            "mark_group_msg_as_read": self._handle_mark_msg_as_read,
            "mark_private_msg_as_read": self._handle_mark_msg_as_read,
            "_mark_all_as_read": self._handle_mark_msg_as_read,
            # 媒体相关
            "get_image": self._handle_get_image,
            "get_record": self._handle_get_record,
        }
        self._handlers.update(handlers)

    # =========================================================================
    # 消息相关处理器
    # =========================================================================

    def _handle_send_group_msg(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        message = params.get("message", [])

        if isinstance(message, str):
            message = [{"type": "text", "data": {"text": message}}]

        msg_id = self.db.send_group_message(group_id, message)
        return self._success_response({"message_id": msg_id})

    def _handle_send_private_msg(self, params: dict) -> dict:
        user_id = str(params.get("user_id", ""))
        message = params.get("message", [])

        if isinstance(message, str):
            message = [{"type": "text", "data": {"text": message}}]

        msg_id = self.db.send_private_message(user_id, message)
        return self._success_response({"message_id": msg_id})

    def _handle_send_msg(self, params: dict) -> dict:
        message_type = params.get("message_type", "")
        if message_type == "group":
            return self._handle_send_group_msg(params)
        elif message_type == "private":
            return self._handle_send_private_msg(params)
        return self._error_response("未知消息类型")

    def _handle_delete_msg(self, params: dict) -> dict:
        message_id = str(params.get("message_id", ""))
        if self.db.delete_message(message_id):
            return self._success_response({})
        return self._error_response("消息不存在")

    def _handle_get_msg(self, params: dict) -> dict:
        message_id = str(params.get("message_id", ""))
        msg = self.db.get_message(message_id)
        if msg:
            return self._success_response(msg)
        return self._error_response("消息不存在")

    def _handle_get_group_msg_history(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        count = int(params.get("count", 20))
        message_seq = params.get("message_seq")
        reverse_order = params.get("reverseOrder", False)

        messages = self.db.get_group_msg_history(
            group_id, count, message_seq, reverse_order
        )
        return self._success_response({"messages": messages})

    def _handle_get_friend_msg_history(self, params: dict) -> dict:
        user_id = str(params.get("user_id", ""))
        count = int(params.get("count", 20))
        message_seq = params.get("message_seq")
        reverse_order = params.get("reverseOrder", False)

        messages = self.db.get_friend_msg_history(
            user_id, count, message_seq, reverse_order
        )
        return self._success_response({"messages": messages})

    def _handle_get_forward_msg(self, params: dict) -> dict:
        return self._success_response({"messages": []})

    def _handle_send_forward_msg(self, params: dict) -> dict:
        return self._success_response({"message_id": "forward_" + str(time.time())})

    def _handle_set_msg_emoji_like(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_fetch_emoji_like(self, params: dict) -> dict:
        return self._success_response({"emojiLikesList": []})

    def _handle_mark_msg_as_read(self, params: dict) -> dict:
        return self._success_response({})

    # =========================================================================
    # 媒体相关处理器
    # =========================================================================

    def _handle_get_image(self, params: dict) -> dict:
        file_id = params.get("file_id") or params.get("file", "")
        return self._success_response(
            {
                "file": f"mock_image_{file_id}.jpg",
                "url": f"https://mock.image.url/{file_id}.jpg",
                "file_size": 1024,
            }
        )

    def _handle_get_record(self, params: dict) -> dict:
        file_id = params.get("file_id") or params.get("file", "")
        return self._success_response(
            {
                "file": f"mock_record_{file_id}.mp3",
                "url": f"https://mock.record.url/{file_id}.mp3",
                "file_size": 1024,
            }
        )
