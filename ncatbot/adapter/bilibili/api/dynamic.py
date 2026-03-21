"""动态操作 API Mixin"""

from __future__ import annotations

from typing import Optional


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
