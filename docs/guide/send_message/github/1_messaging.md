# GitHub 消息发送详解

> GitHub 平台的三种消息类型：Issue Comment、PR Comment、PR Review Comment。
> 消息内容支持 GitHub Flavored Markdown。

---

## Issue 评论

### 通过事件回复

```python
from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent

@registrar.github.on_issue()
async def on_new_issue(self, event: GitHubIssueEvent):
    if event.action != "opened":
        return
    await event.reply(
        f"## 感谢反馈\n\n"
        f"Issue **#{event.issue_number}** 已收到。\n"
        f"- 标签: {', '.join(event.labels) or '无'}\n"
        f"- 仓库: {event.repo}"
    )
```

### 通过 API 主动评论

```python
await self.api.github.create_issue_comment(
    repo="owner/repo",
    issue_number=42,
    body="这个问题已在 v1.2.0 修复，请升级后验证。",
)
```

## PR 评论

```python
from ncatbot.event.github import GitHubPREvent

@registrar.github.on_pr()
async def on_pr(self, event: GitHubPREvent):
    if event.action == "opened":
        await event.reply(
            f"PR **#{event.pr_number}** 已收到。\n"
            f"分支: `{event.data.head_ref}` → `{event.data.base_ref}`"
        )
```

主动评论：

```python
await self.api.github.create_pr_comment(
    repo="owner/repo",
    pr_number=10,
    body="CI 通过，LGTM! :rocket:",
)
```

## 评论的编辑与删除

### 编辑评论

```python
await self.api.github.update_comment(
    repo="owner/repo",
    comment_id=123456,
    body="[已更新] 这个问题已修复。",
)
```

### 删除评论

```python
# 方式 1：通过事件
from ncatbot.event.github import GitHubIssueCommentEvent

@registrar.github.on_comment()
async def on_comment(self, event: GitHubIssueCommentEvent):
    if "spam" in event.comment_body.lower():
        await event.delete()  # 删除当前评论

# 方式 2：通过 API
await self.api.github.delete_comment(repo="owner/repo", comment_id=123456)
```

## 列出评论

```python
comments = await self.api.github.list_issue_comments(
    repo="owner/repo",
    issue_number=42,
    page=1,
    per_page=30,
)
for c in comments:
    print(c["body"])
```

## 实战示例：Issue 自动回复 Bot

```python
from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent, GitHubIssueCommentEvent
from ncatbot.plugin import NcatBotPlugin

class IssueBotPlugin(NcatBotPlugin):
    name = "issue_bot"
    version = "1.0.0"

    @registrar.github.on_issue()
    async def on_issue(self, event: GitHubIssueEvent):
        if event.action == "opened":
            await event.reply("感谢反馈！请确保已搜索过已有 Issue。")
        elif event.action == "closed":
            await event.reply("Issue 已关闭。如有后续问题请重新开启。")

    @registrar.github.on_comment()
    async def on_comment(self, event: GitHubIssueCommentEvent):
        if event.comment_body.strip().lower() == "/close":
            await self.api.github.close_issue(event.repo, event.issue_number)
            await event.reply("Issue 已通过命令关闭。")
```

---

> **返回**：[GitHub 消息发送](README.md) · **相关**：[GitHub API 使用](../../api_usage/github/README.md)
