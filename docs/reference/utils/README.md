# 工具模块参考

> 日志、IO、配置、网络等工具函数完整参考

**源码位置**：`ncatbot/utils/`

---

## Quick Reference

```python
from ncatbot.utils import get_log, post_json, get_json, download_file
```

### 日志 — `get_log`

| 函数/方法 | 签名 | 说明 |
|-----------|------|------|
| `get_log` | `(name=None) → BoundLogger` | 获取日志实例 |
| `.bind` | `(**kwargs) → BoundLogger` | 绑定上下文字段 |
| `.unbind` | `(*keys) → BoundLogger` | 移除上下文字段 |
| `.debug/info/warning/error/critical` | `(msg, *args, **kwargs)` | 各级别日志 |
| `.exception` | `(msg, *args, **kwargs)` | 附带堆栈的 error |

### 配置 — `ConfigManager`

| 方法/属性 | 签名 | 说明 |
|-----------|------|------|
| `get_config_manager` | `(path=None) → ConfigManager` | 获取单例 |
| `.config` | `@property → Config` | 懒加载配置对象 |
| `.bot_uin` | `@property → str` | Bot QQ 号 |
| `.root` | `@property → str` | 管理员 QQ 号 |
| `.debug` | `@property/setter → bool` | 调试模式开关 |
| `.plugin` | `@property → PluginConfig` | 插件子配置 |
| `.update_value` | `(key, value) → None` | 更新配置（支持 `"napcat.ws_uri"` 嵌套键） |
| `.save` | `() → None` | 保存配置 |
| `.reload` | `() → Config` | 重新加载 |
| `.get_adapter_configs` | `() → List[AdapterEntry]` | 已启用适配器列表 |
| `.get_security_issues` | `(auto_fix=True) → List[str]` | 安全检查 |

### 网络 — `post_json` / `get_json` / `download_file`

| 函数 | 签名 | 说明 |
|------|------|------|
| `get_json` | `(url, headers=None, timeout=5.0) → dict` | GET JSON |
| `post_json` | `(url, payload=None, headers=None, timeout=5.0) → dict` | POST JSON |
| `download_file` | `(url, file_name) → None` | 带进度条下载 |
| `get_proxy_url` | `() → str` | GitHub 代理 URL |

### 交互 — `confirm` / `ask` / `select`

| 函数 | 签名 | 说明 |
|------|------|------|
| `confirm` | `(message, *, default=False) → bool` | y/n 确认 |
| `ask` | `(message, *, default="") → str` | 文本输入 |
| `select` | `(message, choices, *, default_index=0) → str` | 列表选择 |
| `async_confirm/ask/select` | 同上（async 版） | 异步版本 |
| `set_non_interactive` | `() → None` | 关闭交互（CI 用） |

### 异常类

| 类 | 构造签名 | 说明 |
|----|----------|------|
| `NcatBotError` | `(info, log=True, stacklevel=3)` | 基础异常（自动日志） |
| `NcatBotValueError` | `(var_name, val_name, must_be=False)` | 值校验异常 |
| `NcatBotConnectionError` | `(info)` | 网络连接异常 |
| `AdapterEventError` | `(info, log=True)` | 适配器事件异常 |

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1a_config.md](1a_config.md) | 配置管理 — ConfigManager、Config / NapCatConfig / PluginConfig 模型 |
| [1b_io_logging.md](1b_io_logging.md) | 日志系统 + 网络工具 — BoundLogger、setup_logging、网络请求 |
| [2_decorators_misc.md](2_decorators_misc.md) | 装饰器 + 杂项工具 — 安全工具、tqdm、环境变量 |
