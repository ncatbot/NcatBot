"""
账号和好友相关 API 处理器
"""
# pyright: reportAttributeAccessIssue=false

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database import MockDatabase


class AccountHandlerMixin:
    """账号和好友相关处理器"""

    # 以下属性/方法由 MockApiHandler 提供
    db: "MockDatabase"
    _handlers: dict

    def _register_account_handlers(self) -> None:
        """注册账号和好友相关处理器"""
        handlers = {
            # 账号相关
            "get_login_info": self._handle_get_login_info,
            "get_status": self._handle_get_status,
            "get_version_info": self._handle_get_version_info,
            # 好友相关
            "get_friend_list": self._handle_get_friend_list,
            "get_friends_with_category": self._handle_get_friends_with_category,
            "get_stranger_info": self._handle_get_stranger_info,
            "get_recent_contact": self._handle_get_recent_contact,
            "send_like": self._handle_send_like,
            "friend_poke": self._handle_poke,
            "set_friend_add_request": self._handle_set_friend_add_request,
            "delete_friend": self._handle_delete_friend,
        }
        self._handlers.update(handlers)

    # =========================================================================
    # 账号相关处理器
    # =========================================================================

    def _handle_get_login_info(self, params: dict) -> dict:
        return self._success_response(self.db.get_login_info())

    def _handle_get_status(self, params: dict) -> dict:
        return self._success_response(self.db.get_status())

    def _handle_get_version_info(self, params: dict) -> dict:
        return self._success_response(
            {
                "app_name": "NapCat.Mock",
                "protocol_version": "v11",
                "app_version": "1.0.0",
            }
        )

    # =========================================================================
    # 好友相关处理器
    # =========================================================================

    def _handle_get_friend_list(self, params: dict) -> dict:
        return self._success_response(self.db.get_friend_list())

    def _handle_get_friends_with_category(self, params: dict) -> dict:
        return self._success_response(self.db.get_friend_list())

    def _handle_get_stranger_info(self, params: dict) -> dict:
        user_id = str(params.get("user_id", ""))
        info = self.db.get_stranger_info(user_id)
        if info:
            return self._success_response(info)
        return self._error_response("用户不存在")

    def _handle_get_recent_contact(self, params: dict) -> dict:
        return self._success_response(self.db.get_friend_list()[:10])

    def _handle_send_like(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_poke(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_friend_add_request(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_delete_friend(self, params: dict) -> dict:
        return self._success_response({})
