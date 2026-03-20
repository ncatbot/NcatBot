# Release Asset 更新

适用场景：推送模式完成后，若 commit 涉及 docs/examples/skills，更新最新 Release 中的 `user-reference.zip`。

## 步骤 1：判断是否需要更新

```powershell
$lastTag = git describe --tags --abbrev=0 2>$null
# docs 是 submodule，指针变更显示为 "docs"（无尾部斜杠）
git diff --name-only "$lastTag..HEAD" | Select-String "^(docs$|docs/|examples/|\.agents/skills/)"
```

有匹配 → 执行后续步骤；无匹配 → 流程结束。

## 步骤 2：获取版本号

```powershell
$latestTag = git describe --tags --abbrev=0
$ver = $latestTag -replace '^v', ''
```

## 步骤 3：打包用户参考资料

```powershell
git submodule update --init

$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

if (Test-Path dist) { Remove-Item dist -Recurse -Force }

$files = Get-ChildItem -Recurse examples, .agents\skills, docs -File |
    Where-Object { $_.FullName -notmatch '__pycache__' }

New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
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

## 步骤 4：替换 Release Asset

```powershell
gh release delete-asset "v$ver" "ncatbot5-$ver-user-reference.zip" --repo ncatbot/NcatBot --yes
gh release upload "v$ver" $zipPath --repo ncatbot/NcatBot
```

## 步骤 5：清理

```powershell
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
```
