# GitHub API 参考

> GitHubBotAPI 完整方法签名与参数说明。

---

## Quick Reference

```python
bot.api.github.create_issue(owner="o", repo="r", title="Bug")
bot.api.github.create_issue_comment(owner="o", repo="r", issue_number=1, body="Fixed")
bot.api.github.merge_pr(owner="o", repo="r", pull_number=42)
bot.api.github.get_repo(owner="o", repo="r")
```

## 本目录索引

| 文件 | 说明 |
|------|------|
| [GitHub API 方法](1_api.md) | Issue / Comment / PR / Query 四大 Mixin 共 20 个方法的完整签名 |

> 用法示例请查阅 [guide/api_usage/github/](../../../guide/api_usage/github/)。
