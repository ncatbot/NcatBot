# PR 与查询 API

> Pull Request 评论、合并、关闭、审查请求，以及仓库 / 用户信息查询。

---

## PR 管理

### PR 评论

```python
await self.api.github.create_pr_comment(
    repo="owner/repo",
    pr_number=10,
    body="CI 全部通过，LGTM! :white_check_mark:",
)
```

> GitHub REST API 中 PR 评论与 Issue 评论共用同一端点，`create_pr_comment()` 是 `create_issue_comment()` 的语义别名。

### 合并 PR

```python
from ncatbot.types.github import GitHubMergeMethod

result = await self.api.github.merge_pr(
    repo="owner/repo",
    pr_number=10,
    merge_method=GitHubMergeMethod.SQUASH,   # "merge" | "squash" | "rebase"
    commit_title="feat: add new feature (#10)",
    commit_message="Squashed commit from PR #10",
)
```

### 关闭 PR

```python
await self.api.github.close_pr("owner/repo", 10)
```

### 请求审查

```python
await self.api.github.request_review(
    repo="owner/repo",
    pr_number=10,
    reviewers=["reviewer1", "reviewer2"],
)
```

### 查询 PR

```python
pr = await self.api.github.get_pr("owner/repo", 10)
print(pr["title"], pr["state"], pr["merged"])
```

## 信息查询

### 查询仓库

```python
repo_info = await self.api.github.get_repo("owner/repo")
print(repo_info["full_name"], repo_info["description"])
```

### 查询用户

```python
user = await self.api.github.get_user("octocat")
print(user["login"], user["html_url"])
```

### 查询当前认证用户

```python
me = await self.api.github.get_authenticated_user()
print(me["login"])
```

## 实战：PR 自动审查流程

```python
from ncatbot.core import registrar
from ncatbot.event.github import GitHubPREvent
from ncatbot.plugin import NcatBotPlugin

class PRReviewPlugin(NcatBotPlugin):
    name = "pr_review"
    version = "1.0.0"

    @registrar.github.on_pr()
    async def on_pr(self, event: GitHubPREvent):
        if event.action != "opened":
            return
        # 自动请求审查
        await self.api.github.request_review(
            event.repo, event.pr_number, ["lead-reviewer"]
        )
        # 添加评论
        await event.reply(
            f"PR #{event.pr_number} 已提交。\n"
            f"分支: `{event.data.head_ref}` → `{event.data.base_ref}`\n"
            f"已自动请求 @lead-reviewer 审查。"
        )
```

---

> **返回**：[GitHub API 使用](README.md) · **相关**：[Issue 与评论 API](1_issue_comment.md) · [GitHub API 参考](../../../reference/api/github/1_api.md)
