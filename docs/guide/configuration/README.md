# 配置管理

> NcatBot 的配置体系基于 Pydantic 模型 + YAML 文件，提供类型安全的全局配置、NapCat 连接配置、插件独立配置和安全检查。

---

## Quick Start

### 最小 config.yaml

```yaml
bot_uin: '1234567890'   # 机器人 QQ 号（必须修改）
root: '9876543210'      # 管理员 QQ 号（必须修改）

napcat:
  ws_uri: ws://localhost:3001
  ws_token: napcat_ws

plugin:
  load_plugin: true
```

其余字段均有默认值，文件不存在时使用默认配置。完整字段参见下方 [配置字段速查](#配置字段速查)。

### 读写全局配置

```python
from ncatbot.utils.config import get_config_manager

manager = get_config_manager()

# 读取
print(manager.bot_uin)            # str
print(manager.napcat.ws_uri)      # str

# 修改 + 保存
manager.update_value("debug", True)
manager.save()
```

### 插件配置读写

插件通过 `ConfigMixin` 获得配置读写能力，无需手动管理文件：

```python
from ncatbot.plugin import NcatBotPlugin


class WeatherPlugin(NcatBotPlugin):
    """天气查询插件 — 演示配置读写"""

    async def on_load(self):
        # 读取配置，不存在则使用默认值
        api_key = self.get_config("api_key", "")
        city = self.get_config("default_city", "北京")

        if not api_key:
            self.logger.warning("未配置 API Key，天气功能不可用")

    async def handle_set_city(self, city: str):
        """用户设置默认城市"""
        self.set_config("default_city", city)
        # set_config 立即写入 plugins/WeatherPlugin/config.yaml

    async def handle_update_settings(self, settings: dict):
        """批量更新设置"""
        self.update_config(settings)
        # 例如: {"default_city": "上海", "update_interval": 1800}
```

### 完整配置示例

```yaml
# config.yaml
bot_uin: '1234567890'
root: '9876543210'
debug: false
enable_webui_interaction: true
github_proxy: null
check_ncatbot_update: true
skip_ncatbot_install_check: false
websocket_timeout: 15

napcat:
  ws_uri: ws://localhost:3001
  ws_token: napcat_ws
  ws_listen_ip: localhost
  webui_uri: http://localhost:6099
  webui_token: your_strong_token_here
  enable_webui: true
  enable_update_check: false
  stop_napcat: false
  skip_setup: false

plugin:
  plugins_dir: plugins
  plugin_whitelist: []
  plugin_blacklist: []
  load_plugin: true
  auto_install_pip_deps: true
  plugin_configs:
    MyPlugin:
      api_key: sk-xxxx
      max_retries: 3
```

---

## 配置字段速查

所有配置模型定义在 `ncatbot.utils.config.models` 模块中，基于 Pydantic v2 构建。基类 `BaseConfig` 提供：

- **`validate_assignment=True`** — 属性赋值时自动验证
- **`extra="allow"`** — 允许 YAML 中存在未声明的额外字段，向前兼容

### Config 顶层字段

`Config` 是主配置模型，聚合了 `NapCatConfig` 和 `PluginConfig` 子配置。其 `to_dict()` 排除 `None` 值。

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `bot_uin` | `str` | `"123456"` | 机器人 QQ 号（启动前必须修改） |
| `root` | `str` | `"123456"` | 管理员 QQ 号（启动前必须修改） |
| `debug` | `bool` | `False` | 是否开启调试模式 |
| `enable_webui_interaction` | `bool` | `True` | 是否启用 WebUI 交互 |
| `github_proxy` | `Optional[str]` | 环境变量 `GITHUB_PROXY` | GitHub 代理地址，优先从环境变量读取 |
| `check_ncatbot_update` | `bool` | `True` | 是否在启动时检查 NcatBot 更新 |
| `skip_ncatbot_install_check` | `bool` | `False` | 跳过 NcatBot 安装完整性检查 |
| `websocket_timeout` | `int` | `15` | WebSocket 超时时间（秒），最小值为 1 |
| `napcat` | `NapCatConfig` | — | NapCat 客户端连接子配置 |
| `plugin` | `PluginConfig` | — | 插件相关子配置 |

> **验证规则**：`bot_uin` 和 `root` 会自动转换为字符串类型；`websocket_timeout` 最小值为 1。

### NapCatConfig 字段

`napcat` 节对应 `NapCatConfig` 模型，管理与 NapCat 的通信连接：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `ws_uri` | `str` | `"ws://localhost:3001"` | WebSocket 服务地址 |
| `ws_token` | `str` | `"napcat_ws"` | WebSocket 认证令牌 |
| `ws_listen_ip` | `str` | `"localhost"` | WS 监听 IP（`0.0.0.0` 时触发安全检查） |
| `webui_uri` | `str` | `"http://localhost:6099"` | NapCat WebUI 地址 |
| `webui_token` | `str` | `"napcat_webui"` | WebUI 认证令牌 |
| `enable_webui` | `bool` | `True` | 是否启用 WebUI |
| `enable_update_check` | `bool` | `False` | 是否检查 NapCat 更新 |
| `stop_napcat` | `bool` | `False` | 程序退出时是否同时停止 NapCat |
| `skip_setup` | `bool` | `False` | 跳过 NapCat 初始化设置 |

> **验证规则**：`ws_uri` 必须以 `ws://` 或 `wss://` 开头，否则自动补全；`webui_uri` 必须以 `http://` 或 `https://` 开头，否则自动补全。

**便捷属性**（只读，从 URI 自动解析）：

| 属性 | 返回类型 | 说明 |
|---|---|---|
| `ws_host` | `Optional[str]` | 从 `ws_uri` 中解析的主机名 |
| `ws_port` | `Optional[int]` | 从 `ws_uri` 中解析的端口号 |
| `webui_host` | `Optional[str]` | 从 `webui_uri` 中解析的主机名 |
| `webui_port` | `Optional[int]` | 从 `webui_uri` 中解析的端口号 |

### PluginConfig 字段

`plugin` 节对应 `PluginConfig` 模型：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `plugins_dir` | `str` | `"plugins"` | 插件存放目录 |
| `plugin_whitelist` | `List[str]` | `[]` | 插件白名单（为空则不限制） |
| `plugin_blacklist` | `List[str]` | `[]` | 插件黑名单 |
| `load_plugin` | `bool` | `False` | 是否加载插件 |
| `auto_install_pip_deps` | `bool` | `True` | 是否允许自动安装插件声明的 pip 依赖（仍会先询问确认） |
| `plugin_configs` | `Dict[str, Dict[str, Any]]` | `{}` | 全局配置中的插件配置覆盖，键为插件名 |

> **验证规则**：`plugins_dir` 为空字符串时自动回落为 `"plugins"`。

---

## ConfigMixin API

插件通过 `ConfigMixin`（定义在 `ncatbot.plugin.mixin.config_mixin`）获得配置读写能力。

**生命周期**：加载时从 YAML 读取 → 合并全局覆盖 → 插件运行期间 get/set/update → 卸载时保存。

| 钩子 | 触发时机 | 动作 |
|---|---|---|
| `_mixin_load()` | 插件加载时 | 从 YAML 加载配置 → 合并全局覆盖 |
| `_mixin_unload()` | 插件卸载时 | 将 `self.config` 保存到 YAML |

**方法速查**：

| 方法 | 签名 | 说明 |
|---|---|---|
| `get_config` | `(key: str, default: Any = None) -> Any` | 读取配置值，键不存在返回 `default` |
| `set_config` | `(key: str, value: Any) -> None` | 设置单个配置项并**立即持久化** |
| `remove_config` | `(key: str) -> bool` | 移除配置项并持久化，成功返回 `True` |
| `update_config` | `(updates: Dict[str, Any]) -> None` | 批量更新配置并持久化 |

> `set_config`、`remove_config`、`update_config` 均**立即写入磁盘**，无需手动 save。

---

## 配置优先级

NcatBot 的配置值按以下优先级从高到低生效：

| 优先级 | 来源 | 说明 |
|---|---|---|
| 1（最高） | 代码运行时修改 | `manager.update_value()` / `manager.update_napcat()` |
| 2 | 全局插件覆盖 | `config.yaml` → `plugin.plugin_configs.{插件名}` |
| 3 | 插件本地配置 | `plugins/{插件名}/config.yaml` |
| 4 | 环境变量 | `NCATBOT_CONFIG_PATH`、`GITHUB_PROXY` 等 |
| 5（最低） | 模型默认值 | Pydantic Field 的 `default` / `default_factory` |

---

## 深入阅读

| 文档 | 内容 |
|---|---|
| [ConfigManager 与 ConfigStorage](1_manager.md) | 配置管理器单例、读取/修改/保存 API、原子写入机制、配置文件路径优先级 |
| [配置安全](2_security.md) | 令牌强度检查、自动修复流程、全局配置覆盖机制、插件配置存储位置 |
