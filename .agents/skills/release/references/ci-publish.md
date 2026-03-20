# CI/CD 发布：本地预检 + 分步推送

## 本地预检（推送前必做）

在创建 tag 之前模拟 CI 的 lint + test，避免浪费 CI 资源：

```powershell
. .venv\Scripts\activate.ps1

# Ruff lint
uv run ruff check .

# Ruff 格式
uv run ruff format --check .

# 测试（无覆盖率，与 CI 一致）
uv run pytest --no-cov
```

全部 exit code 0 才能继续。若失败：
- lint/format 问题：`uv run ruff check --fix .` + `uv run ruff format .`，修复后提交
- 测试失败：修复代码或测试，重新运行预检

## 分步推送

**必须分步**，避免 branch push 和 tag push 同时触发重复 CI 运行：

```powershell
$ver = "X.Y.Z"  # 替换为实际版本号

# 步骤 1：推送 commits 到 main
git push origin main

# 步骤 2：创建并推送 tag（触发完整 CI test + publish）
git tag "v$ver"
git push origin "v$ver"
```

> `ci.yml` 使用 `concurrency: group: ci-${{ github.sha }}` + `cancel-in-progress: true`。
> tag push 到达时会自动取消步骤 1 触发的仅测试运行，最终只执行一次完整流程。

## CI 自动执行流程

1. **Lint** — ruff check + format check
2. **Test** — Python 3.12 / 3.13 双版本 pytest（不通过则中止发布）
3. **Build** — `uv build` 生成 whl 和 tar.gz
4. **Verify** — `twine check dist/*`
5. **Publish to PyPI** — 使用 `PYPI_TOKEN` secret
6. **Package user-reference** — 打包 examples / docs / skills 为 zip
7. **Create GitHub Release** — 附带 whl、tar.gz、user-reference.zip

## 验证发布结果

```powershell
gh run list --workflow=ci.yml --limit=1
gh release view "v$ver" --repo ncatbot/NcatBot
```

若 CI 失败，查看 Actions 日志排查。必要时回退到 [local-publish.md](local-publish.md)。
