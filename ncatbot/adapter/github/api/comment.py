"""Comment API Mixin"""

from __future__ import annotations

from typing import Any


class CommentAPIMixin:
    """评论操作"""

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any: ...

    async def create_issue_comment(
        self, repo: str, issue_number: int, body: str
    ) -> dict:
        return await self._request(
            "POST",
            f"/repos/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )

    async def update_comment(self, repo: str, comment_id: int, body: str) -> dict:
        return await self._request(
            "PATCH",
            f"/repos/{repo}/issues/comments/{comment_id}",
            json={"body": body},
        )

    async def delete_comment(self, repo: str, comment_id: int) -> None:
        await self._request("DELETE", f"/repos/{repo}/issues/comments/{comment_id}")

    async def list_issue_comments(
        self, repo: str, issue_number: int, page: int = 1, per_page: int = 30
    ) -> list:
        return await self._request(
            "GET",
            f"/repos/{repo}/issues/{issue_number}/comments",
            params={"page": page, "per_page": per_page},
        )
