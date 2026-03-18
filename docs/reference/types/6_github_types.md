# GitHub 平台类型

> GitHub 平台数据模型、枚举、Sender 与事件数据类。

---

## 导入

```python
from ncatbot.types.github import (
    # 枚举
    GitHubPostType, GitHubAction, GitHubIssueState, GitHubPRState,
    GitHubUserType, GitHubMergeMethod,
    # 数据模型
    GitHubRepo, GitHubCommit, GitHubRelease, GitHubForkee,
    # Sender
    GitHubSender,
    # 事件数据
    GitHubEventData, GitHubIssueEventData, GitHubIssueCommentEventData,
    GitHubPREventData, GitHubPRReviewCommentEventData, GitHubPushEventData,
    GitHubStarEventData, GitHubForkEventData, GitHubReleaseEventData,
)
```

---

## 枚举

### GitHubPostType

| 值 | 说明 |
|----|------|
| `ISSUE = "issue"` | Issue 事件 |
| `PULL_REQUEST = "pull_request"` | PR 事件 |
| `COMMENT = "comment"` | 评论事件 |
| `PUSH = "push"` | Push 事件 |
| `STAR = "star"` | Star 事件 |
| `FORK = "fork"` | Fork 事件 |
| `RELEASE = "release"` | Release 事件 |

### GitHubAction

| 值 | 说明 |
|----|------|
| `OPENED = "opened"` | Issue/PR 创建 |
| `EDITED = "edited"` | Issue/PR 编辑 |
| `CLOSED = "closed"` | Issue/PR 关闭 |
| `REOPENED = "reopened"` | Issue/PR 重开 |
| `CREATED = "created"` | 通用创建 |
| `DELETED = "deleted"` | 通用删除 |
| `SUBMITTED = "submitted"` | Review 提交 |
| `DISMISSED = "dismissed"` | Review 驳回 |
| `PUBLISHED = "published"` | Release 发布 |
| `SYNCHRONIZE = "synchronize"` | PR 同步更新 |
| `MERGED = "merged"` | PR 合并 |
| `LABELED = "labeled"` | 添加标签 |
| `UNLABELED = "unlabeled"` | 移除标签 |
| `ASSIGNED = "assigned"` | 指派 |
| `UNASSIGNED = "unassigned"` | 取消指派 |
| `REVIEW_REQUESTED = "review_requested"` | 请求审查 |
| `REVIEW_REQUEST_REMOVED = "review_request_removed"` | 取消审查请求 |
| `STARTED = "started"` | Star 开始 |

### GitHubIssueState

| 值 | 说明 |
|----|------|
| `OPEN = "open"` | 打开 |
| `CLOSED = "closed"` | 关闭 |

### GitHubPRState

| 值 | 说明 |
|----|------|
| `OPEN = "open"` | 打开 |
| `CLOSED = "closed"` | 关闭 |

### GitHubUserType

| 值 | 说明 |
|----|------|
| `USER = "User"` | 普通用户 |
| `BOT = "Bot"` | 机器人 |
| `ORGANIZATION = "Organization"` | 组织 |

### GitHubMergeMethod

| 值 | 说明 |
|----|------|
| `MERGE = "merge"` | 普通合并 |
| `SQUASH = "squash"` | 压缩合并 |
| `REBASE = "rebase"` | 变基合并 |

---

## 数据模型

### GitHubRepo

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `owner` | str | `""` | 仓库所有者 |
| `name` | str | `""` | 仓库名 |
| `full_name` | str | `""` | 全名（`"owner/name"`） |
| `id` | str | `""` | 仓库 ID |
| `html_url` | str \| None | None | 网页 URL |
| `description` | str \| None | None | 仓库描述 |
| `private` | bool | False | 是否私有 |
| `default_branch` | str \| None | None | 默认分支 |

### GitHubCommit

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sha` | str | `""` | Commit SHA |
| `message` | str | `""` | 提交消息 |
| `author_name` | str | `""` | 作者名 |
| `author_email` | str | `""` | 作者邮箱 |
| `url` | str \| None | None | Commit URL |
| `timestamp` | str \| None | None | 时间戳 |
| `added` | List[str] | `[]` | 新增文件 |
| `removed` | List[str] | `[]` | 删除文件 |
| `modified` | List[str] | `[]` | 修改文件 |

### GitHubRelease

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `id` | str | `""` | Release ID |
| `tag_name` | str | `""` | Tag 名称 |
| `name` | str | `""` | Release 名称 |
| `body` | str | `""` | 发布说明 |
| `prerelease` | bool | False | 是否预发布 |
| `draft` | bool | False | 是否草稿 |
| `html_url` | str \| None | None | 网页 URL |

### GitHubForkee

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `full_name` | str | `""` | Fork 后仓库全名 |
| `html_url` | str \| None | None | 网页 URL |
| `owner` | str | `""` | Fork 所有者 |
| `description` | str \| None | None | 描述 |

---

## Sender

### GitHubSender

继承自 `BaseSender`。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | str | `""` | 数字 ID（继承） |
| `nickname` | str | `""` | 昵称（继承） |
| `login` | str | `""` | GitHub 登录名 |
| `avatar_url` | str \| None | None | 头像 URL |
| `html_url` | str \| None | None | 个人主页 |
| `user_type` | GitHubUserType | `USER` | 用户类型 |

---

## 事件数据模型

所有事件数据类继承自 `GitHubEventData`（`BaseEventData` 子类）。

### GitHubEventData（基类）

| 字段 | 类型 | 说明 |
|------|------|------|
| `platform` | str | 固定 `"github"` |
| `action` | GitHubAction | Webhook action 字段 |
| `repo` | GitHubRepo | 仓库信息 |
| `sender` | GitHubSender | 操作者信息 |

### 事件数据类速查

| 数据类 | post_type | 核心字段 |
|--------|-----------|---------|
| `GitHubIssueEventData` | `"issue"` | `issue_number`, `issue_title`, `issue_body`, `issue_state`, `labels`, `assignees` |
| `GitHubIssueCommentEventData` | `"comment"` | `comment_id`, `comment_body`, `issue_number`, `issue_title` |
| `GitHubPREventData` | `"pull_request"` | `pr_number`, `pr_title`, `pr_body`, `pr_state`, `head_ref`, `base_ref`, `merged`, `draft` |
| `GitHubPRReviewCommentEventData` | `"comment"` | `comment_id`, `comment_body`, `pr_number`, `diff_hunk`, `path` |
| `GitHubPushEventData` | `"push"` | `ref`, `before`, `after`, `commits`, `head_commit`, `pusher_name` |
| `GitHubStarEventData` | `"star"` | `starred_at` |
| `GitHubForkEventData` | `"fork"` | `forkee` (GitHubForkee) |
| `GitHubReleaseEventData` | `"release"` | `release` (GitHubRelease) |

---

> **返回**：[类型参考首页](README.md) · **相关**：[GitHub 事件实体](../events/4_github_events.md) · [GitHub API](../api/github/1_api.md)
