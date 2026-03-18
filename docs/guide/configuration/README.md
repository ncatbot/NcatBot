# 配置管理

> NcatBot 的配置体系基于 Pydantic 模型 + YAML 文件，提供类型安全的全局配置、适配器连接配置和插件独立配置。

---

## Quick Reference

### Config 模型字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `bot_uin` | `str` | `"123456"` | Bot QQ 号 |
| `root` | `str` | `"123456"` | 超级管理员 QQ 号 |
| `adapters` | `List[AdapterEntry]` | `[]` | 适配器列表 |
| `plugin` | `PluginConfig` | — | 插件配置 |
| `debug` | `bool` | `False` | 调试模式 |
| `websocket_timeout` | `int` | `15` | WebSocket 超时秒数 |
| `check_ncatbot_update` | `bool` | `True` | 启动时检查更新 |

### AdapterEntry 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 适配器类型（如 `"napcat"`） |
| `platform` | `str` | 平台标识（如 `"qq"`） |
| `enabled` | `bool` | 是否启用 |
| `config` | `dict` | 适配器专属配置（`ws_uri`, `ws_token` 等） |

### ConfigManager 方法

| 方法/属性 | 说明 |
|----------|------|
| `get_config_manager()` | 获取全局单例（`from ncatbot.utils import get_config_manager`） |
| `.config` | Config 模型实例 |
| `.bot_uin` | Bot QQ 号 |
| `.debug` | 调试模式 |
| `update_value(key, value)` | 修改配置值 |
| `save()` | 保存到 config.yaml |
| `reload()` | 重新加载配置文件 |
| `get_adapter_configs()` | 获取适配器配置列表 |

### 插件配置方法（ConfigMixin）

| 方法 | 说明 |
|------|------|
| `get_config(key, default=None)` | 读取配置值 |
| `set_config(key, value)` | 设置并立即持久化 |
| `remove_config(key)` | 移除配置项 |
| `update_config(updates: dict)` | 批量更新并持久化 |

### 最小 config.yaml

```yaml
bot_uin: '1234567890'
root: '9876543210'
adapters:
  - type: napcat
    platform: qq
    enabled: true
    config:
      ws_uri: ws://localhost:3001
```

> **旧格式兼容**：如果你的 `config.yaml` 仍使用顶层 `napcat:` 字段，框架会自动迁移为 `adapters:` 列表格式并回写配置文件。

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [配置管理与安全校验](1.config-security.md) | 配置管理器单例、读取/修改/保存 API、令牌强度检查、自动修复流程 |
