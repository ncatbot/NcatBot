"""
GitHub API Mixin 类型化返回测试

规范:
  GHA-01: QueryAPIMixin 返回 GitHubRepoInfo / GitHubUserInfo
  GHA-02: IssueAPIMixin 返回 GitHubIssueInfo / GitHubLabelInfo
  GHA-03: CommentAPIMixin 返回 GitHubCommentInfo
  GHA-04: PRAPIMixin 返回 GitHubPullRequestInfo / GitHubMergeResult / GitHubCommentInfo
  GHA-05: ReleaseAPIMixin 返回 GitHubReleaseInfo
"""

from __future__ import annotations

from typing import Any

import pytest

from ncatbot.adapter.github.api.query import QueryAPIMixin
from ncatbot.adapter.github.api.issue import IssueAPIMixin
from ncatbot.adapter.github.api.comment import CommentAPIMixin
from ncatbot.adapter.github.api.pr import PRAPIMixin
from ncatbot.adapter.github.api.release import ReleaseAPIMixin

from ncatbot.types.github.models import (
    GitHubCommentInfo,
    GitHubIssueInfo,
    GitHubLabelInfo,
    GitHubMergeResult,
    GitHubPullRequestInfo,
    GitHubReleaseAsset,
    GitHubReleaseInfo,
    GitHubRepoInfo,
    GitHubUserInfo,
)

pytestmark = pytest.mark.asyncio


# ---- Helpers ----


class _StubQuery(QueryAPIMixin):
    def __init__(self, response: Any):
        self._response = response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._response


class _StubIssue(IssueAPIMixin):
    def __init__(self, response: Any):
        self._response = response
        self._session = None
        self._base_url = ""

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._response


class _StubComment(CommentAPIMixin):
    def __init__(self, response: Any):
        self._response = response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._response


class _StubPR(PRAPIMixin):
    def __init__(self, response: Any):
        self._response = response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._response


class _StubRelease(ReleaseAPIMixin):
    def __init__(self, response: Any):
        self._response = response

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._response


# ---- GHA-01: Query ----


class TestQueryAPIMixin:
    async def test_gha01_get_repo(self):
        """GHA-01: get_repo 返回 GitHubRepoInfo"""
        raw = {"id": 1, "name": "repo", "full_name": "owner/repo"}
        api = _StubQuery(raw)
        result = await api.get_repo("owner/repo")
        assert isinstance(result, GitHubRepoInfo)
        assert result.full_name == "owner/repo"

    async def test_gha01_get_user(self):
        """GHA-01: get_user 返回 GitHubUserInfo"""
        raw = {"login": "octocat", "id": 1}
        api = _StubQuery(raw)
        result = await api.get_user("octocat")
        assert isinstance(result, GitHubUserInfo)
        assert result.login == "octocat"

    async def test_gha01_get_authenticated_user(self):
        """GHA-01: get_authenticated_user 返回 GitHubUserInfo"""
        raw = {"login": "botuser", "id": 2}
        api = _StubQuery(raw)
        result = await api.get_authenticated_user()
        assert isinstance(result, GitHubUserInfo)


# ---- GHA-02: Issue ----


class TestIssueAPIMixin:
    async def test_gha02_create_issue(self):
        """GHA-02: create_issue 返回 GitHubIssueInfo"""
        raw = {"id": 10, "number": 1, "title": "test", "state": "open"}
        api = _StubIssue(raw)
        result = await api.create_issue("owner/repo", "test")
        assert isinstance(result, GitHubIssueInfo)
        assert result.title == "test"

    async def test_gha02_get_issue(self):
        """GHA-02: get_issue 返回 GitHubIssueInfo"""
        raw = {"id": 10, "number": 1, "title": "bug", "state": "open"}
        api = _StubIssue(raw)
        result = await api.get_issue("owner/repo", 1)
        assert isinstance(result, GitHubIssueInfo)

    async def test_gha02_add_labels(self):
        """GHA-02: add_labels 返回 List[GitHubLabelInfo]"""
        raw = [
            {"id": 1, "name": "bug", "color": "d73a4a"},
            {"id": 2, "name": "help wanted", "color": "008672"},
        ]
        api = _StubIssue(raw)
        result = await api.add_labels("owner/repo", 1, ["bug", "help wanted"])
        assert len(result) == 2
        assert all(isinstance(r, GitHubLabelInfo) for r in result)


