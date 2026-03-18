"""弹幕操作 API Mixin"""

from __future__ import annotations

from typing import Any


class DanmuAPIMixin:
    async def send_danmu(self, room_id: int, text: str) -> Any:
        room = self._get_room(room_id)
        return await room.send_danmaku(text)

    def _get_room(self, room_id: int) -> Any:
        """获取或创建 LiveRoom 实例（带缓存）"""
        if room_id not in self._rooms:
            from bilibili_api.live import LiveRoom

            self._rooms[room_id] = LiveRoom(
                room_display_id=room_id, credential=self._credential
            )
        return self._rooms[room_id]
