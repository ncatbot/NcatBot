# Issue 与评论 API

> Issue 的创建、更新、关闭、标签管理、指派管理，以及 Issue 评论的增删改查。

---

## Issue 管理

### 创建 Issue

```python
result = await self.api.github.create_issue(
    repo="owner/repo",
    title="Bug: 启动失败",
    body="## 复现步骤\n\n1. 执行 `ncatbot run`\n2. 报错",
    labels=["bug", "high-priority"],
    assignees=["octocat"],
)
print(result["number"])  # 新 Issue 编号
```

### 更新 Issue

```python
await self.api.github.update_issue(
    repo="owner/repo",
    issue_number=42,
    title="[Updated] Bug: 启动失败",
    labels=["bug", "confirmed"],
)
```

### 关闭与重开

```python
await self.api.github.close_issue("owner/repo", 42)
await self.api.github.reopen_issue("owner/repo", 42)
```

### 查询 Issue

```python
issue = await self.api.github.get_issue("owner/repo", 42)
print(issue["title"], issue["state"])
```

## 标签管理

```python
# 添加标签
await self.api.github.add_labels("owner/repo", 42, ["enhancement", "v2.0"])

# 移除单个标签
await self.api.github.remove_label("owner/repo", 42, "enhancement")
```

## 指派管理

```python
await self.api.github.set_assignees("owner/repo", 42, ["user1", "user2"])
```

## 评论操作

### 创建评论

```python
result = await self.api.github.create_issue_comment(
    repo="owner/repo",
    issue_number=42,
    body="已确认，将在下个版本修复。",
)
print(result["id"])  # 评论 ID
```

### 更新评论

```python
await self.api.github.update_comment(
    repo="owner/repo",
    comment_id=123456,
    body="[更新] 已在 v1.3.0 修复。",
)
```

### 删除评论

```python
await self.api.github.delete_comment("owner/repo", 123456)
```

### 列出评论

```python
comments = await self.api.github.list_issue_comments(
    repo="owner/repo",
    issue_number=42,
    page=1,
    per_page=50,
)
for c in comments:
    print(f"#{c['id']} by {c['user']['login']}: {c['body'][:50]}")
```

## 实战：自动标签分类

```python
@registrar.github.on_issue()
async def auto_label(self, event: GitHubIssueEvent):
    if event.action != "opened":
        return
    title = event.issue_title.lower()
    labels = []
    if "bug" in title or "错误" in title:
        labels.append("bug")
    if "feature" in title or "功能" in title:
        labels.append("enhancement")
    if labels:
        await self.api.github.add_labels(event.repo, event.issue_number, labels)
```

---

> **返回**：[GitHub API 使用](README.md) · **相关**：[PR 与查询 API](2_pr_query.md)
