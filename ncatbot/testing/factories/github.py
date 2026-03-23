"""
GitHub 事件工厂 — 快速构建测试用 GitHub 平台 BaseEventData 实例
"""

from __future__ import annotations

import time
from typing import Any, List, Optional

from ncatbot.types.github.events import (
    GitHubIssueEventData,
    GitHubIssueCommentEventData,
    GitHubPREventData,
    GitHubPushEventData,
    GitHubStarEventData,
    GitHubReleaseEventData,
)


def _now() -> int:
    return int(time.time())


def _repo(repo: str) -> dict:
    parts = repo.split("/", 1)
    owner = parts[0] if len(parts) == 2 else ""
    name = parts[1] if len(parts) == 2 else repo
    return {"owner": owner, "name": name, "full_name": repo}


def _sender(login: str) -> dict:
    return {"user_id": login, "nickname": login, "login": login}


def issue_opened(
    title: str = "Bug report",
    body: str = "",
    *,
    repo: str = "owner/repo",
    issue_number: int = 1,
    login: str = "test-user",
    labels: Optional[List[str]] = None,
    **extra: Any,
) -> GitHubIssueEventData:
    """构造 Issue opened 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "issue",
        "action": "opened",
        "repo": _repo(repo),
        "sender": _sender(login),
        "issue_number": issue_number,
        "issue_title": title,
        "issue_body": body,
        "issue_state": "open",
        "labels": labels or [],
        **extra,
    }
    return GitHubIssueEventData.model_validate(data)


def issue_closed(
    title: str = "Bug report",
    *,
    repo: str = "owner/repo",
    issue_number: int = 1,
    login: str = "test-user",
    **extra: Any,
) -> GitHubIssueEventData:
    """构造 Issue closed 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "issue",
        "action": "closed",
        "repo": _repo(repo),
        "sender": _sender(login),
        "issue_number": issue_number,
        "issue_title": title,
        "issue_state": "closed",
        **extra,
    }
    return GitHubIssueEventData.model_validate(data)


def issue_comment(
    body: str = "LGTM",
    *,
    repo: str = "owner/repo",
    issue_number: int = 1,
    comment_id: str = "c_001",
    login: str = "test-user",
    **extra: Any,
) -> GitHubIssueCommentEventData:
    """构造 Issue 评论事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "comment",
        "action": "created",
        "repo": _repo(repo),
        "sender": _sender(login),
        "comment_id": comment_id,
        "comment_body": body,
        "issue_number": issue_number,
        **extra,
    }
    return GitHubIssueCommentEventData.model_validate(data)


def pr_opened(
    title: str = "Fix bug",
    body: str = "",
    *,
    repo: str = "owner/repo",
    pr_number: int = 1,
    head_ref: str = "feature",
    base_ref: str = "main",
    login: str = "test-user",
    **extra: Any,
) -> GitHubPREventData:
    """构造 PR opened 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "pull_request",
        "action": "opened",
        "repo": _repo(repo),
        "sender": _sender(login),
        "pr_number": pr_number,
        "pr_title": title,
        "pr_body": body,
        "pr_state": "open",
        "head_ref": head_ref,
        "base_ref": base_ref,
        **extra,
    }
    return GitHubPREventData.model_validate(data)


def push(
    ref: str = "refs/heads/main",
    *,
    repo: str = "owner/repo",
    login: str = "test-user",
    before: str = "0" * 40,
    after: str = "a" * 40,
    **extra: Any,
) -> GitHubPushEventData:
    """构造 Push 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "push",
        "action": "created",
        "repo": _repo(repo),
        "sender": _sender(login),
        "ref": ref,
        "before": before,
        "after": after,
        **extra,
    }
    return GitHubPushEventData.model_validate(data)


def star(
    *,
    repo: str = "owner/repo",
    login: str = "test-user",
    action: str = "created",
    **extra: Any,
) -> GitHubStarEventData:
    """构造 Star 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "star",
        "action": action,
        "repo": _repo(repo),
        "sender": _sender(login),
        **extra,
    }
    return GitHubStarEventData.model_validate(data)


def release_published(
    tag_name: str = "v1.0.0",
    name: str = "Release v1.0.0",
    body: str = "",
    *,
    repo: str = "owner/repo",
    login: str = "test-user",
    **extra: Any,
) -> GitHubReleaseEventData:
    """构造 Release published 事件"""
    data = {
        "time": _now(),
        "self_id": "gh_bot",
        "platform": "github",
        "post_type": "release",
        "action": "published",
        "repo": _repo(repo),
        "sender": _sender(login),
        "release": {
            "tag_name": tag_name,
            "name": name,
            "body": body,
        },
        **extra,
    }
    return GitHubReleaseEventData.model_validate(data)
