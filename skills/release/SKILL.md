---
name: release
description: 发布 NcatBot 新版本到 PyPI 和 GitHub Release。当用户需要构建、打包、发布新版本时触发此技能。
license: MIT
---

# 技能指令

你是 NcatBot 发布助手。帮助用户完成版本发布的完整流程：PyPI 发布、用户参考资料打包、GitHub Release 创建。

## 前置条件

- Python 虚拟环境已激活（`.venv\Scripts\activate.ps1`）
- 已安装 `build` 和 `twine`（`uv pip install build twine`）
- PyPI API Token 已配置为环境变量 `TWINE_PASSWORD`（见 `.vscode/settings.json`）
- GitHub CLI（`gh`）已登录（`gh auth login --web`）

## 发布流程总览

> 详细参考：[references/release-steps.md](references/release-steps.md)

### 1. 更新版本号

修改 `pyproject.toml` 中的 `version` 字段。

### 2. 构建发行包

```powershell
# 清理旧产物
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
# 构建 sdist + wheel
python -m build
```

### 3. 发布到 PyPI

```powershell
python -m twine upload dist/* -u __token__
```

`twine` 会自动读取 `TWINE_PASSWORD` 环境变量中的 API Token。

### 4. 打包用户参考资料

将 `examples/`、`skills/`、`docs/` 打包为 zip（排除 `__pycache__`）：

```powershell
$ver = "X.Y.Z"  # 替换为实际版本
$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

$files = Get-ChildItem -Recurse examples, skills, docs -File |
    Where-Object { $_.FullName -notmatch '__pycache__' }

if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
foreach ($f in $files) {
    $rel = $f.FullName.Replace((Get-Location).Path + '\', '')
    $dest = Join-Path $tempDir $rel
    $destDir = Split-Path $dest
    if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $f.FullName $dest
}
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath
Remove-Item $tempDir -Recurse -Force
```

### 5. 创建 GitHub Release

```powershell
$ver = "X.Y.Z"
gh release create "v$ver" `
    "dist/ncatbot5-$ver-user-reference.zip" `
    "dist/ncatbot5-$ver-py3-none-any.whl" `
    "dist/ncatbot5-$ver.tar.gz" `
    --title "v$ver" `
    --notes "NcatBot $ver 正式版发布" `
    --repo ncatbot/NcatBot
```

## 关键约束

- 发布前确认版本号已正确更新
- 构建前必须清理旧 `dist/` 目录
- 打包参考资料时排除 `__pycache__` 目录
- PyPI Token **不要**提交到版本控制（已在 `.gitignore` 或 `.vscode/settings.json` 本地配置中）
