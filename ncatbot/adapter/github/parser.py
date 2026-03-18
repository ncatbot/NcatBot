"""GitHubEventParser — GitHub 事件解析器

将 webhook payload / polling 数据转为 NcatBot 事件数据模型。
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from ncatbot.types.common.base import BaseEventData
from ncatbot.types.github.enums import GitHubUserType
from ncatbot.types.github.models import (
    GitHubCommit,
    GitHubForkee,
    GitHubRelease,
    GitHubRepo,
)
from ncatbot.types.github.sender import GitHubSender
from ncatbot.types.github.events import (
    GitHubEventData,
    GitHubIssueEventData,
    GitHubIssueCommentEventData,
    GitHubPREventData,
    GitHubPRReviewCommentEventData,
    GitHubPushEventData,
    GitHubStarEventData,
    GitHubForkEventData,
    GitHubReleaseEventData,
)
from ncatbot.utils import get_log

LOG = get_log("GitHubParser")

__all__ = [
    "GitHubEventParser",
]


class GitHubEventParser:
    """GitHub 事件解析器"""

    def __init__(self, self_id: str = "0") -> None:
        self._self_id = self_id

    # ---- 签名验证 ----

    @staticmethod
    def verify_signature(payload_body: bytes, secret: str, signature: str) -> bool:
        """验证 GitHub webhook HMAC-SHA256 签名"""
        if not secret:
            return True
        if not signature or not signature.startswith("sha256="):
            return False
        expected = hmac.new(
            secret.encode("utf-8"),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    # ---- 主解析入口 ----

    def parse(self, event_type: str, payload: dict) -> Optional[BaseEventData]:
        """按 X-GitHub-Event 头路由到具体解析方法"""
        try:
            parser = _EVENT_PARSERS.get(event_type)
            if parser is not None:
                return parser(self, payload)
        except Exception:
            LOG.debug("解析 %s 事件失败: %s", event_type, str(payload)[:200])
        return None

    # ---- 通用字段提取 ----

    def _common(self, payload: dict) -> dict:
        """提取所有事件共有的字段"""
        now = int(time.time())
        raw_repo = payload.get("repository", {})
        raw_sender = payload.get("sender", {})

        full_name = raw_repo.get("full_name", "")
        parts = full_name.split("/", 1) if full_name else ["", ""]
        repo = GitHubRepo(
            owner=parts[0] if len(parts) > 0 else "",
            name=parts[1] if len(parts) > 1 else "",
            full_name=full_name,
            id=str(raw_repo.get("id", "")),
            html_url=raw_repo.get("html_url"),
            description=raw_repo.get("description"),
            private=raw_repo.get("private", False),
            default_branch=raw_repo.get("default_branch"),
        )

        sender = GitHubSender(
            user_id=str(raw_sender.get("id", "")),
            nickname=raw_sender.get("login", ""),
            login=raw_sender.get("login", ""),
            avatar_url=raw_sender.get("avatar_url"),
            html_url=raw_sender.get("html_url"),
            user_type=raw_sender.get("type", GitHubUserType.USER),
        )

        return dict(
            time=now,
            self_id=self._self_id,
            platform="github",
            action=payload.get("action", "created"),
            repo=repo,
            sender=sender,
        )

    # ---- 各事件解析 ----

    def _parse_issue(self, payload: dict) -> GitHubIssueEventData:
        common = self._common(payload)
        issue = payload.get("issue", {})
        return GitHubIssueEventData(
            **common,
            issue_number=issue.get("number", 0),
            issue_title=issue.get("title", ""),
            issue_body=issue.get("body", "") or "",
            issue_state=issue.get("state", "open"),
            issue_url=issue.get("html_url", ""),
            labels=[lb.get("name", "") for lb in issue.get("labels", [])],
            assignees=[a.get("login", "") for a in issue.get("assignees", [])],
        )

    def _parse_issue_comment(self, payload: dict) -> GitHubIssueCommentEventData:
        common = self._common(payload)
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        return GitHubIssueCommentEventData(
            **common,
            comment_id=str(comment.get("id", "")),
            comment_body=comment.get("body", "") or "",
            comment_url=comment.get("html_url", ""),
            issue_number=issue.get("number", 0),
            issue_title=issue.get("title", ""),
        )

    def _parse_pr(self, payload: dict) -> GitHubPREventData:
        common = self._common(payload)
        pr = payload.get("pull_request", {})
        head = pr.get("head", {})
        base = pr.get("base", {})
        return GitHubPREventData(
            **common,
            pr_number=pr.get("number", 0),
            pr_title=pr.get("title", ""),
            pr_body=pr.get("body", "") or "",
            pr_state=pr.get("state", "open"),
            pr_url=pr.get("html_url", ""),
            head_ref=head.get("ref", ""),
            base_ref=base.get("ref", ""),
            merged=pr.get("merged", False),
            draft=pr.get("draft", False),
        )

    def _parse_pr_review_comment(self, payload: dict) -> GitHubPRReviewCommentEventData:
        common = self._common(payload)
        comment = payload.get("comment", {})
        pr = payload.get("pull_request", {})
        return GitHubPRReviewCommentEventData(
            **common,
            comment_id=str(comment.get("id", "")),
            comment_body=comment.get("body", "") or "",
            comment_url=comment.get("html_url", ""),
            pr_number=pr.get("number", 0),
            diff_hunk=comment.get("diff_hunk", ""),
            path=comment.get("path", ""),
        )

    def _parse_push(self, payload: dict) -> GitHubPushEventData:
        common = self._common(payload)
        pusher = payload.get("pusher", {})

        commits = []
        for c in payload.get("commits", []):
            author = c.get("author", {})
            commits.append(
                GitHubCommit(
                    sha=c.get("id", ""),
                    message=c.get("message", ""),
                    author_name=author.get("name", ""),
                    author_email=author.get("email", ""),
                    url=c.get("url"),
                    timestamp=c.get("timestamp"),
                    added=c.get("added", []),
                    removed=c.get("removed", []),
                    modified=c.get("modified", []),
                )
            )

        head_commit_raw = payload.get("head_commit")
        head_commit = None
        if head_commit_raw and isinstance(head_commit_raw, dict):
            hc_author = head_commit_raw.get("author", {})
            head_commit = GitHubCommit(
                sha=head_commit_raw.get("id", ""),
                message=head_commit_raw.get("message", ""),
                author_name=hc_author.get("name", ""),
                author_email=hc_author.get("email", ""),
                url=head_commit_raw.get("url"),
                timestamp=head_commit_raw.get("timestamp"),
                added=head_commit_raw.get("added", []),
                removed=head_commit_raw.get("removed", []),
                modified=head_commit_raw.get("modified", []),
            )

        return GitHubPushEventData(
            **common,
            ref=payload.get("ref", ""),
            before=payload.get("before", ""),
            after=payload.get("after", ""),
            commits=commits,
            head_commit=head_commit,
            pusher_name=pusher.get("name", ""),
            pusher_email=pusher.get("email", ""),
        )

    def _parse_star(self, payload: dict) -> GitHubStarEventData:
        common = self._common(payload)
        return GitHubStarEventData(
            **common,
            starred_at=payload.get("starred_at", "") or "",
        )

    def _parse_fork(self, payload: dict) -> GitHubForkEventData:
        common = self._common(payload)
        raw_forkee = payload.get("forkee", {})
        forkee = GitHubForkee(
            full_name=raw_forkee.get("full_name", ""),
            html_url=raw_forkee.get("html_url"),
            owner=(raw_forkee.get("owner", {}) or {}).get("login", ""),
            description=raw_forkee.get("description"),
        )
        return GitHubForkEventData(
            **common,
            forkee=forkee,
        )

    def _parse_release(self, payload: dict) -> GitHubReleaseEventData:
        common = self._common(payload)
        raw_release = payload.get("release", {})
        release = GitHubRelease(
            id=str(raw_release.get("id", "")),
            tag_name=raw_release.get("tag_name", ""),
            name=raw_release.get("name", "") or "",
            body=raw_release.get("body", "") or "",
            prerelease=raw_release.get("prerelease", False),
            draft=raw_release.get("draft", False),
            html_url=raw_release.get("html_url"),
        )
        return GitHubReleaseEventData(
            **common,
            release=release,
        )

    def _parse_ping(self, payload: dict) -> GitHubEventData:
        """GitHub webhook 配置完成后的 ping 事件"""
        common = self._common(payload)
        common["action"] = "ping"
        return GitHubEventData(**common)


# 事件类型 → 解析方法注册表
_EVENT_PARSERS = {
    "issues": GitHubEventParser._parse_issue,
    "issue_comment": GitHubEventParser._parse_issue_comment,
    "pull_request": GitHubEventParser._parse_pr,
    "pull_request_review_comment": GitHubEventParser._parse_pr_review_comment,
    "push": GitHubEventParser._parse_push,
    "watch": GitHubEventParser._parse_star,
    "fork": GitHubEventParser._parse_fork,
    "release": GitHubEventParser._parse_release,
    "ping": GitHubEventParser._parse_ping,
}
