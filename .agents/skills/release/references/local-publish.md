# 本地人工发布（备用）

> **仅当 CI/CD 不可用时使用。** 正常情况下请使用 CI/CD 流程（[ci-publish.md](ci-publish.md)）。

## 额外前置条件

```powershell
uv pip install build twine
# PyPI Token 已配置为环境变量 TWINE_PASSWORD（见 .vscode/settings.json）
```

## 阶段 1：构建

```powershell
. .venv\Scripts\activate.ps1
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
python -m build
```

产物：
- `dist/ncatbot5-{version}-py3-none-any.whl`
- `dist/ncatbot5-{version}.tar.gz`

## 阶段 2：发布到 PyPI

```powershell
python -m twine upload dist/* -u __token__
```

## 阶段 3：打包用户参考资料

```powershell
git submodule update --init  # 确保 docs 内容已拉取

$ver = "X.Y.Z"
$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

$files = Get-ChildItem -Recurse examples, .agents\skills, docs -File |
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

## 阶段 4：创建 GitHub Release

```powershell
gh release create "v$ver" `
    "dist/ncatbot5-$ver-user-reference.zip" `
    "dist/ncatbot5-$ver-py3-none-any.whl" `
    "dist/ncatbot5-$ver.tar.gz" `
    --title "v$ver" `
    --notes-file release-notes.md `
    --repo ncatbot/NcatBot
```

## 阶段 5：清理

```powershell
Remove-Item dist -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item release-notes.md -ErrorAction SilentlyContinue
```
