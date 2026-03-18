"""GitHub SourceManager — Webhook / Polling 双模式数据源管理

Webhook 模式：启动 aiohttp HTTP Server 接收 GitHub webhook。
Polling 模式：定时调用 GitHub Events API 获取事件。
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import aiohttp
from aiohttp import web

from ncatbot.utils import get_log

LOG = get_log("GitHubSource")


class SourceManager:
    """GitHub 数据源管理器"""

    def __init__(
        self,
        *,
        callback: Callable[[str, dict], Awaitable[None]],
        mode: str = "webhook",
        token: str = "",
        repos: Optional[List[str]] = None,
        # webhook
        webhook_host: str = "0.0.0.0",
        webhook_port: int = 8080,
        webhook_path: str = "/webhook",
        webhook_secret: str = "",
        # polling
        poll_interval: float = 60.0,
    ) -> None:
        self._callback = callback
        self._mode = mode
        self._token = token
        self._repos = repos or []
        # webhook
        self._webhook_host = webhook_host
        self._webhook_port = webhook_port
        self._webhook_path = webhook_path
        self._webhook_secret = webhook_secret
        # polling
        self._poll_interval = poll_interval
        self._etags: Dict[str, str] = {}
        self._seen_ids: Set[str] = set()
        # runtime
        self._runner: Optional[web.AppRunner] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._stop_event = asyncio.Event()

    async def run_forever(self) -> None:
        """阻塞运行，直到 stop() 被调用"""
        if self._mode == "webhook":
            await self._run_webhook()
        else:
            await self._run_polling()

    async def stop(self) -> None:
        """停止数据源"""
        self._stop_event.set()
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
        if self._session is not None:
            await self._session.close()
            self._session = None

    # ==================== Webhook 模式 ====================

    async def _run_webhook(self) -> None:
        app = web.Application()
        app.router.add_post(self._webhook_path, self._handle_webhook)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self._webhook_host, self._webhook_port)
        await site.start()

        LOG.info(
            "GitHub Webhook Server 已启动: http://%s:%d%s",
            self._webhook_host,
            self._webhook_port,
            self._webhook_path,
        )

        # 阻塞直到 stop
        await self._stop_event.wait()

    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """处理 GitHub webhook POST 请求"""
        from ncatbot.adapter.github.parser import GitHubEventParser

        body = await request.read()

        # 签名验证
        if self._webhook_secret:
            signature = request.headers.get("X-Hub-Signature-256", "")
            if not GitHubEventParser.verify_signature(
                body, self._webhook_secret, signature
            ):
                LOG.warning("Webhook 签名验证失败")
                return web.Response(status=403, text="Invalid signature")

        event_type = request.headers.get("X-GitHub-Event", "")
        if not event_type:
            return web.Response(status=400, text="Missing X-GitHub-Event header")

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return web.Response(status=400, text="Invalid JSON")

        LOG.info(
            "Webhook 事件: type=%s, action=%s", event_type, payload.get("action", "N/A")
        )
        # 异步回调，不阻塞响应
        asyncio.ensure_future(self._callback(event_type, payload))

        return web.Response(status=200, text="OK")

    # ==================== Polling 模式 ====================

    async def _run_polling(self) -> None:
        headers: Dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        self._session = aiohttp.ClientSession(headers=headers)

        LOG.info(
            "GitHub Polling 已启动 (repos: %s, interval: %.0fs)",
            self._repos,
            self._poll_interval,
        )

        try:
            while not self._stop_event.is_set():
                for repo in self._repos:
                    await self._poll_repo(repo)
                # 等待下一轮或被停止
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._poll_interval,
                    )
                    break  # stop_event 被设置
                except asyncio.TimeoutError:
                    pass  # 超时 → 继续下一轮
        finally:
            if self._session is not None:
                await self._session.close()
                self._session = None

    async def _poll_repo(self, repo: str) -> None:
        """轮询单个仓库的事件"""
        if self._session is None:
            return

        url = f"https://api.github.com/repos/{repo}/events"
        req_headers: Dict[str, str] = {}

        # ETag 增量获取
        etag = self._etags.get(repo)
        if etag:
            req_headers["If-None-Match"] = etag

        try:
            async with self._session.get(url, headers=req_headers) as resp:
                # 检查速率限制
                remaining = resp.headers.get("X-RateLimit-Remaining")
                if remaining is not None and int(remaining) < 100:
                    LOG.warning(
                        "GitHub API 速率限制接近: remaining=%s, repo=%s",
                        remaining,
                        repo,
                    )

                if resp.status == 304:
                    return  # 无新事件

                if resp.status != 200:
                    LOG.debug("轮询 %s 失败: HTTP %d", repo, resp.status)
                    return

                # 保存 ETag
                new_etag = resp.headers.get("ETag")
                if new_etag:
                    self._etags[repo] = new_etag

                events: Any = await resp.json()
                if not isinstance(events, list):
                    return

                # 反向遍历（最旧的先处理）
                for event in reversed(events):
                    event_id = str(event.get("id", ""))
                    if event_id in self._seen_ids:
                        continue
                    self._seen_ids.add(event_id)

                    event_type = event.get("type", "")
                    payload = event.get("payload", {})

                    # GitHub Events API 的 type 与 webhook event 类型映射
                    webhook_type = _POLL_TYPE_MAP.get(event_type)
                    if webhook_type is None:
                        continue

                    # 注入 repository 和 sender (polling payload 结构不同)
                    if "repository" not in payload:
                        payload["repository"] = event.get("repo", {})
                        # Events API 的 repo 只有 id/name，补充 full_name
                        repo_obj = payload["repository"]
                        if "full_name" not in repo_obj and "name" in repo_obj:
                            repo_obj["full_name"] = repo_obj["name"]
                    if "sender" not in payload:
                        payload["sender"] = event.get("actor", {})

                    await self._callback(webhook_type, payload)

        except aiohttp.ClientError as e:
            LOG.debug("轮询 %s 网络错误: %s", repo, e)

        # 清理过多的已见 ID（保留最近 5000 条）
        if len(self._seen_ids) > 5000:
            excess = len(self._seen_ids) - 3000
            it = iter(self._seen_ids)
            to_remove = [next(it) for _ in range(excess)]
            self._seen_ids -= set(to_remove)


# Events API type → webhook event type 映射
_POLL_TYPE_MAP: Dict[str, str] = {
    "IssuesEvent": "issues",
    "IssueCommentEvent": "issue_comment",
    "PullRequestEvent": "pull_request",
    "PullRequestReviewCommentEvent": "pull_request_review_comment",
    "PushEvent": "push",
    "WatchEvent": "watch",
    "ForkEvent": "fork",
    "ReleaseEvent": "release",
}
