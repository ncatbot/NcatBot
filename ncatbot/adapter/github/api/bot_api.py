"""GitHubBotAPI — GitHub 平台 API 主实现

组合所有 Mixin 并实现 IGitHubAPIClient 接口。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp

from ncatbot.api.github import IGitHubAPIClient
from ncatbot.utils import get_log

from .issue import IssueAPIMixin
from .comment import CommentAPIMixin
from .pr import PRAPIMixin
from .query import QueryAPIMixin

LOG = get_log("GitHubBotAPI")

_BASE_URL = "https://api.github.com"


class GitHubBotAPI(
    IssueAPIMixin,
    CommentAPIMixin,
    PRAPIMixin,
    QueryAPIMixin,
    IGitHubAPIClient,
):
    """GitHub 平台 IGitHubAPIClient 实现"""

    @property
    def platform(self) -> str:
        return "github"

    def __init__(self, token: str) -> None:
        self._token = token
        self._base_url = _BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None

    async def ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers: Dict[str, str] = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """统一 HTTP 请求"""
        session = await self.ensure_session()
        url = f"{self._base_url}{path}"
        async with session.request(method, url, **kwargs) as resp:
            # 记录速率限制
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) < 100:
                LOG.warning("GitHub API 速率限制接近: remaining=%s", remaining)

            if resp.status == 204:
                return None
            body = await resp.json()
            if resp.status >= 400:
                msg = body.get("message", "") if isinstance(body, dict) else str(body)
                LOG.error(
                    "GitHub API 错误: %s %s → %d %s", method, path, resp.status, msg
                )
                raise aiohttp.ClientResponseError(
                    request_info=resp.request_info,
                    history=resp.history,
                    status=resp.status,
                    message=msg,
                )
            return body

    async def call(self, action: str, params: Optional[dict] = None) -> Any:
        """通用 API 调用入口 — 按 action 名分派到对应方法"""
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"未知的 API action: {action}")
        if params:
            return await method(**params)
        return await method()
