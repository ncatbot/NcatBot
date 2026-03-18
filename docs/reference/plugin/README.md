# 插件系统参考

> 插件基类、Mixin、生命周期的完整 API 参考

**源码位置**：`ncatbot/plugin/`

---

## Quick Reference

```python
from ncatbot.plugin import NcatBotPlugin
```

### NcatBotPlugin 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 插件名称（子类必须定义） |
| `version` | `str` | 插件版本（子类必须定义） |
| `author` | `str` | 作者（默认 `"Unknown"`） |
| `description` | `str` | 描述 |
| `dependencies` | `Dict[str, str]` | 依赖声明 |
| `workspace` | `Path` | 插件工作目录（框架注入） |
| `services` | `ServiceManager` | 服务管理器（框架注入） |
| `api` | `BotAPIClient` | Bot API 客户端（框架注入） |
| `debug` | `bool` | 调试模式 |

### NcatBotPlugin 方法

| 方法 | 签名 | 说明 |
|------|------|------|
| `_init_` | `() → None` | 同步初始化 |
| `on_load` | `async () → None` | 异步初始化 |
| `on_close` | `async () → None` | 异步清理 |
| `_close_` | `() → None` | 同步清理 |
| `meta_data` | `@property → Dict` | 插件元数据字典 |
| `list_plugins` | `() → List[str]` | 已加载插件名称列表 |
| `get_plugin` | `(name) → Optional[BasePlugin]` | 获取已加载的插件实例 |

### Mixin 方法签名

| Mixin | 方法 | 签名 | 说明 |
|-------|------|------|------|
| **ConfigMixin** | `get_config` | `(key, default=None) → Any` | 读取配置 |
| | `set_config` | `(key, value) → None` | 写入并持久化 |
| | `remove_config` | `(key) → bool` | 移除配置项 |
| | `update_config` | `(updates: Dict) → None` | 批量更新 |
| **DataMixin** | `self.data` | `Dict[str, Any]` | JSON 持久化字典 |
| **RBACMixin** | `check_permission` | `(user, permission) → bool` | 权限检查 |
| | `add_permission` | `(path) → None` | 注册权限路径 |
| | `remove_permission` | `(path) → None` | 移除权限路径 |
| | `add_role` | `(role, exist_ok=True) → None` | 创建角色 |
| | `user_has_role` | `(user, role) → bool` | 检查角色归属 |
| | `self.rbac` | `@property → RBACService?` | RBAC 服务实例 |
| **TimeTaskMixin** | `add_scheduled_task` | `(name, interval, conditions=, max_runs=, callback=) → bool` | 添加定时任务 |
| | `remove_scheduled_task` | `(name) → bool` | 移除任务 |
| | `get_task_status` | `(name) → Optional[Dict]` | 任务状态 |
| | `list_scheduled_tasks` | `() → List[str]` | 列出任务 |
| **EventMixin** | `events` | `(event_type=) → EventStream` | 创建事件流 |
| | `wait_event` | `async (predicate=, timeout=) → Event` | 等待匹配事件 |

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1_base_class.md](1_base_class.md) | NcatBotPlugin 完整 API — 属性、方法、继承关系、PluginManifest、依赖解析 |
| [2_mixins.md](2_mixins.md) | EventMixin / TimeTaskMixin / RBACMixin / ConfigMixin / DataMixin 完整 API |
