"""
GitHub 事件实体测试 — GitHubBaseEvent 继承 + HasAttachments

规范:
  GHE-01: GitHubBaseEvent 提供 api / user_id / sender / repo / action
  GHE-02: 所有 GitHub 事件继承 GitHubBaseEvent 的公共属性
  GHE-03: GitHubIssueEvent.reply() 调用 API
  GHE-04: get_attachments() 将 GitHubReleaseAsset 转为 Attachment
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ncatbot.event.common.base import BaseEvent
from ncatbot.event.common.factory import create_entity
from ncatbot.event.common.mixins import HasSender
from ncatbot.event.github import (
    GitHubBaseEvent,
    GitHubIssueEvent,
    GitHubIssueCommentEvent,
    GitHubPREvent,
    GitHubPRReviewCommentEvent,
    GitHubPushEvent,
    GitHubStarEvent,
    GitHubForkEvent,
    GitHubReleaseEvent,
)
from ncatbot.types.github.events import (
    GitHubIssueEventData,
    GitHubIssueCommentEventData,
    GitHubPREventData,
    GitHubPRReviewCommentEventData,
    GitHubPushEventData,
    GitHubStarEventData,
    GitHubForkEventData,
    GitHubReleaseEventData,
)
from ncatbot.types.github.models import (
    GitHubRelease,
    GitHubReleaseAsset,
    GitHubRepo,
)
from ncatbot.types.github.sender import GitHubSender
from ncatbot.types.common.attachment import Attachment
from ncatbot.types.common.attachment_list import AttachmentList


# ---- Helpers ----


def _mock_github_api() -> MagicMock:
    """创建满足 IGitHubAPIClient 接口的 mock"""
    api = MagicMock()
    api.platform = "github"
    api.create_issue_comment = AsyncMock(return_value={"id": 1})
    api.delete_comment = AsyncMock(return_value=None)
    api.list_release_assets = AsyncMock(return_value=[])
    api.get_release_by_tag = AsyncMock(return_value={})
    return api


def _make_repo() -> GitHubRepo:
    return GitHubRepo(owner="ncatbot", name="NcatBot", full_name="ncatbot/NcatBot")


def _make_sender() -> GitHubSender:
    return GitHubSender(user_id="12345", nickname="testuser", login="testuser")


# BaseEventData 必需字段
_BASE = {"time": 0, "self_id": "bot"}


# ---- GHE-01: GitHubBaseEvent 公共属性 ----


class TestGitHubBaseEvent:
    def test_ghe01_base_event_provides_common_properties(self):
        """GHE-01: GitHubBaseEvent 提供 api / user_id / sender / repo / action"""
        data = GitHubIssueEventData(
            **_BASE,
            action="opened",
            repo=_make_repo(),
            sender=_make_sender(),
            issue_number=1,
            issue_title="test",
        )
        api = _mock_github_api()
        event = GitHubIssueEvent(data, api)

        assert event.api is api
        assert event.user_id == "12345"
        assert event.sender.login == "testuser"
        assert event.repo == "ncatbot/NcatBot"
        assert event.action == "opened"

    def test_ghe01_isinstance_checks(self):
        """GitHubBaseEvent 所有子类都 isinstance BaseEvent 和 HasSender"""
        data = GitHubPushEventData(
            **_BASE,
            ref="refs/heads/main",
            repo=_make_repo(),
            sender=_make_sender(),
        )
        event = GitHubPushEvent(data, _mock_github_api())
        assert isinstance(event, BaseEvent)
        assert isinstance(event, HasSender)
        assert isinstance(event, GitHubBaseEvent)


# ---- GHE-02: 所有事件继承公共属性 ----


_EVENT_DATA_PAIRS = [
    (GitHubIssueEventData, GitHubIssueEvent, {"issue_number": 1, "issue_title": "t"}),
    (
        GitHubIssueCommentEventData,
        GitHubIssueCommentEvent,
        {"comment_body": "c", "issue_number": 1},
    ),
    (GitHubPREventData, GitHubPREvent, {"pr_number": 1, "pr_title": "t"}),
    (
        GitHubPRReviewCommentEventData,
        GitHubPRReviewCommentEvent,
        {"comment_body": "c", "pr_number": 1, "path": "f.py"},
    ),
    (GitHubPushEventData, GitHubPushEvent, {"ref": "refs/heads/main"}),
    (GitHubStarEventData, GitHubStarEvent, {"starred_at": "2026-01-01"}),
    (GitHubForkEventData, GitHubForkEvent, {}),
    (GitHubReleaseEventData, GitHubReleaseEvent, {}),
]


class TestAllEventsInherit:
    @pytest.mark.parametrize("data_cls,event_cls,extra", _EVENT_DATA_PAIRS)
    def test_ghe02_common_properties(self, data_cls, event_cls, extra):
        """GHE-02: 所有 GitHub 事件都从 GitHubBaseEvent 继承 repo/user_id/sender/action"""
        data = data_cls(
            **_BASE,
            action="created",
            repo=_make_repo(),
            sender=_make_sender(),
            **extra,
        )
        api = _mock_github_api()
        event = event_cls(data, api)

        assert isinstance(event, GitHubBaseEvent)
        assert event.repo == "ncatbot/NcatBot"
        assert event.user_id == "12345"
        assert event.sender.login == "testuser"
        assert event.action == "created"
        assert event.api is api

    @pytest.mark.parametrize("data_cls,event_cls,extra", _EVENT_DATA_PAIRS)
    def test_ghe02_factory_creates_correct_type(self, data_cls, event_cls, extra):
        """GHE-02: 工厂创建正确的事件类型"""
        data = data_cls(
            **_BASE,
            action="created",
            repo=_make_repo(),
            sender=_make_sender(),
            **extra,
        )
        entity = create_entity(data, _mock_github_api())
        assert isinstance(entity, event_cls)


# ---- GHE-03: Issue reply 调用 API ----


class TestIssueReply:
    async def test_ghe03_issue_reply(self):
        """GHE-03: GitHubIssueEvent.reply() 调用 create_issue_comment"""
        data = GitHubIssueEventData(
            **_BASE,
            action="opened",
            repo=_make_repo(),
            sender=_make_sender(),
            issue_number=42,
            issue_title="test",
        )
        api = _mock_github_api()
        event = GitHubIssueEvent(data, api)

        await event.reply("Thanks!")
        api.create_issue_comment.assert_awaited_once_with(
            repo="ncatbot/NcatBot", issue_number=42, body="Thanks!"
        )


# ---- GHE-04: HasAttachments ----


class TestHasAttachments:
    async def test_ghe04_get_attachments_converts_assets(self):
        """GHE-04: get_attachments() 将 GitHubReleaseAsset 转为 Attachment"""
        release = GitHubRelease(id="123", tag_name="v1.0.0", name="v1.0.0")
        data = GitHubReleaseEventData(
            **_BASE,
            action="published",
            repo=_make_repo(),
            sender=_make_sender(),
            release=release,
        )
        api = _mock_github_api()
        api.list_release_assets.return_value = [
            GitHubReleaseAsset(
                id="1",
                name="binary.zip",
                browser_download_url="https://example.com/dl",
                size=2048,
                content_type="application/zip",
                download_count=50,
            ),
            GitHubReleaseAsset(
                id="2",
                name="source.tar.gz",
                browser_download_url="https://example.com/src",
                size=1024,
                content_type="application/gzip",
                download_count=10,
            ),
        ]
        event = GitHubReleaseEvent(data, api)

        attachments = await event.get_attachments()
        assert len(attachments) == 2
        assert isinstance(attachments, AttachmentList)
        assert all(isinstance(a, Attachment) for a in attachments)

        att0 = attachments[0]
        assert att0.name == "binary.zip"
        assert att0.url == "https://example.com/dl"
        assert att0.size == 2048
        assert att0.content_type == "application/zip"
        assert att0.extra["id"] == "1"
        assert att0.extra["download_count"] == 50

    async def test_ghe04_get_attachments_empty(self):
        """GHE-04: get_attachments() 无 assets 时返回空列表"""
        release = GitHubRelease(id="123", tag_name="v1.0.0", name="v1.0.0")
        data = GitHubReleaseEventData(
            **_BASE,
            action="published",
            repo=_make_repo(),
            sender=_make_sender(),
            release=release,
        )
        api = _mock_github_api()
        api.list_release_assets.return_value = []
        event = GitHubReleaseEvent(data, api)

        attachments = await event.get_attachments()
        assert attachments == []
