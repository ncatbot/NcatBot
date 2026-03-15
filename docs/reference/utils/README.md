# 工具模块参考

> 日志、IO、配置、网络等工具函数完整参考

**源码位置**：`ncatbot/utils/`

---

## Quick Start

### 获取日志器

```python
from ncatbot.utils.logger import get_log

log = get_log("my_module")
log.info("启动完成")
log = log.bind(user_id="12345")   # 绑定上下文
log.info("处理消息")               # extra 自动携带 user_id
```

### 读取配置

```python
from ncatbot.utils.config.manager import get_config_manager

cm = get_config_manager()
print(cm.bot_uin)        # 机器人 QQ 号
print(cm.napcat.ws_uri)  # WebSocket 地址
cm.update_value("debug", True)
cm.save()
```

### 发送网络请求

```python
from ncatbot.utils.network import post_json, get_json, download_file

data = get_json("https://api.example.com/status")
resp = post_json("https://api.example.com/action", payload={"key": "value"})
download_file("https://example.com/file.zip", "local.zip")
```

> 子文档详细 API 参见 [深入阅读](#深入阅读)。

---

## 工具函数速查表

### 配置管理 — `ncatbot/utils/config/`

#### ConfigManager

```python
from ncatbot.utils.config.manager import ConfigManager, get_config_manager
```

| 方法/属性 | 签名 | 说明 |
|-----------|------|------|
| `get_config_manager` | `(path: Optional[str] = None) -> ConfigManager` | 获取全局单例 |
| `.config` | `Config` | 主配置对象（懒加载） |
| `.napcat` | `NapCatConfig` | NapCat 连接子配置 |
| `.plugin` | `PluginConfig` | 插件子配置 |
| `.bot_uin` | `str` | 机器人 QQ 号 |
| `.root` | `str` | 管理员 QQ 号 |
| `.debug` | `bool` | 调试模式开关（可写） |
| `.reload` | `() -> Config` | 从文件重新加载配置 |
| `.save` | `() -> None` | 将当前配置写回文件 |
| `.update_value` | `(key: str, value) -> None` | 更新配置项，支持嵌套键 `"napcat.ws_uri"` |
| `.update_napcat` | `(**kwargs) -> None` | 批量更新 NapCat 子配置 |
| `.get_uri_with_token` | `() -> str` | 返回带 `access_token` 的 WS URI |
| `.is_local` | `() -> bool` | WS 连接是否为本地 |
| `.is_default_uin` | `() -> bool` | QQ 号是否为默认值 |
| `.is_default_root` | `() -> bool` | 管理员号是否为默认值 |
| `.get_security_issues` | `(auto_fix: bool = True) -> List[str]` | 安全检查，`auto_fix=True` 自动修复弱 token |
| `.get_issues` | `() -> List[str]` | 返回所有配置问题 |
| `.ensure_plugins_dir` | `() -> None` | 确保插件目录存在 |

#### Config 模型

```python
from ncatbot.utils.config.models import Config
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `napcat` | `NapCatConfig` | `NapCatConfig()` | NapCat 连接配置 |
| `plugin` | `PluginConfig` | `PluginConfig()` | 插件配置 |
| `bot_uin` | `str` | `"123456"` | 机器人 QQ 号 |
| `root` | `str` | `"123456"` | 管理员 QQ 号 |
| `debug` | `bool` | `False` | 调试模式 |
| `enable_webui_interaction` | `bool` | `True` | 启用 WebUI 交互 |
| `github_proxy` | `Optional[str]` | 环境变量 `GITHUB_PROXY` | GitHub 代理地址 |
| `check_ncatbot_update` | `bool` | `True` | 启动时检查更新 |
| `skip_ncatbot_install_check` | `bool` | `False` | 跳过安装检查 |
| `websocket_timeout` | `int` | `15` | WebSocket 超时秒数（最小 1） |

#### NapCatConfig 模型

```python
from ncatbot.utils.config.models import NapCatConfig
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ws_uri` | `str` | `"ws://localhost:3001"` | WebSocket 连接地址 |
| `ws_token` | `str` | `"napcat_ws"` | WebSocket 认证令牌 |
| `ws_listen_ip` | `str` | `"localhost"` | WS 监听 IP |
| `webui_uri` | `str` | `"http://localhost:6099"` | WebUI 地址 |
| `webui_token` | `str` | `"napcat_webui"` | WebUI 认证令牌 |
| `enable_webui` | `bool` | `True` | 启用 WebUI |
| `enable_update_check` | `bool` | `False` | 启用 NapCat 更新检查 |
| `stop_napcat` | `bool` | `False` | 关闭时停止 NapCat |
| `skip_setup` | `bool` | `False` | 跳过 NapCat 初始化 |
| `ws_host` | `Optional[str]` | — | 从 `ws_uri` 解析的主机名（只读） |
| `ws_port` | `Optional[int]` | — | 从 `ws_uri` 解析的端口号（只读） |
| `webui_host` | `Optional[str]` | — | 从 `webui_uri` 解析的主机名（只读） |
| `webui_port` | `Optional[int]` | — | 从 `webui_uri` 解析的端口号（只读） |

#### PluginConfig 模型

```python
from ncatbot.utils.config.models import PluginConfig
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `plugins_dir` | `str` | `"plugins"` | 插件目录路径 |
| `plugin_whitelist` | `List[str]` | `[]` | 插件白名单 |
| `plugin_blacklist` | `List[str]` | `[]` | 插件黑名单 |
| `load_plugin` | `bool` | `False` | 是否加载插件 |
| `auto_install_pip_deps` | `bool` | `True` | 自动安装插件 pip 依赖 |
| `plugin_configs` | `Dict[str, Dict[str, Any]]` | `{}` | 插件配置覆盖，键为插件名 |

#### ConfigStorage

```python
from ncatbot.utils.config.storage import ConfigStorage
```

| 方法 | 签名 | 说明 |
|------|------|------|
| `__init__` | `(path: Optional[str] = None)` | 路径默认取 `NCATBOT_CONFIG_PATH` 或 `./config.yaml` |
| `load` | `() -> Config` | 读取 YAML 并校验 |
| `save` | `(config: Config) -> None` | 原子写入（临时文件 + `os.replace`） |
| `exists` | `() -> bool` | 配置文件是否存在 |

#### 安全工具

```python
from ncatbot.utils.config.security import strong_password_check, generate_strong_token
```

| 函数 | 签名 | 说明 |
|------|------|------|
| `strong_password_check` | `(password: str) -> bool` | 检查密码强度：≥12 位，含数字大小写特殊符号 |
| `generate_strong_token` | `(length: int = 16) -> str` | 生成满足强度策略的随机 token |

---

### 日志系统 — `ncatbot/utils/logger/`

| 函数/类 | 签名 | 说明 |
|---------|------|------|
| `get_log` | `(name: Optional[str] = None) -> BoundLogger` | 获取日志器实例 |
| `BoundLogger.bind` | `(**kwargs) -> BoundLogger` | 绑定上下文字段 |
| `BoundLogger.unbind` | `(*keys) -> BoundLogger` | 移除上下文字段 |
| `setup_logging` | `(*, console_level, file_level, log_dir, backup_count, routing_rules) -> None` | 全局日志初始化 |
| `ColoredFormatter` | `(datefmt: str)` | 控制台彩色格式化器 |
| `FileFormatter` | `(datefmt: str)` | 文件格式化器 |
| `MessageFoldFilter` | — | 折叠超长消息和 base64 内容 |
| `tqdm` | `(iterable, *, desc, colour, ...)` | 集成 NcatBot 配色的进度条 |

详细参数、级别策略与格式模板 → [1b_io_logging.md](1b_io_logging.md)

---

### 网络工具 — `ncatbot/utils/network.py`

| 函数 | 签名 | 说明 |
|------|------|------|
| `post_json` | `(url, payload=None, headers=None, timeout=5.0) -> dict` | JSON POST 请求 |
| `get_json` | `(url, headers=None, timeout=5.0) -> dict` | JSON GET 请求 |
| `download_file` | `(url: str, file_name: str) -> None` | 下载文件（带 tqdm 进度条） |
| `get_proxy_url` | `() -> str` | 探测并返回可用 GitHub 代理 URL |
| `gen_url_with_proxy` | `(original_url: str) -> str` | 为 GitHub URL 添加代理前缀 |

详细用法与异常说明 → [1b_io_logging.md](1b_io_logging.md#2-网络工具)

---

## 深入阅读

| 文档 | 内容 |
|------|------|
| [1a_io_logging.md](1a_io_logging.md) | 配置管理 — ConfigManager、Config / NapCatConfig / PluginConfig 模型、ConfigStorage |
| [1b_io_logging.md](1b_io_logging.md) | 日志系统 + 网络工具 — BoundLogger、setup_logging、过滤器/格式化器、网络请求 |
| [2_decorators_misc.md](2_decorators_misc.md) | 装饰器 + 杂项工具 — 安全工具、tqdm 进度条、GitHub 代理、环境变量汇总 |