# ---- GHA-03: Comment ----


class TestCommentAPIMixin:
    async def test_gha03_create_comment(self):
        """GHA-03: create_issue_comment 返回 GitHubCommentInfo"""
        raw = {"id": 100, "body": "LGTM"}
        api = _StubComment(raw)
        result = await api.create_issue_comment("owner/repo", 1, "LGTM")
        assert isinstance(result, GitHubCommentInfo)
        assert result.body == "LGTM"

    async def test_gha03_list_comments(self):
        """GHA-03: list_issue_comments 返回 List[GitHubCommentInfo]"""
        raw = [{"id": 100, "body": "A"}, {"id": 101, "body": "B"}]
        api = _StubComment(raw)
        result = await api.list_issue_comments("owner/repo", 1)
        assert len(result) == 2
        assert all(isinstance(r, GitHubCommentInfo) for r in result)


# ---- GHA-04: PR ----


class TestPRAPIMixin:
    async def test_gha04_get_pr(self):
        """GHA-04: get_pr 返回 GitHubPullRequestInfo"""
        raw = {"id": 200, "number": 5, "title": "feat", "state": "open"}
        api = _StubPR(raw)
        result = await api.get_pr("owner/repo", 5)
        assert isinstance(result, GitHubPullRequestInfo)

    async def test_gha04_merge_pr(self):
        """GHA-04: merge_pr 返回 GitHubMergeResult"""
        raw = {"sha": "abc", "merged": True, "message": "ok"}
        api = _StubPR(raw)
        result = await api.merge_pr("owner/repo", 5)
        assert isinstance(result, GitHubMergeResult)
        assert result.merged is True

    async def test_gha04_close_pr(self):
        """GHA-04: close_pr 返回 GitHubPullRequestInfo"""
        raw = {"id": 200, "number": 5, "title": "feat", "state": "closed"}
        api = _StubPR(raw)
        result = await api.close_pr("owner/repo", 5)
        assert isinstance(result, GitHubPullRequestInfo)
        assert result.state == "closed"

    async def test_gha04_create_pr_comment(self):
        """GHA-04: create_pr_comment 返回 GitHubCommentInfo"""
        raw = {"id": 300, "body": "Nice"}
        api = _StubPR(raw)
        result = await api.create_pr_comment("owner/repo", 5, "Nice")
        assert isinstance(result, GitHubCommentInfo)


# ---- GHA-05: Release ----


class TestReleaseAPIMixin:
    async def test_gha05_get_release(self):
        """GHA-05: get_release 返回 GitHubReleaseInfo"""
        raw = {"id": "400", "tag_name": "v1.0", "name": "v1.0", "body": "notes"}
        api = _StubRelease(raw)
        result = await api.get_release("owner/repo", 400)
        assert isinstance(result, GitHubReleaseInfo)
        assert result.tag_name == "v1.0"

    async def test_gha05_get_latest_release(self):
        """GHA-05: get_latest_release 返回 GitHubReleaseInfo"""
        raw = {"id": "500", "tag_name": "v2.0", "name": "v2.0", "body": ""}
        api = _StubRelease(raw)
        result = await api.get_latest_release("owner/repo")
        assert isinstance(result, GitHubReleaseInfo)

    async def test_gha05_list_release_assets(self):
        """GHA-05: list_release_assets 返回 List[GitHubReleaseAsset]"""
        raw = [
            {
                "id": 1,
                "name": "a.zip",
                "size": 100,
                "browser_download_url": "https://dl",
            }
        ]
        api = _StubRelease(raw)
        result = await api.list_release_assets("owner/repo", 400)
        assert len(result) == 1
        assert isinstance(result[0], GitHubReleaseAsset)
