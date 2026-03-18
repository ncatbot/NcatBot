# GitHub API 使用

> 通过 `self.api.github` 调用 GitHub REST API — Issue 管理、评论操作、PR 管理与信息查询。

---

## Quick Start

```python
from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent
from ncatbot.plugin import NcatBotPlugin

class MyPlugin(NcatBotPlugin):
    name = "github_ops"
    version = "1.0.0"

    @registrar.github.on_issue()
    async def on_issue(self, event: GitHubIssueEvent):
        if event.action == "opened":
            # 自动添加标签
            await self.api.github.add_labels(event.repo, event.issue_number, ["triage"])
            # 评论
            await self.api.github.create_issue_comment(
                event.repo, event.issue_number, "已标记为 triage，等待处理。"
            )
```

---

## Quick Reference

### 访问方式

| 方式 | 调用 |
|------|------|
| 插件内 | `self.api.github.*` |
| 按名称 | `self.api.platform("github").*` |
| 查看平台 | `self.api.platforms` |

### API 功能分类

| 类别 | 方法数 | 典型操作 |
|------|--------|---------|
| Issue 管理 | 8 | 创建 / 更新 / 关闭 / 重开 / 标签 / 指派 |
| 评论操作 | 4 | 创建 / 更新 / 删除 / 列出 |
| PR 管理 | 5 | 评论 / 合并 / 关闭 / 请求审查 / 查询 |
| 信息查询 | 3 | 查仓库 / 查用户 / 查认证用户 |

### 方法速查

| 方法 | 说明 |
|------|------|
| `create_issue(repo, title, body, labels, assignees)` | 创建 Issue |
| `update_issue(repo, issue_number, *, title, body, state, labels, assignees)` | 更新 Issue |
| `close_issue(repo, issue_number)` | 关闭 Issue |
| `reopen_issue(repo, issue_number)` | 重开 Issue |
| `get_issue(repo, issue_number)` | 查询 Issue |
| `add_labels(repo, issue_number, labels)` | 添加标签 |
| `remove_label(repo, issue_number, label)` | 移除标签 |
| `set_assignees(repo, issue_number, assignees)` | 设置指派人 |
| `create_issue_comment(repo, issue_number, body)` | 创建评论 |
| `update_comment(repo, comment_id, body)` | 更新评论 |
| `delete_comment(repo, comment_id)` | 删除评论 |
| `list_issue_comments(repo, issue_number, page, per_page)` | 列出评论 |
| `create_pr_comment(repo, pr_number, body)` | PR 评论 |
| `merge_pr(repo, pr_number, *, merge_method, commit_title, commit_message)` | 合并 PR |
| `close_pr(repo, pr_number)` | 关闭 PR |
| `request_review(repo, pr_number, reviewers)` | 请求审查 |
| `get_pr(repo, pr_number)` | 查询 PR |
| `get_repo(repo)` | 查询仓库 |
| `get_user(username)` | 查询用户 |
| `get_authenticated_user()` | 查询当前认证用户 |

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [1_issue_comment.md](1_issue_comment.md) | Issue CRUD、Label、Assignee、评论操作 |
| [2_pr_query.md](2_pr_query.md) | PR 评论 / 合并 / 审查 + 信息查询 |

---

> **相关**：[GitHub 消息发送](../../send_message/github/README.md) · [GitHub API 参考](../../../reference/api/github/1_api.md) · [跨平台 Trait](../common/2_traits.md)
