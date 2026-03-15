# 高级开发环境

> IDE 配置、调试技巧、CI/CD 本地模拟、NapCat 本地部署与常见问题排查。

---

## 目录

- [IDE 配置（VSCode）](#ide-配置vscode)
- [调试配置](#调试配置)
- [pre-commit 详解](#pre-commit-详解)
- [CI/CD 本地模拟](#cicd-本地模拟)
- [NapCat 本地部署](#napcat-本地部署)
- [常见问题排查](#常见问题排查)

---

## IDE 配置（VSCode）

### 推荐扩展

在 VSCode 中安装以下扩展以获得最佳开发体验：

| 扩展 | ID | 用途 |
|------|------|------|
| Python | `ms-python.python` | Python 语言支持 |
| Pylance | `ms-python.vscode-pylance` | 类型检查 + 智能补全 |
| Ruff | `charliermarsh.ruff` | Lint + 格式化 |
| Even Better TOML | `tamasfe.even-better-toml` | TOML 语法高亮 |

### 推荐 settings.json

在项目根目录创建 `.vscode/settings.json`（如尚不存在）：

```jsonc
{
    // Python 环境
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",

    // Ruff 作为默认格式化器
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    // Pylance 类型检查
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,

    // 文件关联
    "files.associations": {
        "*.toml": "toml"
    },

    // 行尾统一 LF
    "files.eol": "\n"
}
```

> **Linux/macOS 用户**：将 `python.defaultInterpreterPath` 改为 `${workspaceFolder}/.venv/bin/python`。

---

## 调试配置

在 `.vscode/launch.json` 中添加以下配置：

```jsonc
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "NcatBot: 运行 main.py",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "NcatBot: 运行当前文件",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "NcatBot: pytest 当前文件",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["${file}", "-v", "--no-cov"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "NcatBot: pytest 全部测试",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["-v", "--no-cov"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

**使用方式**：按 `F5` 或在"运行和调试"面板选择配置启动。调试 pytest 时使用 `--no-cov` 避免覆盖率插件干扰断点。

---

## pre-commit 详解

### 安装钩子

```bash
uv run pre-commit install
```

安装后每次 `git commit` 会自动运行以下检查：

| 来源 | 检查内容 |
|------|---------|
| **pre-commit-hooks** | 尾部空白、文件末尾换行、YAML/TOML 语法、AST 合法性、大文件检测、合并冲突标记、私钥泄露检测、debug 语句、行尾统一 LF |
| **ruff** | 代码 lint（自动修复）+ 格式化 |
| **codespell** | 拼写检查 |

### 常见场景

```bash
# 手动对所有文件运行（推荐首次安装后执行）
uv run pre-commit run --all-files

# 如果 pre-commit 自动修复了文件，需要重新暂存
git add .
git commit -m "your message"
```

> **提示**：pre-commit 自动修复文件后 `git commit` 会中断，请 `git add` 修复后的文件再重新提交。不推荐使用 `--no-verify` 跳过检查。

---

## CI/CD 本地模拟

### 使用 tox 多版本测试

tox 可在本地模拟 CI 的多 Python 版本测试矩阵：

```bash
# 运行所有版本（Python 3.12 + 3.13）
uv run tox

# 指定版本
uv run tox -e py312
uv run tox -e py313
```

tox 配置位于 `tox.ini`：

```ini
[tox]
envlist = py312, py313
requires = tox-uv

[testenv]
extras = dev
commands = pytest --no-cov {posargs}
uv_python_preference = managed
```

> tox 使用 `tox-uv` 插件集成 uv，会自动下载所需的 Python 版本。多版本测试不是提交 PR 的必要条件，CI 会自动处理。

### 模拟完整 CI 流程

在本地按以下顺序执行，可覆盖 CI 的所有检查项：

```bash
# 1. 代码检查
uv run ruff check .
uv run ruff format --check .
uv run codespell

# 2. 类型检查
uv run mypy ncatbot/

# 3. 单元测试
uv run pytest

# 4. 多版本测试（可选）
uv run tox
```

全部通过后即可放心提交 PR。

---

## NapCat 本地部署

NcatBot 依赖 [NapCat](https://github.com/NapNeko/NapCatQQ) 作为 OneBot v11 协议后端。项目根目录的 `napcat/` 包含预配置的 NapCat 文件。

### 启动 NapCat

```powershell
# Windows — 使用快速登录脚本
.\napcat\1550507358_quickLogin.bat

# 或使用通用启动脚本
.\napcat\launcher.bat
```

### 配置文件

NapCat 配置文件位于 `napcat/config/` 目录，关键配置项：

| 文件 | 说明 |
|------|------|
| `napcat/qqnt.json` | QQ 版本与协议配置 |
| `napcat/config/` | WebSocket / HTTP 连接配置 |

### 连接 NcatBot

确保 NapCat 与 NcatBot 的 WebSocket 端口一致（默认 `3001`），在项目的 `config.yaml` 中配置：

```yaml
ws_port: 3001
http_port: 3000
```

> 开发环境可使用 `dev/config.yaml` 覆盖默认配置。

---

## 常见问题排查

### `uv sync` 安装失败

- **检查 Python 版本**：`python --version` 确认 ≥ 3.12
- **检查 uv 版本**：`uv --version`，建议升级到最新：`uv self update`
- **网络问题**：配置镜像源

```bash
uv sync --extra dev --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### `import ncatbot` 报错 ModuleNotFoundError

- **未激活虚拟环境**：执行 `.venv\Scripts\activate.ps1`（Windows）或 `source .venv/bin/activate`（Linux/macOS）
- **依赖未安装**：执行 `uv sync --extra dev`
- **IDE 解释器未指向 `.venv`**：在 VSCode 中按 `Ctrl+Shift+P` → "Python: Select Interpreter" → 选择 `.venv` 中的 Python

### pre-commit 报错

- **首次运行慢**：pre-commit 需要下载钩子环境，属正常现象
- **自动修复后提交失败**：这是预期行为，`git add .` 后重新 `git commit`
- **清除缓存重装**：

```bash
uv run pre-commit clean
uv run pre-commit install
uv run pre-commit run --all-files
```

### pytest 找不到测试

- **确认在项目根目录执行**：`cd ncatbot` 项目根目录
- **确认虚拟环境已激活**
- **查看 pytest 配置**：`pyproject.toml` 中 `[tool.pytest.ini_options]` 的 `testpaths` 设置

### NapCat 连接失败

- **确认 NapCat 已启动**：检查 NapCat 终端是否有错误输出
- **端口冲突**：确认 `ws_port`（默认 3001）和 `http_port`（默认 3000）未被占用
- **防火墙**：确保本地防火墙未拦截 WebSocket 连接

### tox 下载 Python 失败

- **网络问题**：tox-uv 会自动下载 Python，确保网络畅通
- **跳过多版本测试**：多版本测试非必需，CI 会自动处理，本地只需 `uv run pytest` 即可
