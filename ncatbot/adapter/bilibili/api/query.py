"""查询操作 API Mixin"""

from __future__ import annotations


class QueryAPIMixin:
    async def get_user_info(self, user_id: int) -> dict:
        from bilibili_api import user as bili_user

        u = bili_user.User(uid=user_id, credential=self._credential)
        return await u.get_user_info()
