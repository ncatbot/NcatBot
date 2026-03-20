---
name: release
description: "发布 NcatBot 新版本到 PyPI 和 GitHub Release，或仅编排 Commit 推送到 main。从工作区变更编排 commit 到最终发布的全链路流程。Use when: 发版、release、发布、changelog、版本号、pick commits、挑选提交、release notes、编排 commit、push、推送。"
license: MIT
---

# Release Skill

你是 NcatBot 发布助手，负责从工作区变更到版本发布的全链路流程。

## 模式判断

自动检查工作区变更 + 待推送 commits，判断是否涉及核心路径：

| 核心路径 | `ncatbot/` · `pyproject.toml` · `main.py` |
|---------|------------------------------------------|
| **发布模式** | 检测到重大变动时或用户明确要求发布时 |
| **推送模式** | 用户明确要求推送时 |


> docs 是 Git submodule，其指针变更在 `git diff` 中显示为 `docs`（无斜杠），不触发发布模式。

---

## 发布模式

> 主要方式：推送 `v*` tag → CI 自动完成 lint → test → build → PyPI → GitHub Release。

**流程：**

1. **同步远端** — `git pull --rebase origin main`
2. **Commit 编排** — 处理未提交变更（含 docs submodule）→ 参见 [commit-workflow.md](references/commit-workflow.md)
3. **审查历史 commits + 生成 Release Notes** — 确认哪些进 release notes，确定版本号 → 参见 [versioning.md](references/versioning.md)
4. **本地预检 + 分步推送 tag** — ruff + pytest → push branch + push tag → 参见 [ci-publish.md](references/ci-publish.md)
5. **（备用）本地人工发布** — CI 不可用时 → 参见 [local-publish.md](references/local-publish.md)

---

## 推送模式

**流程：**

1. **同步远端** — `git pull --rebase origin main`
2. **Commit 编排** — 同发布模式步骤 2 → 参见 [commit-workflow.md](references/commit-workflow.md)
3. **推送** — `git push origin main`
4. **（按需）更新 Release Asset** — 若 commit 涉及 docs/skills → 参见 [asset-update.md](references/asset-update.md)

---

## 前置条件

- Python 虚拟环境已激活：`.venv\Scripts\activate.ps1`
- GitHub CLI 已登录：`gh auth login --web`
- GitHub Secrets 已配置 `PYPI_TOKEN`（CI 使用）
- docs submodule 已初始化：`git submodule update --init`

## 关键约束

- **测试优先**：CI 中 pytest 全部通过才执行发布；本地预检同样不可跳过
- **先 commit 再定版本**：版本号取决于本次 commits 的变更类型
- **分步推送**：先推 branch，再推 tag，避免重复触发 CI
- **major 由人类决定**：AI 不主动提及、不建议 major 升版
- **docs 变更先进子仓库**：主仓库只提交 submodule 指针更新

## ASK 决策点

| 触发条件 | 询问内容 |
|---------|---------|
| 模式无法自动判断 | 发布 or 推送 |
| 未明确且无法自动推断版号 | 版本号策略 |
