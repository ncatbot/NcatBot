"""动态操作 API Mixin"""

from __future__ import annotations

from typing import Any, Optional


class DynamicAPIMixin:
    async def get_user_dynamics(self, uid: int, offset: str = "") -> dict:
        """获取用户动态列表（新版接口）"""
        from bilibili_api.user import User

        user = User(uid=uid, credential=self._credential)
        return await user.get_dynamics_new(offset=offset)

    async def get_user_latest_dynamic(self, uid: int) -> Optional[dict]:
        """获取用户最新一条动态"""
        resp = await self.get_user_dynamics(uid)
        items = resp.get("items") or []
        if not items:
            return None
        return max(
            items,
            key=lambda it: int(
                ((it.get("modules") or {}).get("module_author") or {}).get("pub_ts", 0)
            ),
        )

    async def add_dynamic_watch(self, uid: int) -> None:
        """添加动态监听"""
        await self._source_manager.add_dynamic_watch(uid, self._credential)

    async def remove_dynamic_watch(self, uid: int) -> None:
        """移除动态监听"""
        await self._source_manager.remove_dynamic_watch(uid)

    async def add_dynamic_page_watch(self, uid: int) -> None:
        """添加动态页监听（先关注再加入轮询）"""
        await self.follow_user(uid)
        await self._source_manager.add_dynamic_page_watch(uid, self._credential)

    async def remove_dynamic_page_watch(self, uid: int) -> None:
        """移除动态页监听"""
        await self._source_manager.remove_dynamic_page_watch(uid)

    async def follow_user(self, uid: int) -> Any:
        """关注用户（已关注或关注自己时静默跳过）"""
        from bilibili_api.user import User, RelationType
        from bilibili_api.exceptions import ResponseCodeException

        user = User(uid=uid, credential=self._credential)
        try:
            return await user.modify_relation(RelationType.SUBSCRIBE)
        except ResponseCodeException as e:
            # 22001: 不能关注自己  22014: 已经关注
            if e.code in (22001, 22014):
                return None
            raise
