# Commit 编排工作流

适用场景：发布模式和推送模式开始前，将工作区未提交变更整理为规范 commits。

> 工作区干净（`git status` 无输出）时，跳过本文档全部步骤。

## 步骤 1：检查工作区状态

```powershell
git status --short
git diff --stat
```

## 步骤 1.5：docs 子模块处理

```powershell
git -C docs status --short
```

**若 docs 有变更**（输出非空）：

```powershell
# 在 docs 子仓库中提交推送
cd docs
git add .
git commit -m "docs: 变更描述"
git push origin master
cd ..

# 在主仓库暂存 submodule 指针（后续与其他 commit 合并）
git add docs
```

> docs 指针更新可合并到其他 commit 中，不需单独一个 commit。

## 步骤 2：ASK — 确认纳入范围

使用 `vscode_askQuestions` 展示变更文件列表，让用户确认：

- 哪些文件/改动纳入本次提交
- 哪些暂不提交（留到下次）

## 步骤 3：ASK — 确认 Commit 分组方案

按模块/功能建议分组，使用 `vscode_askQuestions` 确认：

- 遵循 conventional-commits 格式：`type(scope): description`
- 标题和描述写中文，约定式前缀、常用术语保持英文（如 `fix: 修复 xxx 导致的 yyy Bug`）
- 用户可合并、拆分、调整分组

示例建议：

```
分组 1: fix(adapter): 修复 WebSocket 连接中断问题
  - ncatbot/adapter/ws.py
  - ncatbot/adapter/connection.py

分组 2: feat(plugin): 新增热重载支持
  - ncatbot/plugin/loader.py
  - ncatbot/plugin/watcher.py
```

## 步骤 4：执行 Commit

```powershell
git add <files>
git commit -m "type(scope): description"
# 重复直到所有选中变更已提交
```
