"""GitHub 平台数据结构"""

from __future__ import annotations

from typing import List, Optional


from pydantic import Field

from ._base import GitHubModel

__all__ = [
    # 事件内嵌模型
    "GitHubRepo",
    "GitHubCommit",
    "GitHubRelease",
    "GitHubReleaseAsset",
    "GitHubForkee",
    # API 响应模型
    "GitHubUserInfo",
    "GitHubLabelInfo",
    "GitHubBranchRef",
    "GitHubIssueInfo",
    "GitHubCommentInfo",
    "GitHubPullRequestInfo",
    "GitHubMergeResult",
    "GitHubReleaseInfo",
    "GitHubRepoInfo",
]


# ====================================================================
# 事件内嵌模型（Webhook payload 中的简化字段）
# ====================================================================


class GitHubRepo(GitHubModel):
    """仓库信息"""

    owner: str = ""
    name: str = ""
    full_name: str = ""
    id: str = ""
    html_url: Optional[str] = None
    description: Optional[str] = None
    private: bool = False
    default_branch: Optional[str] = None


class GitHubCommit(GitHubModel):
    """Commit 信息"""

    sha: str = ""
    message: str = ""
    author_name: str = ""
    author_email: str = ""
    url: Optional[str] = None
    timestamp: Optional[str] = None
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    modified: List[str] = Field(default_factory=list)


class GitHubRelease(GitHubModel):
    """Release 信息"""

    id: str = ""
    tag_name: str = ""
    name: str = ""
    body: str = ""
    prerelease: bool = False
    draft: bool = False
    html_url: Optional[str] = None


class GitHubReleaseAsset(GitHubModel):
    """Release Asset 信息"""

    id: str = ""
    name: str = ""
    content_type: str = ""
    size: int = 0
    download_count: int = 0
    browser_download_url: str = ""
    created_at: Optional[str] = None


class GitHubForkee(GitHubModel):
    """Fork 目标仓库信息"""

    full_name: str = ""
    html_url: Optional[str] = None
    owner: str = ""
    description: Optional[str] = None


# ====================================================================
# API 响应模型（忠实映射 REST API 返回结构）
# ====================================================================


class GitHubUserInfo(GitHubModel):
    """用户信息 — GET /users/{username}, GET /user"""

    login: str = ""
    id: int = 0
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    type: str = "User"
    name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0


class GitHubLabelInfo(GitHubModel):
    """标签信息"""

    id: int = 0
    name: str = ""
    color: str = ""
    description: Optional[str] = None


class GitHubBranchRef(GitHubModel):
    """PR 分支引用"""

    ref: str = ""
    sha: str = ""
    label: str = ""


class GitHubIssueInfo(GitHubModel):
    """Issue 详情 — GET /repos/{owner}/{repo}/issues/{number}"""

    id: int = 0
    number: int = 0
    title: str = ""
    body: Optional[str] = None
    state: str = ""
    html_url: Optional[str] = None
    user: Optional[GitHubUserInfo] = None
    labels: List[GitHubLabelInfo] = Field(default_factory=list)
    assignees: List[GitHubUserInfo] = Field(default_factory=list)
    comments: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    closed_at: Optional[str] = None


class GitHubCommentInfo(GitHubModel):
    """评论详情"""

    id: int = 0
    body: str = ""
    user: Optional[GitHubUserInfo] = None
    html_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GitHubPullRequestInfo(GitHubModel):
    """PR 详情 — GET /repos/{owner}/{repo}/pulls/{number}"""

    id: int = 0
    number: int = 0
    title: str = ""
    body: Optional[str] = None
    state: str = ""
    html_url: Optional[str] = None
    head: Optional[GitHubBranchRef] = None
    base: Optional[GitHubBranchRef] = None
    user: Optional[GitHubUserInfo] = None
    merged: bool = False
    draft: bool = False
    mergeable: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GitHubMergeResult(GitHubModel):
    """PR 合并结果 — PUT /repos/{owner}/{repo}/pulls/{number}/merge"""

    sha: str = ""
    merged: bool = False
    message: str = ""


class GitHubReleaseInfo(GitHubRelease):
    """Release 完整信息 — GET /repos/{owner}/{repo}/releases/{id}

    继承事件内嵌 ``GitHubRelease``，补充 API 返回的完整字段。
    """

    author: Optional[GitHubUserInfo] = None
    assets: List[GitHubReleaseAsset] = Field(default_factory=list)
    created_at: Optional[str] = None
    published_at: Optional[str] = None
    tarball_url: Optional[str] = None
    zipball_url: Optional[str] = None


class GitHubRepoInfo(GitHubModel):
    """仓库完整信息 — GET /repos/{owner}/{repo}"""

    id: int = 0
    name: str = ""
    full_name: str = ""
    owner: Optional[GitHubUserInfo] = None
    private: bool = False
    html_url: Optional[str] = None
    description: Optional[str] = None
    fork: bool = False
    default_branch: str = "main"
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
