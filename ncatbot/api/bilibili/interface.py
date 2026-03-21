"""IBiliAPIClient — Bilibili 平台 API 接口

定义 B 站适配器所有可用 API 方法。
由 BiliBotAPI 实现。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ncatbot.api.base import IAPIClient
from ncatbot.types.bilibili.models import LiveRoomInfo


class IBiliAPIClient(IAPIClient):
    """Bilibili 平台 Bot API 接口"""

    # ---- 数据源管理 ----

    @abstractmethod
    async def add_live_room(self, room_id: int) -> None:
        """添加直播间监听"""

    @abstractmethod
    async def remove_live_room(self, room_id: int) -> None:
        """移除直播间监听"""

    @abstractmethod
    async def add_comment_watch(
        self, resource_id: str, resource_type: str = "video"
    ) -> None:
        """添加评论监听"""

    @abstractmethod
    async def remove_comment_watch(self, resource_id: str) -> None:
        """移除评论监听"""

    @abstractmethod
    async def list_sources(self) -> List[Dict[str, Any]]:
        """列出所有数据源"""

    # ---- 直播间操作 ----

    @abstractmethod
    async def send_danmu(self, room_id: int, text: str) -> Any:
        """发送弹幕"""

    @abstractmethod
    async def ban_user(self, room_id: int, user_id: int, hour: int = 1) -> Any:
        """禁言用户"""

    @abstractmethod
    async def unban_user(self, room_id: int, user_id: int) -> Any:
        """解除禁言"""

    @abstractmethod
    async def set_room_silent(self, room_id: int, enable: bool, **kwargs: Any) -> Any:
        """全员禁言"""

    @abstractmethod
    async def get_room_info(self, room_id: int) -> Optional[LiveRoomInfo]:
        """获取直播间信息"""

    # ---- 私信 ----

    @abstractmethod
    async def send_private_msg(self, user_id: int, content: str) -> Any:
        """发送私信"""

    @abstractmethod
    async def send_private_image(self, user_id: int, image_url: str) -> Any:
        """发送私信图片"""

    @abstractmethod
    async def get_session_history(self, user_id: int, count: int = 20) -> list:
        """获取私信历史"""

    # ---- 评论 ----

    @abstractmethod
    async def send_comment(
        self, resource_id: str, resource_type: str, text: str
    ) -> Any:
        """发送评论"""

    @abstractmethod
    async def reply_comment(
        self,
        resource_id: str,
        resource_type: str,
        root_id: int,
        parent_id: int,
        text: str,
    ) -> Any:
        """回复评论"""

    @abstractmethod
    async def delete_comment(
        self, resource_id: str, resource_type: str, comment_id: int
    ) -> Any:
        """删除评论"""

    @abstractmethod
    async def like_comment(
        self, resource_id: str, resource_type: str, comment_id: int
    ) -> Any:
        """点赞评论"""

    @abstractmethod
    async def get_comments(
        self, resource_id: str, resource_type: str, page: int = 1
    ) -> list:
        """获取评论列表"""

    # ---- 动态 ----

    @abstractmethod
    async def get_user_dynamics(self, uid: int, offset: str = "") -> dict:
        """获取用户动态列表"""

    @abstractmethod
    async def get_user_latest_dynamic(self, uid: int) -> Optional[dict]:
        """获取用户最新一条动态"""

    @abstractmethod
    async def add_dynamic_watch(self, uid: int) -> None:
        """添加动态监听"""

    @abstractmethod
    async def remove_dynamic_watch(self, uid: int) -> None:
        """移除动态监听"""

    # ---- 用户查询 ----

    @abstractmethod
    async def get_user_info(self, user_id: int) -> dict:
        """获取用户信息"""
