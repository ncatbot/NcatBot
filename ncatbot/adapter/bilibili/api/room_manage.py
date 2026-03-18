"""直播间管理 API Mixin"""

from __future__ import annotations

from typing import Any


class RoomManageAPIMixin:
    async def ban_user(self, room_id: int, user_id: int, hour: int = 1) -> Any:
        room = self._get_room(room_id)
        return await room.ban_user(uid=user_id, hour=hour)

    async def unban_user(self, room_id: int, user_id: int) -> Any:
        room = self._get_room(room_id)
        return await room.unban_user(uid=user_id)

    async def set_room_silent(self, room_id: int, enable: bool, **kwargs: Any) -> Any:
        room = self._get_room(room_id)
        if enable:
            return await room.set_room_silent(
                silent_type=kwargs.get("silent_type", "member"),
                minute=kwargs.get("minute", 0),
            )
        return await room.del_room_silent()

    async def get_room_info(self, room_id: int) -> dict:
        room = self._get_room(room_id)
        return await room.get_room_info()
