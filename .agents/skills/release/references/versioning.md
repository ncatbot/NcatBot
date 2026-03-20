# 版本号与 Release Notes

## 1. 获取候选 Commits

```powershell
$lastTag = git describe --tags --abbrev=0 2>$null
if (!$lastTag) { $lastTag = (git rev-list --max-parents=0 HEAD) }
git log "$lastTag..HEAD" --oneline --no-merges
```

## 2. 分类展示

按 conventional-commits 类型分组：

| 类型前缀 | 分类 | Emoji | 默认纳入 |
|----------|------|-------|---------|
| `feat` | 新功能 | ✨ | ✅ |
| `fix` | 修复 | 🐛 | ✅ |
| `refactor` | 重构 | ♻️ | ✅ |
| `perf` | 性能优化 | ⚡ | ✅ |
| 含 `BREAKING CHANGE` 或 `!` | 破坏性变更 | 💥 | ✅ |
| `docs` | 文档 | 📝 | ❌ |
| `test` | 测试 | ✅ | ❌ |
| `chore` / `build` / `ci` | 构建/维护 | 🔧 | ❌ |

## 3. ASK — 确认纳入范围

用 `vscode_askQuestions` 让用户确认默认分类是否需要调整（排除某些 commit，或额外纳入默认跳过的类别）。

## 4. 版本号递增规则

格式：`X.Y.Z[.postN]`

| 条件 | 递增 | 示例 | 是否 ASK |
|------|------|------|---------|
| 仅 1 个 `fix`（紧急热修复） | **post** | 5.1.0 → 5.1.0.post1 | 自动 |
| 多个 `fix` 或小 `feat` | **patch** | 5.1.0 → 5.1.1 | 自动 |
| 大型 `feat` 或 `BREAKING CHANGE` | **minor** | 5.1.0 → 5.2.0 | 自动 |
| 无法归类（仅 refactor/docs 等） | — | — | **必须 ASK** |

优先级：自上向下，第一条匹配则停止。

**major 不在 AI 决策范围内**，由人类主动发起，AI 不主动提及或建议。

## 5. 更新 pyproject.toml

读取当前版本，计算新版本后直接修改 `pyproject.toml` 中的 `version` 字段。

## 6. 生成 Release Notes

写入 `release-notes.md`（CI 流程使用此文件生成 GitHub Release 说明）：

~~~markdown
## 💥 破坏性变更
- 描述 (hash)

## ✨ 新功能
- **scope**: 描述 (hash)

## 🐛 修复
- 描述 (hash)

## ♻️ 重构
- 描述 (hash)
~~~

格式规则：
- 移除 `type(scope):` 前缀，只保留描述
- scope 非空时加粗：`- **scope**: 描述 (hash)`
- 空类别不展示；破坏性变更始终排最前
- 使用中文描述，简洁明了，突出用户关心的变更点
