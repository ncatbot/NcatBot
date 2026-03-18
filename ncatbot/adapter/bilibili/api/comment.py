"""评论操作 API Mixin"""

from __future__ import annotations

from typing import Any


def _get_resource_type(resource_type: str) -> Any:
    from bilibili_api.comment import CommentResourceType

    _map = {
        "video": CommentResourceType.VIDEO,
        "dynamic": CommentResourceType.DYNAMIC,
        "article": CommentResourceType.ARTICLE,
    }
    return _map.get(resource_type, CommentResourceType.VIDEO)


def _resolve_oid(resource_id: str) -> int:
    """将 resource_id (可能是 BV 号) 转为 oid (int)"""
    try:
        return int(resource_id)
    except ValueError:
        pass
    from bilibili_api.utils.aid_bvid_transformer import bvid2aid

    return bvid2aid(resource_id)


class CommentAPIMixin:
    async def send_comment(
        self, resource_id: str, resource_type: str, text: str
    ) -> Any:
        from bilibili_api import comment as bili_comment

        oid = _resolve_oid(resource_id)
        return await bili_comment.send_comment(
            text=text,
            oid=oid,
            type_=_get_resource_type(resource_type),
            credential=self._credential,
        )

    async def reply_comment(
        self,
        resource_id: str,
        resource_type: str,
        root_id: int,
        parent_id: int,
        text: str,
    ) -> Any:
        from bilibili_api import comment as bili_comment

        oid = _resolve_oid(resource_id)
        return await bili_comment.send_comment(
            text=text,
            oid=oid,
            type_=_get_resource_type(resource_type),
            root=root_id,
            parent=parent_id,
            credential=self._credential,
        )

    async def delete_comment(
        self, resource_id: str, resource_type: str, comment_id: int
    ) -> Any:
        from bilibili_api import comment as bili_comment

        oid = _resolve_oid(resource_id)
        c = bili_comment.Comment(
            oid=oid,
            type_=_get_resource_type(resource_type),
            rpid=comment_id,
            credential=self._credential,
        )
        return await c.delete()

    async def like_comment(
        self, resource_id: str, resource_type: str, comment_id: int
    ) -> Any:
        from bilibili_api import comment as bili_comment

        oid = _resolve_oid(resource_id)
        c = bili_comment.Comment(
            oid=oid,
            type_=_get_resource_type(resource_type),
            rpid=comment_id,
            credential=self._credential,
        )
        return await c.like()

    async def get_comments(
        self, resource_id: str, resource_type: str, page: int = 1
    ) -> list:
        from bilibili_api import comment as bili_comment

        oid = _resolve_oid(resource_id)
        resp = await bili_comment.get_comments(
            oid=oid,
            type_=_get_resource_type(resource_type),
            page_index=page,
            credential=self._credential,
        )
        return resp.get("replies", [])
