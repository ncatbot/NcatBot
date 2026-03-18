"""数据源管理 API Mixin"""

from __future__ import annotations

from typing import Any, Dict, List


class SourceManageAPIMixin:
    async def add_live_room(self, room_id: int) -> None:
        await self._source_manager.add_live_room(room_id, self._credential)

    async def remove_live_room(self, room_id: int) -> None:
        await self._source_manager.remove_live_room(room_id)

    async def add_comment_watch(
        self, resource_id: str, resource_type: str = "video"
    ) -> None:
        await self._source_manager.add_comment_watch(
            resource_id, resource_type, self._credential
        )

    async def remove_comment_watch(self, resource_id: str) -> None:
        await self._source_manager.remove_comment_watch(resource_id)

    async def list_sources(self) -> List[Dict[str, Any]]:
        return self._source_manager.list_sources()
