# 发布步骤详解

## 完整发布清单

### 阶段 1：准备

1. 确认所有代码已合并到目标分支
2. 确认测试通过（`python -m pytest`）
3. 更新 `pyproject.toml` 中的 `version` 字段
   - 正式版：`"5.0.0"`
   - 预发布版：`"5.0.0rc1"`、`"5.0.0a1"`、`"5.0.0b1"`

### 阶段 2：构建

```powershell
# 激活虚拟环境
.venv\Scripts\activate.ps1

# 确保构建工具已安装
uv pip install build twine

# 清理旧产物
if (Test-Path dist) { Remove-Item dist -Recurse -Force }

# 构建
python -m build
```

构建产物：
- `dist/ncatbot5-{version}-py3-none-any.whl` — wheel 包
- `dist/ncatbot5-{version}.tar.gz` — 源码包

### 阶段 3：发布到 PyPI

```powershell
# 使用 API Token 上传（Token 通过 TWINE_PASSWORD 环境变量提供）
python -m twine upload dist/* -u __token__
```

验证发布：访问 https://pypi.org/project/ncatbot5/{version}/

### 阶段 4：打包用户参考资料

目标：将 `examples/`、`skills/`、`docs/` 打包为一个 zip 文件，供用户下载参考。

```powershell
$ver = "{version}"
$zipPath = "dist\ncatbot5-$ver-user-reference.zip"
$tempDir = "dist\_pack_temp"

# 收集文件（排除 __pycache__）
$files = Get-ChildItem -Recurse examples, skills, docs -File |
    Where-Object { $_.FullName -notmatch '__pycache__' }

# 复制到临时目录（保持目录结构）
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
foreach ($f in $files) {
    $rel = $f.FullName.Replace((Get-Location).Path + '\', '')
    $dest = Join-Path $tempDir $rel
    $destDir = Split-Path $dest
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item $f.FullName $dest
}

# 压缩
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath

# 清理临时目录
Remove-Item $tempDir -Recurse -Force
```

### 阶段 5：创建 GitHub Release

```powershell
$ver = "{version}"
gh release create "v$ver" `
    "dist/ncatbot5-$ver-user-reference.zip" `
    "dist/ncatbot5-$ver-py3-none-any.whl" `
    "dist/ncatbot5-$ver.tar.gz" `
    --title "v$ver" `
    --notes "NcatBot $ver 正式版发布" `
    --repo ncatbot/NcatBot
```

验证发布：访问 https://github.com/ncatbot/NcatBot/releases/tag/v{version}

## 环境变量配置

| 变量 | 用途 | 配置位置 |
|------|------|---------|
| `TWINE_PASSWORD` | PyPI API Token | `.vscode/settings.json` → `terminal.integrated.env.windows` |

## 常见问题

### `No module named build`

安装构建工具：`uv pip install build twine`

### `gh: To get started with GitHub CLI, please run: gh auth login`

运行 `gh auth login --web` 进行浏览器认证。

### twine 上传 403

检查 Token 是否过期，重新生成后更新 `.vscode/settings.json` 中的 `TWINE_PASSWORD`。

### 版本号冲突

PyPI 不允许覆盖已发布的版本。如果版本号已存在，需要递增版本号。
