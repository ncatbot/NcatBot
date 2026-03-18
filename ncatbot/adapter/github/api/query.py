"""Query API Mixin"""

from __future__ import annotations

from typing import Any


class QueryAPIMixin:
    """查询操作"""

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any: ...

    async def get_repo(self, repo: str) -> dict:
        return await self._request("GET", f"/repos/{repo}")

    async def get_user(self, username: str) -> dict:
        return await self._request("GET", f"/users/{username}")

    async def get_authenticated_user(self) -> dict:
        return await self._request("GET", "/user")
