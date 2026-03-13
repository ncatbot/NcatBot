"""
IBotAPI 抽象接口

定义与协议无关的 Bot 操作接口，由 Adapter 提供具体实现。
位于 Layer 2（Abstract API），Core 层和 Plugin 层通过此接口调用 API。
"""

from abc import ABC, abstractmethod
from typing import List, Union


class IBotAPI(ABC):
    """与协议无关的 Bot API 接口

    此接口定义框架期望的所有 Bot 操作。
    各 Adapter 提供具体实现。

    方法分类：
    1. 消息操作：发送、撤回、转发
    2. 群管理：踢人、禁言、设置管理员
    3. 账号操作：设置资料、好友管理
    4. 信息查询：获取群/好友/消息信息
    5. 文件操作：群文件管理
    6. 辅助功能：戳一戳、点赞等
    """

    # ==================================================================
    # 消息操作
    # ==================================================================

    @abstractmethod
    async def send_private_msg(
        self, user_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        """发送私聊消息"""

    @abstractmethod
    async def send_group_msg(
        self, group_id: Union[str, int], message: list, **kwargs
    ) -> dict:
        """发送群聊消息"""

    @abstractmethod
    async def delete_msg(self, message_id: Union[str, int]) -> None:
        """撤回消息"""

    @abstractmethod
    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs,
    ) -> dict:
        """发送合并转发消息"""

    # ==================================================================
    # 群管理
    # ==================================================================

    @abstractmethod
    async def set_group_kick(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        reject_add_request: bool = False,
    ) -> None:
        """踢出群成员"""

    @abstractmethod
    async def set_group_ban(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        duration: int = 30 * 60,
    ) -> None:
        """禁言群成员"""

    @abstractmethod
    async def set_group_whole_ban(
        self, group_id: Union[str, int], enable: bool = True
    ) -> None:
        """全群禁言"""

    @abstractmethod
    async def set_group_admin(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        enable: bool = True,
    ) -> None:
        """设置群管理员"""

    @abstractmethod
    async def set_group_card(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        card: str = "",
    ) -> None:
        """设置群名片"""

    @abstractmethod
    async def set_group_name(self, group_id: Union[str, int], name: str) -> None:
        """设置群名称"""

    @abstractmethod
    async def set_group_leave(
        self, group_id: Union[str, int], is_dismiss: bool = False
    ) -> None:
        """退出群组"""

    @abstractmethod
    async def set_group_special_title(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
        special_title: str = "",
    ) -> None:
        """设置群成员专属头衔"""

    # ==================================================================
    # 账号操作
    # ==================================================================

    @abstractmethod
    async def set_friend_add_request(
        self, flag: str, approve: bool = True, remark: str = ""
    ) -> None:
        """处理好友请求"""

    @abstractmethod
    async def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool = True,
        reason: str = "",
    ) -> None:
        """处理群请求/邀请"""

    # ==================================================================
    # 信息查询
    # ==================================================================

    @abstractmethod
    async def get_login_info(self) -> dict:
        """获取登录号信息"""

    @abstractmethod
    async def get_stranger_info(self, user_id: Union[str, int]) -> dict:
        """获取陌生人信息"""

    @abstractmethod
    async def get_friend_list(self) -> List[dict]:
        """获取好友列表"""

    @abstractmethod
    async def get_group_info(self, group_id: Union[str, int]) -> dict:
        """获取群信息"""

    @abstractmethod
    async def get_group_list(self) -> list:
        """获取群列表"""

    @abstractmethod
    async def get_group_member_info(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> dict:
        """获取群成员信息"""

    @abstractmethod
    async def get_group_member_list(self, group_id: Union[str, int]) -> list:
        """获取群成员列表"""

    @abstractmethod
    async def get_msg(self, message_id: Union[str, int]) -> dict:
        """获取消息"""

    @abstractmethod
    async def get_forward_msg(self, message_id: Union[str, int]) -> dict:
        """获取合并转发消息"""

    # ==================================================================
    # 文件操作
    # ==================================================================

    @abstractmethod
    async def upload_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: str,
        folder_id: str = "",
    ) -> None:
        """上传群文件"""

    @abstractmethod
    async def get_group_root_files(self, group_id: Union[str, int]) -> dict:
        """获取群根目录文件列表"""

    @abstractmethod
    async def get_group_file_url(self, group_id: Union[str, int], file_id: str) -> str:
        """获取群文件 URL"""

    @abstractmethod
    async def delete_group_file(self, group_id: Union[str, int], file_id: str) -> None:
        """删除群文件"""

    # ==================================================================
    # 辅助功能
    # ==================================================================

    @abstractmethod
    async def send_like(self, user_id: Union[str, int], times: int = 1) -> None:
        """发送好友赞"""

    @abstractmethod
    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        """发送戳一戳"""
