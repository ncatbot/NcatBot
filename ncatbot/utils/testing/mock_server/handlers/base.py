"""
Mock API 处理器基础类

处理来自 MockServer 的 API 请求，返回相应的响应。
"""

from typing import Any, Callable, Dict, Optional

from ..database import MockDatabase
from .account import AccountHandlerMixin
from .group import GroupHandlerMixin
from .message import MessageHandlerMixin
from .file import FileHandlerMixin
from .upload import UploadHandlerMixin


class MockApiHandler(
    AccountHandlerMixin,
    GroupHandlerMixin,
    MessageHandlerMixin,
    FileHandlerMixin,
    UploadHandlerMixin,
):
    """
    Mock API 处理器

    根据 OneBot 协议处理 API 请求，从 MockDatabase 获取/存储数据。
    """

    def __init__(self, database: MockDatabase):
        """
        初始化 Mock API 处理器

        Args:
            database: Mock 数据库实例
        """
        self.db = database
        self._init_handlers()

    def _init_handlers(self) -> None:
        """初始化 API 处理器映射"""
        self._handlers: Dict[str, Callable[[dict], dict]] = {}

        # 注册各模块的处理器
        self._register_account_handlers()
        self._register_group_handlers()
        self._register_message_handlers()
        self._register_file_handlers()
        self._register_upload_handlers()
        self._register_other_handlers()

    def _register_other_handlers(self) -> None:
        """注册其他处理器"""
        other_handlers = {
            "set_qq_profile": self._handle_generic_success,
            "set_online_status": self._handle_generic_success,
            "set_self_longnick": self._handle_generic_success,
            "set_friend_remark": self._handle_generic_success,
            "create_collection": self._handle_generic_success,
            "set_input_status": self._handle_generic_success,
            "AskShareGroup": self._handle_generic_success,
            "fetch_custom_face": self._handle_fetch_custom_face,
            "nc_get_user_status": self._handle_nc_get_user_status,
        }
        self._handlers.update(other_handlers)

    def handle_request(self, action: str, params: Optional[dict] = None) -> dict:
        """
        处理 API 请求

        Args:
            action: API 动作名
            params: 请求参数

        Returns:
            API 响应字典
        """
        action = action.lstrip("/")
        params = params or {}

        handler = self._handlers.get(action)
        if handler:
            try:
                return handler(params)
            except Exception as e:
                return self._error_response(f"处理请求时出错: {e}")

        # 未知 API，返回通用成功响应
        return self._success_response({})

    def register_handler(
        self,
        action: str,
        handler: Callable[[dict], dict],
    ) -> None:
        """
        注册自定义 API 处理器

        Args:
            action: API 动作名
            handler: 处理函数
        """
        self._handlers[action.lstrip("/")] = handler

    # =========================================================================
    # 响应构建
    # =========================================================================

    @staticmethod
    def _success_response(data: Any) -> dict:
        """构建成功响应"""
        return {
            "status": "ok",
            "retcode": 0,
            "data": data,
            "message": "",
            "wording": "",
        }

    @staticmethod
    def _error_response(message: str, retcode: int = -1) -> dict:
        """构建错误响应"""
        return {
            "status": "failed",
            "retcode": retcode,
            "data": None,
            "message": message,
            "wording": message,
        }

    # =========================================================================
    # 其他处理器
    # =========================================================================

    def _handle_generic_success(self, params: dict) -> dict:
        return self._success_response({})

    def _handle_fetch_custom_face(self, params: dict) -> dict:
        return self._success_response([])

    def _handle_nc_get_user_status(self, params: dict) -> dict:
        return self._success_response({"status": 10, "ext_status": 0})
