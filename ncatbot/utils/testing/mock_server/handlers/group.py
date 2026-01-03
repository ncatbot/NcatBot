"""
群组相关 API 处理器
"""
# pyright: reportAttributeAccessIssue=false

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database import MockDatabase


class GroupHandlerMixin:
    """群组相关处理器"""

    # 以下属性/方法由 MockApiHandler 提供
    db: "MockDatabase"
    _handlers: dict

    def _register_group_handlers(self) -> None:
        """注册群组相关处理器"""
        handlers = {
            "get_group_list": self._handle_get_group_list,
            "get_group_info": self._handle_get_group_info,
            "get_group_info_ex": self._handle_get_group_info_ex,
            "get_group_member_list": self._handle_get_group_member_list,
            "get_group_member_info": self._handle_get_group_member_info,
            "get_group_shut_list": self._handle_get_group_shut_list,
            "get_group_honor_info": self._handle_get_group_honor_info,
            "set_group_kick": self._handle_set_group_kick,
            "set_group_ban": self._handle_set_group_ban,
            "set_group_whole_ban": self._handle_set_group_whole_ban,
            "set_group_admin": self._handle_set_group_admin,
            "set_group_special_title": self._handle_set_group_special_title,
            "set_group_card": self._handle_set_group_card,
            "set_group_add_request": self._handle_set_group_add_request,
            "group_poke": self._handle_poke,
            # 精华消息
            "set_essence_msg": self._handle_set_essence_msg,
            "delete_essence_msg": self._handle_delete_essence_msg,
            "get_essence_msg_list": self._handle_get_essence_msg_list,
        }
        self._handlers.update(handlers)

    # =========================================================================
    # 群组相关处理器
    # =========================================================================

    def _handle_get_group_list(self, params: dict) -> dict:
        return self._success_response(self.db.get_group_list())

    def _handle_get_group_info(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        info = self.db.get_group_info(group_id)
        if info:
            return self._success_response(info)
        return self._error_response("群不存在")

    def _handle_get_group_info_ex(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        info = self.db.get_group_info(group_id)
        if info:
            return self._success_response(info)
        return self._error_response("群不存在")

    def _handle_get_group_member_list(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        members = self.db.get_group_member_list(group_id)
        return self._success_response(members)

    def _handle_get_group_member_info(self, params: dict) -> dict:
        group_id = str(params.get("group_id", ""))
        user_id = str(params.get("user_id", ""))
        info = self.db.get_group_member_info(group_id, user_id)
        if info:
            return self._success_response(info)
        return self._error_response("成员不存在")

    def _handle_get_group_shut_list(self, params: dict) -> dict:
        return self._success_response([])

    def _handle_get_group_honor_info(self, params: dict) -> dict:
        return self._success_response(
            {
                "group_id": params.get("group_id"),
                "current_talkative": None,
                "talkative_list": [],
                "performer_list": [],
                "legend_list": [],
                "emotion_list": [],
            }
        )

    def _handle_set_group_kick(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_ban(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_whole_ban(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_admin(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_special_title(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_card(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_set_group_add_request(self, params: dict) -> dict:
        return self._success_response({})

    # =========================================================================
    # 精华消息处理器
    # =========================================================================

    def _handle_set_essence_msg(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_delete_essence_msg(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_get_essence_msg_list(self, params: dict) -> dict:
        return self._success_response([])
