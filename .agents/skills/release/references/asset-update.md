# Release Asset 更新

适用场景：推送模式完成后，若 commit 涉及 docs/examples/skills，更新最新 Release 中的 `user-reference.zip`。

## 步骤 1：判断是否需要更新

```bash
LAST_TAG=$(git describe --tags --abbrev=0)
# docs 是 submodule，指针变更显示为 "docs"（无尾部斜杠）
git diff --name-only "$LAST_TAG..HEAD" | grep -E '^(docs$|docs/|\.agents/skills/)'
```

有匹配 → 执行后续步骤；无匹配 → 流程结束。

## 步骤 2：打包用户参考资料

运行打包脚本（自动从 git tag 推导版本号）：

```bash
uv run python .agents/skills/release/scripts/pack_user_ref.py
# 或手动指定版本号
uv run python .agents/skills/release/scripts/pack_user_ref.py --version X.Y.Z
```

> 脚本源码：[scripts/pack_user_ref.py](../scripts/pack_user_ref.py)

## 步骤 3：替换 Release Asset

```bash
VER=$(git describe --tags --abbrev=0 | sed 's/^v//')
gh release delete-asset "v$VER" "ncatbot5-$VER-user-reference.zip" --repo ncatbot/NcatBot --yes
gh release upload "v$VER" "dist/ncatbot5-$VER-user-reference.zip" --repo ncatbot/NcatBot
```

## 步骤 4：清理

```bash
rm -rf dist
```
