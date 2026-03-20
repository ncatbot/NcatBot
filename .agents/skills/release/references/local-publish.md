# 本地人工发布（备用）

> **仅当 CI/CD 不可用时使用。** 正常情况下请使用 CI/CD 流程（[ci-publish.md](ci-publish.md)）。

## 额外前置条件

```bash
uv pip install build twine
# PyPI Token 已配置为环境变量 TWINE_PASSWORD（见 .vscode/settings.json）
```

## 阶段 1：构建

```bash
rm -rf dist
python -m build
```

产物：
- `dist/ncatbot5-{version}-py3-none-any.whl`
- `dist/ncatbot5-{version}.tar.gz`

## 阶段 2：发布到 PyPI

```bash
python -m twine upload dist/* -u __token__
```

## 阶段 3：打包用户参考资料

```bash
uv run python .agents/skills/release/scripts/pack_user_ref.py --version X.Y.Z
```

> 脚本源码：[scripts/pack_user_ref.py](../scripts/pack_user_ref.py)

## 阶段 4：创建 GitHub Release

```bash
VER="X.Y.Z"
gh release create "v$VER" \
    "dist/ncatbot5-$VER-user-reference.zip" \
    "dist/ncatbot5-$VER-py3-none-any.whl" \
    "dist/ncatbot5-$VER.tar.gz" \
    --title "v$VER" \
    --notes-file release-notes.md \
    --repo ncatbot/NcatBot
```

## 阶段 5：清理

```bash
rm -rf dist release-notes.md
```
