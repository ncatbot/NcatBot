"""Issue API Mixin"""

from __future__ import annotations

from typing import Any, List, Optional


class IssueAPIMixin:
    """Issue 操作"""

    _session: Any
    _base_url: str

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any: ...

    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        data: dict = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        return await self._request("POST", f"/repos/{repo}/issues", json=data)

    async def update_issue(
        self,
        repo: str,
        issue_number: int,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        data: dict = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        if assignees is not None:
            data["assignees"] = assignees
        return await self._request(
            "PATCH", f"/repos/{repo}/issues/{issue_number}", json=data
        )

    async def close_issue(self, repo: str, issue_number: int) -> dict:
        return await self.update_issue(repo, issue_number, state="closed")

    async def reopen_issue(self, repo: str, issue_number: int) -> dict:
        return await self.update_issue(repo, issue_number, state="open")

    async def get_issue(self, repo: str, issue_number: int) -> dict:
        return await self._request("GET", f"/repos/{repo}/issues/{issue_number}")

    async def add_labels(self, repo: str, issue_number: int, labels: List[str]) -> list:
        return await self._request(
            "POST",
            f"/repos/{repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )

    async def remove_label(self, repo: str, issue_number: int, label: str) -> None:
        await self._request(
            "DELETE", f"/repos/{repo}/issues/{issue_number}/labels/{label}"
        )

    async def set_assignees(
        self, repo: str, issue_number: int, assignees: List[str]
    ) -> dict:
        return await self.update_issue(repo, issue_number, assignees=assignees)
