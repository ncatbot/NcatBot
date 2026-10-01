"""账号操作 API Mixin"""

from typing import Union

from ncatbot.types.napcat import OcrResult


class AccountAPIMixin:
    async def set_friend_add_request(
        self,
        flag: str,
        approve: bool = True,
        remark: str = "",
    ) -> None:
        await self._call(
            "set_friend_add_request",
            {
                "flag": flag,
                "approve": approve,
                "remark": remark,
            },
        )

    async def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool = True,
        reason: str = "",
    ) -> None:
        await self._call(
            "set_group_add_request",
            {
                "flag": flag,
                "sub_type": sub_type,
                "approve": approve,
                "reason": reason,
            },
        )

    # ---- 好友管理 ----

    async def set_friend_remark(self, user_id: Union[str, int], remark: str) -> None:
        await self._call(
            "set_friend_remark",
            {"user_id": int(user_id), "remark": remark},
        )

    async def delete_friend(self, user_id: Union[str, int]) -> None:
        await self._call("delete_friend", {"user_id": int(user_id)})

    async def friend_poke(self, user_id: Union[str, int]) -> None:
        await self._call("friend_poke", {"user_id": int(user_id)})

    # ---- 个人资料 ----

    async def set_self_longnick(self, long_nick: str) -> None:
        await self._call("set_self_longnick", {"longNick": long_nick})

    async def set_qq_avatar(self, file: str) -> None:
        await self._call("set_qq_avatar", {"file": file})

    async def set_qq_profile(
        self,
        nickname: str = "",
        company: str = "",
        email: str = "",
        college: str = "",
        personal_note: str = "",
    ) -> None:
        params: dict = {}
        if nickname:
            params["nickname"] = nickname
        if company:
            params["company"] = company
        if email:
            params["email"] = email
        if college:
            params["college"] = college
        if personal_note:
            params["personal_note"] = personal_note
        await self._call("set_qq_profile", params)

    async def set_online_status(
        self,
        status: int,
        ext_status: int = 0,
        custom_status: str = "",
        *,
        battery_status: int = 0,
    ) -> None:
        params: dict = {
            "status": status,
            "ext_status": ext_status,
            "battery_status": battery_status,
        }
        if custom_status:
            params["custom_status"] = custom_status
        await self._call("set_online_status", params)

    async def ocr_image(self, image: str) -> OcrResult:
        data = await self._call_data("ocr_image", {"image": image}) or {}
        return OcrResult(**data)
