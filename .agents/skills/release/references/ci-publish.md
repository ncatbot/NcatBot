# CI/CD 发布：本地预检 + 分步推送

## 本地预检（推送前必做）

在创建 tag 之前模拟 CI 的 lint + test，避免浪费 CI 资源。

运行预检脚本（自动修复 lint/format 并生成报告）：

```bash
uv run python .agents/skills/release/scripts/precheck.py
```

> 脚本源码：[scripts/precheck.py](../scripts/precheck.py)

全部 exit code 0 才能继续。若 lint/format 已自动修复，提交修复后重新运行；测试失败则修复代码或测试。

## 分步推送

**必须分步**，避免 branch push 和 tag push 同时触发重复 CI 运行：

```bash
VER="X.Y.Z"  # 替换为实际版本号

# 步骤 1：推送 commits 到 main
git push origin main

# 步骤 2：创建并推送 tag（触发完整 CI test + publish）
git tag "v$VER"
git push origin "v$VER"
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
