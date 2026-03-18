# GitHub API 参考

> `GitHubBotAPI` 完整方法签名 — Issue、Comment、PR、Query 四个 Mixin 共 20 个方法。

---

## API 架构

```text
api.github : GitHubBotAPI
├── IssueAPIMixin       ← Issue 增删改查 + 标签 + 指派
├── CommentAPIMixin     ← 评论增删改查
├── PRAPIMixin          ← PR 评论 / 合并 / 关闭 / 审查
└── QueryAPIMixin       ← 仓库 / 用户查询
```

---

## Issue 操作（IssueAPIMixin）

### create_issue()

```python
async def create_issue(
    repo: str,
    title: str,
    body: str = "",
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
) -> dict
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| repo | str | — | 仓库全名，如 `"owner/repo"` |
| title | str | — | Issue 标题 |
| body | str | `""` | Issue 内容（支持 Markdown） |
| labels | List[str] \| None | None | 标签列表 |
| assignees | List[str] \| None | None | 指派人列表 |

### update_issue()

```python
async def update_issue(
    repo: str,
    issue_number: int,
    *,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
) -> dict
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| repo | str | — | 仓库全名 |
| issue_number | int | — | Issue 编号 |
| title | str \| None | None | 新标题 |
| body | str \| None | None | 新内容 |
| state | str \| None | None | `"open"` 或 `"closed"` |
| labels | List[str] \| None | None | 替换标签 |
| assignees | List[str] \| None | None | 替换指派人 |

### close_issue()

```python
async def close_issue(repo: str, issue_number: int) -> dict
```

### reopen_issue()

```python
async def reopen_issue(repo: str, issue_number: int) -> dict
```

### get_issue()

```python
async def get_issue(repo: str, issue_number: int) -> dict
```

### add_labels()

```python
async def add_labels(repo: str, issue_number: int, labels: List[str]) -> list
```

### remove_label()

```python
async def remove_label(repo: str, issue_number: int, label: str) -> None
```

### set_assignees()

```python
async def set_assignees(repo: str, issue_number: int, assignees: List[str]) -> dict
```

---

## 评论操作（CommentAPIMixin）

### create_issue_comment()

```python
async def create_issue_comment(repo: str, issue_number: int, body: str) -> dict
```

| 参数 | 类型 | 说明 |
|------|------|------|
| repo | str | 仓库全名 |
| issue_number | int | Issue 或 PR 编号 |
| body | str | 评论内容（支持 Markdown） |

### update_comment()

```python
async def update_comment(repo: str, comment_id: int, body: str) -> dict
```

### delete_comment()

```python
async def delete_comment(repo: str, comment_id: int) -> None
```

### list_issue_comments()

```python
async def list_issue_comments(
    repo: str, issue_number: int, page: int = 1, per_page: int = 30
) -> list
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| per_page | int | 30 | 每页数量 |

---

## PR 操作（PRAPIMixin）

### create_pr_comment()

```python
async def create_pr_comment(repo: str, pr_number: int, body: str) -> dict
```

> PR 评论与 Issue 评论共用 GitHub REST 端点。

### merge_pr()

```python
async def merge_pr(
    repo: str,
    pr_number: int,
    *,
    merge_method: Union[GitHubMergeMethod, str] = GitHubMergeMethod.MERGE,
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None,
) -> dict
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| merge_method | GitHubMergeMethod \| str | `"merge"` | `"merge"` / `"squash"` / `"rebase"` |
| commit_title | str \| None | None | 合并提交标题 |
| commit_message | str \| None | None | 合并提交消息 |

### close_pr()

```python
async def close_pr(repo: str, pr_number: int) -> dict
```

### request_review()

```python
async def request_review(repo: str, pr_number: int, reviewers: List[str]) -> dict
```

### get_pr()

```python
async def get_pr(repo: str, pr_number: int) -> dict
```

---

## 查询操作（QueryAPIMixin）

### get_repo()

```python
async def get_repo(repo: str) -> dict
```

### get_user()

```python
async def get_user(username: str) -> dict
```

### get_authenticated_user()

```python
async def get_authenticated_user() -> dict
```

---

> **返回**：[API 参考首页](../README.md) · **相关**：[GitHub API 使用指南](../../../guide/api_usage/github/README.md) · [GitHub 事件](../../events/4_github_events.md)
