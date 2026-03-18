# GitHub 消息发送

> GitHub 平台的消息发送方式 — Issue 评论、PR 评论与 API 直接调用。
> GitHub 平台消息以纯文本 / Markdown 为主，不支持富媒体消息段（At、Image 等）。

---

## Quick Start

### 通过事件回复

```python
from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent, GitHubPREvent

@registrar.github.on_issue()
async def on_issue(self, event: GitHubIssueEvent):
    await event.reply("感谢你的反馈！")                   # Issue 评论

@registrar.github.on_pr()
async def on_pr(self, event: GitHubPREvent):
    await event.reply("PR 已收到，正在 review。")          # PR 评论
```

### 通过 API 直接调用

```python
# Issue 评论
await self.api.github.create_issue_comment("owner/repo", issue_number=42, body="已处理")

# PR 评论
await self.api.github.create_pr_comment("owner/repo", pr_number=10, body="LGTM!")
```

---

## Quick Reference

| 方式 | 调用 | 适用场景 |
|------|------|---------|
| `event.reply(text)` | `await event.reply("内容")` | 事件 handler 内回复（Issue / PR / Comment） |
| `create_issue_comment()` | `await api.github.create_issue_comment(repo, issue_number, body)` | 主动评论 Issue |
| `create_pr_comment()` | `await api.github.create_pr_comment(repo, pr_number, body)` | 主动评论 PR |
| `update_comment()` | `await api.github.update_comment(repo, comment_id, body)` | 编辑已有评论 |
| `delete_comment()` | `await api.github.delete_comment(repo, comment_id)` | 删除评论 |
| `event.delete()` | `await event.delete()` | 删除当前评论（评论事件） |

### 与其他平台的差异

| 特性 | QQ | Bilibili | GitHub |
|------|-----|----------|--------|
| 消息格式 | 富文本（消息段） | 纯文本 | 纯文本 / Markdown |
| At / 图片 / 视频 | ✅ | 部分 | ❌ |
| `event.reply()` | ✅ | ✅ | ✅ |
| `event.delete()` | ✅ | ✅ | ✅（仅评论事件） |
| MessageArray | ✅ | — | — |

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [1_messaging.md](1_messaging.md) | Issue / PR / Review Comment 发送详解与示例 |

---

> **相关**：[GitHub API 使用](../../api_usage/github/README.md) · [跨平台通用消息段](../common/README.md) · [多平台开发](../../multi_platform/README.md)
