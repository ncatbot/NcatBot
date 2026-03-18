"""Pull Request API Mixin"""

from __future__ import annotations

from typing import Any, List, Optional, Union

from ncatbot.types.github.enums import GitHubMergeMethod


class PRAPIMixin:
    """PR 操作"""

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any: ...

    async def create_pr_comment(self, repo: str, pr_number: int, body: str) -> dict:
        # GitHub API 中 PR 评论与 Issue 评论共用同一端点
        return await self._request(
            "POST",
            f"/repos/{repo}/issues/{pr_number}/comments",
            json={"body": body},
        )

    async def merge_pr(
        self,
        repo: str,
        pr_number: int,
        *,
        merge_method: Union[GitHubMergeMethod, str] = GitHubMergeMethod.MERGE,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> dict:
        data: dict = {"merge_method": str(merge_method)}
        if commit_title is not None:
            data["commit_title"] = commit_title
        if commit_message is not None:
            data["commit_message"] = commit_message
        return await self._request(
            "PUT", f"/repos/{repo}/pulls/{pr_number}/merge", json=data
        )

    async def close_pr(self, repo: str, pr_number: int) -> dict:
        return await self._request(
            "PATCH",
            f"/repos/{repo}/pulls/{pr_number}",
            json={"state": "closed"},
        )

    async def request_review(
        self, repo: str, pr_number: int, reviewers: List[str]
    ) -> dict:
        return await self._request(
            "POST",
            f"/repos/{repo}/pulls/{pr_number}/requested_reviewers",
            json={"reviewers": reviewers},
        )

    async def get_pr(self, repo: str, pr_number: int) -> dict:
        return await self._request("GET", f"/repos/{repo}/pulls/{pr_number}")
