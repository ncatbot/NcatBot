"""私信操作 API Mixin"""

from __future__ import annotations

from typing import Any


class SessionAPIMixin:
    async def send_private_msg(self, user_id: int, content: str) -> Any:
        from bilibili_api import session as bili_session

        return await bili_session.send_msg(
            self._credential,
            receiver_id=user_id,
            msg_type=bili_session.EventType.TEXT,
            content=content,
        )

    async def send_private_image(self, user_id: int, image_url: str) -> Any:
        from bilibili_api import session as bili_session

        return await bili_session.send_msg(
            self._credential,
            receiver_id=user_id,
            msg_type=bili_session.EventType.PICTURE,
            content=image_url,
        )

    async def get_session_history(self, user_id: int, count: int = 20) -> list:
        from bilibili_api import session as bili_session

        resp = await bili_session.fetch_session_msgs(
            self._credential,
            talker_id=user_id,
            session_type=1,
            begin_seqno=0,
        )
        messages = resp.get("messages", [])
        return messages[:count]
