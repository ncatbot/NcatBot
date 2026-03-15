# 装饰器与杂项工具

> 安全工具、进度条、GitHub 代理配置与环境变量参考

**源码位置**：`ncatbot/utils/config/security.py`、`ncatbot/utils/logger/tqdm.py`、`ncatbot/utils/network.py`

---

## 目录

- [1. 安全工具](#1-安全工具)
- [2. tqdm 进度条](#2-tqdm-进度条)
- [3. GitHub 代理详解](#3-github-代理详解)
- [4. 配置 YAML 完整示例](#4-配置-yaml-完整示例)
- [5. 环境变量汇总](#5-环境变量汇总)

---

## 1. 安全工具

源码位置：`ncatbot/utils/config/security.py`

```python
from ncatbot.utils.config.security import strong_password_check, generate_strong_token
```

### strong_password_check

检查密码是否满足强度策略。

```python
def strong_password_check(password: str) -> bool
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `password` | `str` | 待检查的密码 |

**强度策略**：

- 长度 ≥ 12
- 包含数字
- 包含大写字母
- 包含小写字母
- 包含特殊符号

**允许的特殊字符**：`-_.~!()*`（URI 安全字符集）

```python
strong_password_check("abc")           # False — 太短
strong_password_check("Abcdef123456")  # False — 无特殊符号
strong_password_check("Abcdef1234_!")  # True
```

### generate_strong_token

生成满足强度策略的随机 token。

```python
def generate_strong_token(length: int = 16) -> str
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `length` | `int` | `16` | token 长度 |

```python
token = generate_strong_token()     # 16 位随机 token
token = generate_strong_token(32)   # 32 位随机 token
assert strong_password_check(token) # 始终满足强度策略
```

### 安全自动修复

`ConfigManager.get_security_issues(auto_fix=True)` 会自动检测以下问题并修复：

| 检查项 | 修复方式 |
|--------|----------|
| `ws_token` 不满足强度策略 | 自动调用 `generate_strong_token()` 替换 |
| `webui_token` 不满足强度策略 | 自动调用 `generate_strong_token()` 替换 |

修复后会自动调用 `cm.save()` 持久化。

---

## 2. tqdm 进度条

自定义 `tqdm` 包装，集成 NcatBot 配色方案。

源码位置：`ncatbot/utils/logger/tqdm.py`

```python
from ncatbot.utils.logger.tqdm import tqdm

for item in tqdm(range(100), desc="处理中", colour="CYAN"):
    process(item)
```

### 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `colour` | `"GREEN"` | 进度条颜色 |
| `bar_format` | 内置模板 | 自定义格式，包含百分比、计数、耗时 |
| `ncols` | `80` | 终端宽度 |

### 可用颜色

`BLACK`、`RED`、`GREEN`、`YELLOW`、`BLUE`、`MAGENTA`、`CYAN`、`WHITE`

### 与 download_file 集成

`download_file` 内部使用此 tqdm 包装显示下载进度：

```python
from ncatbot.utils.network import download_file

download_file("https://example.com/large.zip", "large.zip")
# 处理中:  45%|████████████                | 45/100 [00:03<00:04, 12.50it/s]
```

---

## 3. GitHub 代理详解

源码位置：`ncatbot/utils/network.py`

用于在国内网络环境下加速 GitHub 资源访问。

```python
from ncatbot.utils.network import get_proxy_url, gen_url_with_proxy
```

### get_proxy_url

探测并返回可用 GitHub 代理 URL，结果缓存（后续调用直接返回缓存值）。

```python
def get_proxy_url() -> str
```

返回空字符串表示直连。

### gen_url_with_proxy

为 GitHub URL 添加代理前缀。

```python
def gen_url_with_proxy(original_url: str) -> str
```

```python
url = gen_url_with_proxy("https://github.com/user/repo/releases/latest")
# 可能返回: "https://proxy.example.com/https://github.com/user/repo/releases/latest"
# 或直连: "https://github.com/user/repo/releases/latest"
```

### 代理配置优先级

1. **配置文件** — `Config.github_proxy` 字段（最高优先）
2. **环境变量** — `GITHUB_PROXY`
3. **自动探测** — `get_proxy_url()` 逐一测试内置代理列表

### 建议

- 开发环境直接设置环境变量 `GITHUB_PROXY`，避免自动探测延迟
- 生产环境在 `config.yaml` 的 `github_proxy` 字段指定固定代理

---

## 4. 配置 YAML 完整示例

```yaml
# 基础配置
bot_uin: "1234567890"
root: "9876543210"
debug: false
websocket_timeout: 15
enable_webui_interaction: true
check_ncatbot_update: true
skip_ncatbot_install_check: false

# GitHub 代理（留空或删除此行使用自动探测）
github_proxy: "https://proxy.example.com"

# NapCat 连接配置
napcat:
  ws_uri: "ws://localhost:3001"
  ws_token: "your_strong_token_here"
  ws_listen_ip: "localhost"
  webui_uri: "http://localhost:6099"
  webui_token: "your_webui_token_here"
  enable_webui: true
  enable_update_check: false
  stop_napcat: false
  skip_setup: false

# 插件配置
plugin:
  plugins_dir: "plugins"
  load_plugin: true
  plugin_whitelist: []           # 空=不过滤
  plugin_blacklist: []
  auto_install_pip_deps: true
  plugin_configs:
    my_plugin:
      key: value
```

---

## 5. 环境变量汇总

| 环境变量 | 作用 | 默认值 | 使用方 |
|----------|------|--------|--------|
| `NCATBOT_CONFIG_PATH` | 配置文件路径 | `./config.yaml` | `ConfigStorage` |
| `LOG_LEVEL` | 控制台日志级别 | `DEBUG` | `setup_logging` |
| `FILE_LOG_LEVEL` | 文件日志级别 | `DEBUG` | `setup_logging` |
| `LOG_FILE_PATH` | 日志目录 | `./logs` | `setup_logging` |
| `BACKUP_COUNT` | 日志保留天数 | `7` | `setup_logging` |
| `GITHUB_PROXY` | GitHub 代理地址 | — | `Config`、`get_proxy_url` |

### 设置示例

**PowerShell**：

```powershell
$env:LOG_LEVEL = "INFO"
$env:GITHUB_PROXY = "https://proxy.example.com"
python main.py
```

**Linux / macOS**：

```bash
export LOG_LEVEL=INFO
export GITHUB_PROXY=https://proxy.example.com
python main.py
```

**.env 文件**（需框架支持）：

```env
LOG_LEVEL=INFO
FILE_LOG_LEVEL=DEBUG
LOG_FILE_PATH=./logs
BACKUP_COUNT=7
GITHUB_PROXY=https://proxy.example.com
```
