"""
账号相关 API

提供账号管理、好友管理、消息状态等功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING, Union

from .utils import (
    APIComponent,
    APIReturnStatus,
    generate_sync_methods,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# 数据模型
# =============================================================================


@dataclass
class LoginInfo:
    """登录信息"""

    nickname: str
    user_id: str

    def __repr__(self) -> str:
        return f"LoginInfo(nickname={self.nickname!r}, user_id={self.user_id})"


class CustomFaceList:
    """自定义表情列表"""

    urls: List[str]

    def __init__(self, data: List[dict]):
        self.urls = [item["url"] for item in data]

    def __len__(self) -> int:
        return len(self.urls)

    def __iter__(self):
        return iter(self.urls)

    def __repr__(self) -> str:
        return f"CustomFaceList(count={len(self.urls)})"


# =============================================================================
# AccountAPI 实现
# =============================================================================


@generate_sync_methods
class AccountAPI(APIComponent):
    """
    账号相关 API

    提供账号管理、好友管理、消息状态等功能的接口。

    使用依赖注入模式，通过构造函数接收 IAPIClient 实例。
    """

    # -------------------------------------------------------------------------
    # region 账号相关
    # -------------------------------------------------------------------------

    async def set_qq_profile(
        self,
        nickname: str,
        personal_note: str,
        sex: Literal["未知", "男", "女"],
    ) -> None:
        """
        设置 QQ 资料

        Args:
            nickname: 昵称
            personal_note: 个性签名
            sex: 性别 ("未知", "男", "女")
        """
        sex_mapping = {"未知": 0, "男": 1, "女": 2}
        sex_id = str(sex_mapping[sex])

        result = await self._request_raw(
            "/set_qq_profile",
            {"nickname": nickname, "personal_note": personal_note, "sex": sex_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_online_status(
        self,
        status: int,
        ext_status: int,
        battery_status: int,
    ) -> None:
        """
        设置在线状态

        Args:
            status: 在线状态码
            ext_status: 扩展状态码
            battery_status: 电池状态
        """
        result = await self._request_raw(
            "/set_online_status",
            {
                "status": status,
                "ext_status": ext_status,
                "battery_status": battery_status,
            },
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_qq_avatar(self, file: str) -> None:
        """
        设置 QQ 头像

        Args:
            file: 图片文件路径或 URL
        """
        pass

    async def set_self_longnick(self, long_nick: str) -> None:
        """
        设置个人长昵称

        Args:
            long_nick: 长昵称内容
        """
        result = await self._request_raw(
            "/set_self_longnick",
            {"longNick": long_nick},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_login_info(self) -> LoginInfo:
        """
        获取当前登录账号信息

        Returns:
            LoginInfo: 包含昵称和用户ID的登录信息
        """
        result = await self._request_raw("/get_login_info")
        status = APIReturnStatus(result)
        return LoginInfo(**status.data)

    async def get_status(self) -> dict:
        """
        获取当前状态

        Returns:
            dict: 状态信息字典
        """
        result = await self._request_raw("/get_status")
        status = APIReturnStatus(result)
        return status.data

    # -------------------------------------------------------------------------
    # region 好友相关
    # -------------------------------------------------------------------------

    async def get_friends_with_cat(self) -> List[dict]:
        """
        获取好友列表（带分类）

        Returns:
            List[dict]: 好友列表
        """
        result = await self._request_raw("/get_friends_with_category")
        status = APIReturnStatus(result)
        return status.data

    async def send_like(
        self,
        user_id: Union[str, int],
        times: int = 1,
    ) -> Dict[str, Any]:
        """
        给好友点赞

        Args:
            user_id: 目标用户 QQ 号
            times: 点赞次数，默认 1

        Returns:
            dict: 响应结果
        """
        result = await self._request_raw(
            "/send_like",
            {"user_id": user_id, "times": times},
        )
        try:
            APIReturnStatus.raise_if_failed(result)
        except Exception:
            pass
        return result

    async def set_friend_add_request(
        self,
        flag: str,
        approve: bool,
        remark: Optional[str] = None,
    ) -> None:
        """
        处理好友添加请求

        Args:
            flag: 请求标识
            approve: 是否同意
            remark: 通过后的好友备注
        """
        result = await self._request_raw(
            "/set_friend_add_request",
            {"flag": flag, "approve": approve, "remark": remark},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_friend_list(self) -> List[dict]:
        """
        获取好友列表

        Returns:
            List[dict]: 好友信息列表
        """
        result = await self._request_raw("/get_friend_list")
        status = APIReturnStatus(result)
        return status.data

    async def delete_friend(
        self,
        user_id: Union[str, int],
        block: bool = True,
        both: bool = True,
    ) -> None:
        """
        删除好友

        Args:
            user_id: 目标用户 QQ 号
            block: 是否拉黑，默认 True
            both: 是否双向删除，默认 True
        """
        result = await self._request_raw(
            "/delete_friend",
            {"user_id": user_id, "block": block, "both": both},
        )
        APIReturnStatus.raise_if_failed(result)

    async def set_friend_remark(
        self,
        user_id: Union[str, int],
        remark: str,
    ) -> None:
        """
        设置好友备注

        Args:
            user_id: 目标用户 QQ 号
            remark: 备注内容
        """
        result = await self._request_raw(
            "/set_friend_remark",
            {"user_id": user_id, "remark": remark},
        )
        APIReturnStatus.raise_if_failed(result)

    # -------------------------------------------------------------------------
    # region 消息状态
    # -------------------------------------------------------------------------

    async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None:
        """
        将群消息标记为已读

        Args:
            group_id: 群号
        """
        result = await self._request_raw(
            "/mark_group_msg_as_read",
            {"group_id": group_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None:
        """
        将私聊消息标记为已读

        Args:
            user_id: 用户 QQ 号
        """
        result = await self._request_raw(
            "/mark_private_msg_as_read",
            {"user_id": user_id},
        )
        APIReturnStatus.raise_if_failed(result)

    async def create_collection(self, raw_data: str, brief: str) -> None:
        """
        创建收藏

        Args:
            raw_data: 原始数据
            brief: 简介
        """
        result = await self._request_raw(
            "/create_collection",
            {"rawData": raw_data, "brief": brief},
        )
        APIReturnStatus.raise_if_failed(result)

    async def get_recent_contact(self) -> List[dict]:
        """
        获取最近联系人

        Returns:
            List[dict]: 最近联系人列表
        """
        result = await self._request_raw("/get_recent_contact")
        status = APIReturnStatus(result)
        return status.data

    async def _mark_all_as_read(self) -> None:
        """将所有消息标记为已读（内部方法）"""
        result = await self._request_raw("/_mark_all_as_read")
        APIReturnStatus.raise_if_failed(result)

    # -------------------------------------------------------------------------
    # region 群相关
    # -------------------------------------------------------------------------

    async def ask_share_group(self, group_id: Union[str, int]) -> None:
        """
        请求分享群

        Args:
            group_id: 群号
        """
        result = await self._request_raw(
            "/AskShareGroup",
            {"group_id": group_id},
        )
        APIReturnStatus.raise_if_failed(result)

    # 向后兼容别名
    async def AskShareGroup(self, group_id: Union[str, int]) -> None:
        """向后兼容：请使用 ask_share_group"""
        return await self.ask_share_group(group_id)

    # -------------------------------------------------------------------------
    # region 其它
    # -------------------------------------------------------------------------

    async def get_stranger_info(self, user_id: Union[str, int]) -> dict:
        """
        获取陌生人信息

        Args:
            user_id: 用户 QQ 号

        Returns:
            dict: 用户信息字典

        Note:
            接口暂不完善，有需求请提 PR
            解析参考: https://napcat.apifox.cn/226656970e0
        """
        result = await self._request_raw(
            "/get_stranger_info",
            {"user_id": user_id},
        )
        status = APIReturnStatus(result)
        return status.data

    async def fetch_custom_face(self, count: int = 48) -> CustomFaceList:
        """
        获取自定义表情

        Args:
            count: 获取数量，默认 48

        Returns:
            CustomFaceList: 自定义表情列表
        """
        result = await self._request_raw(
            "/fetch_custom_face",
            {"count": count},
        )
        status = APIReturnStatus(result)
        return CustomFaceList(status.data)

    async def nc_get_user_status(self, user_id: Union[str, int]) -> dict:
        """
        获取用户状态（NapCat 扩展）

        Args:
            user_id: 用户 QQ 号

        Returns:
            dict: 用户状态信息
        """
        result = await self._request_raw(
            "/nc_get_user_status",
            {"user_id": user_id},
        )
        status = APIReturnStatus(result)
        return status.data
