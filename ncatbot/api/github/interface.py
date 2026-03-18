"""IGitHubAPIClient — GitHub 平台 API 接口

定义 GitHub 适配器所有可用 API 方法。
由 GitHubBotAPI 实现。
"""

from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional, Union

from ncatbot.api.base import IAPIClient
from ncatbot.types.github.enums import GitHubMergeMethod


class IGitHubAPIClient(IAPIClient):
    """GitHub 平台 Bot API 接口"""

    # ---- Issue 操作 ----

    @abstractmethod
    async def create_issue(
        self,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> dict:
        """创建 Issue"""

    @abstractmethod
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
        """更新 Issue"""

    @abstractmethod
    async def close_issue(self, repo: str, issue_number: int) -> dict:
        """关闭 Issue"""

    @abstractmethod
    async def reopen_issue(self, repo: str, issue_number: int) -> dict:
        """重新打开 Issue"""

    @abstractmethod
    async def get_issue(self, repo: str, issue_number: int) -> dict:
        """获取 Issue 详情"""

    @abstractmethod
    async def add_labels(self, repo: str, issue_number: int, labels: List[str]) -> list:
        """添加标签"""

    @abstractmethod
    async def remove_label(self, repo: str, issue_number: int, label: str) -> None:
        """移除标签"""

    @abstractmethod
    async def set_assignees(
        self, repo: str, issue_number: int, assignees: List[str]
    ) -> dict:
        """设置负责人"""

    # ---- 评论操作 ----

    @abstractmethod
    async def create_issue_comment(
        self, repo: str, issue_number: int, body: str
    ) -> dict:
        """创建 Issue/PR 评论"""

    @abstractmethod
    async def update_comment(self, repo: str, comment_id: int, body: str) -> dict:
        """更新评论"""

    @abstractmethod
    async def delete_comment(self, repo: str, comment_id: int) -> None:
        """删除评论"""

    @abstractmethod
    async def list_issue_comments(
        self, repo: str, issue_number: int, page: int = 1, per_page: int = 30
    ) -> list:
        """列出评论"""

    # ---- PR 操作 ----

    @abstractmethod
    async def create_pr_comment(self, repo: str, pr_number: int, body: str) -> dict:
        """创建 PR 评论 (等同 create_issue_comment)"""

    @abstractmethod
    async def merge_pr(
        self,
        repo: str,
        pr_number: int,
        *,
        merge_method: Union[GitHubMergeMethod, str] = GitHubMergeMethod.MERGE,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> dict:
        """合并 PR"""

    @abstractmethod
    async def close_pr(self, repo: str, pr_number: int) -> dict:
        """关闭 PR"""

    @abstractmethod
    async def request_review(
        self, repo: str, pr_number: int, reviewers: List[str]
    ) -> dict:
        """请求 Review"""

    @abstractmethod
    async def get_pr(self, repo: str, pr_number: int) -> dict:
        """获取 PR 详情"""

    # ---- 查询 ----

    @abstractmethod
    async def get_repo(self, repo: str) -> dict:
        """获取仓库信息"""

    @abstractmethod
    async def get_user(self, username: str) -> dict:
        """获取用户信息"""

    @abstractmethod
    async def get_authenticated_user(self) -> dict:
        """获取当前认证用户"""
