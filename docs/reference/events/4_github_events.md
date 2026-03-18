# GitHub 事件实体

> GitHub 平台 8 个事件实体类的完整参考 — 属性、方法、Trait、工厂映射。

---

## Issue 事件

### GitHubIssueEvent

**Traits：** `HasSender`, `Replyable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `issue_number` | int | Issue 编号 |
| `issue_title` | str | Issue 标题 |
| `action` | str | 动作（opened / edited / closed / reopened / labeled 等） |
| `labels` | list | 标签列表 |
| `repo` | str | 仓库全名（`"owner/repo"`） |
| `user_id` | str | 操作者 ID |
| `sender` | GitHubSender | 操作者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async reply(text: str) -> Any` | 在该 Issue 下创建评论 |

```python
@registrar.github.on_issue()
async def on_issue(self, event: GitHubIssueEvent):
    if event.action == "opened":
        await event.reply(f"Issue #{event.issue_number} 已收到。")
```

### GitHubIssueCommentEvent

**Traits：** `HasSender`, `Replyable`, `Deletable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `comment_body` | str | 评论内容 |
| `issue_number` | int | 所属 Issue/PR 编号 |
| `repo` | str | 仓库全名 |
| `user_id` | str | 评论者 ID |
| `sender` | GitHubSender | 评论者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async reply(text: str) -> Any` | 在同一 Issue 下回复 |
| `delete()` | `async delete() -> Any` | 删除该评论 |

---

## PR 事件

### GitHubPREvent

**Traits：** `HasSender`, `Replyable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `pr_number` | int | PR 编号 |
| `pr_title` | str | PR 标题 |
| `action` | str | 动作（opened / closed / synchronize / merged 等） |
| `merged` | bool | 是否已合并 |
| `repo` | str | 仓库全名 |
| `user_id` | str | 操作者 ID |
| `sender` | GitHubSender | 操作者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async reply(text: str) -> Any` | 在该 PR 下创建评论 |

```python
@registrar.github.on_pr()
async def on_pr(self, event: GitHubPREvent):
    if event.action == "opened" and not event.merged:
        await event.reply("PR 已提交，等待 review。")
```

### GitHubPRReviewCommentEvent

**Traits：** `HasSender`, `Replyable`, `Deletable`

| 属性 | 类型 | 说明 |
|------|------|------|
| `comment_body` | str | Review 评论内容 |
| `pr_number` | int | 所属 PR 编号 |
| `path` | str | 评论所在文件路径 |
| `repo` | str | 仓库全名 |
| `user_id` | str | 评论者 ID |
| `sender` | GitHubSender | 评论者信息 |

| 方法 | 签名 | 说明 |
|------|------|------|
| `reply()` | `async reply(text: str) -> Any` | 在同一 PR 下回复 |
| `delete()` | `async delete() -> Any` | 删除该评论 |

---

## Push 事件

### GitHubPushEvent

**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `ref` | str | 分支引用（如 `"refs/heads/main"`） |
| `before` | str | Push 前 SHA |
| `after` | str | Push 后 SHA |
| `commits` | List[GitHubCommit] | 提交列表 |
| `head_commit` | GitHubCommit \| None | 最新提交 |
| `repo` | str | 仓库全名 |
| `user_id` | str | 推送者 ID |
| `sender` | GitHubSender | 推送者信息 |

```python
@registrar.github.on_push()
async def on_push(self, event: GitHubPushEvent):
    for commit in event.commits:
        print(f"{commit.sha[:7]} {commit.message}")
```

---

## 其他事件

### GitHubStarEvent

**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `repo` | str | 仓库全名 |
| `starred_at` | str | Star 时间 |
| `user_id` | str | Star 用户 ID |
| `sender` | GitHubSender | Star 用户信息 |

### GitHubForkEvent

**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `repo` | str | 原仓库全名 |
| `forkee` | GitHubForkee | Fork 目标仓库信息 |
| `forkee_full_name` | str | Fork 后的仓库全名 |
| `user_id` | str | Fork 用户 ID |
| `sender` | GitHubSender | Fork 用户信息 |

### GitHubReleaseEvent

**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `repo` | str | 仓库全名 |
| `release` | GitHubRelease | Release 详情 |
| `release_tag` | str | Tag 名称 |
| `release_name` | str | Release 名称 |
| `release_body` | str | Release 说明 |
| `prerelease` | bool | 是否预发布 |
| `user_id` | str | 发布者 ID |
| `sender` | GitHubSender | 发布者信息 |

```python
@registrar.github.on_release()
async def on_release(self, event: GitHubReleaseEvent):
    if event.data.action == "published" and not event.prerelease:
        print(f"正式版发布: {event.release_tag}")
```

---

## 继承关系

```text
BaseEvent
├── GitHubIssueEvent         (HasSender, Replyable)
├── GitHubIssueCommentEvent  (HasSender, Replyable, Deletable)
├── GitHubPREvent            (HasSender, Replyable)
├── GitHubPRReviewCommentEvent (HasSender, Replyable, Deletable)
├── GitHubPushEvent          (HasSender)
├── GitHubStarEvent          (HasSender)
├── GitHubForkEvent          (HasSender)
└── GitHubReleaseEvent       (HasSender)
```

## 工厂映射

| 数据模型 | 事件实体 | post_type |
|----------|---------|-----------|
| `GitHubIssueEventData` | `GitHubIssueEvent` | `"issue"` |
| `GitHubIssueCommentEventData` | `GitHubIssueCommentEvent` | `"comment"` |
| `GitHubPREventData` | `GitHubPREvent` | `"pull_request"` |
| `GitHubPRReviewCommentEventData` | `GitHubPRReviewCommentEvent` | `"comment"` |
| `GitHubPushEventData` | `GitHubPushEvent` | `"push"` |
| `GitHubStarEventData` | `GitHubStarEvent` | `"star"` |
| `GitHubForkEventData` | `GitHubForkEvent` | `"fork"` |
| `GitHubReleaseEventData` | `GitHubReleaseEvent` | `"release"` |

---

> **返回**：[事件参考首页](README.md) · **相关**：[GitHub API 参考](../api/github/1_api.md) · [GitHub 类型](../types/6_github_types.md)

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 操作者 |
| `repo` | `str` | 仓库全名 |
| `starred_at` | `str` | Star 时间 |

### GitHubForkEvent

Fork 事件。**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | Fork 者 |
| `repo` | `str` | 源仓库全名 |
| `forkee` | `GitHubForkee` | Fork 出的仓库对象 |
| `forkee_full_name` | `str` | Fork 仓库全名 |

### GitHubReleaseEvent

Release 发布事件。**Traits：** `HasSender`

| 属性 | 类型 | 说明 |
|------|------|------|
| `user_id` | `str` | 发布者 |
| `repo` | `str` | 仓库全名 |
| `release` | `GitHubRelease` | Release 对象 |
| `release_tag` | `str` | Tag 名称 |
| `release_name` | `str` | Release 名称 |
| `release_body` | `str` | Release 说明 |

---

## 注册器速查

| 装饰器 | 事件类型 |
|--------|---------|
| `@registrar.github.on_issue()` | `issue` |
| `@registrar.github.on_pr()` | `pull_request` |
| `@registrar.github.on_push()` | `push` |
| `@registrar.github.on_star()` | `star` |
| `@registrar.github.on_fork()` | `fork` |
| `@registrar.github.on_release()` | `release` |
| `@registrar.github.on_comment()` | `comment` |
