# Mixin 详解

> EventMixin / TimeTaskMixin / RBACMixin / ConfigMixin / DataMixin 完整 API

---

## 1. EventMixin

> 路径：`ncatbot/plugin/mixin/event_mixin.py`

代理 `AsyncEventDispatcher` 的事件消费接口。卸载时自动关闭所有活跃的 `EventStream`。

### 1.1 events()

```python
def events(
    self,
    event_type: Optional[Union[str, EventType]] = None,
) -> EventStream
```

创建事件流，可选按类型过滤。返回的 `EventStream` 支持 `async with` / `async for`。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `event_type` | `str \| EventType \| None` | `None` | 事件类型过滤（前缀匹配），如 `"message"`、`"notice"` |

**返回值**：`EventStream` 异步迭代器

**示例**：

```python
async def on_load(self):
    async with self.events("message") as stream:
        async for event in stream:
            print(event.raw_message)
```

### 1.2 wait_event()

```python
async def wait_event(
    self,
    predicate: Optional[Callable[[Event], bool]] = None,
    timeout: Optional[float] = None,
) -> Event
```

等待下一个满足条件的事件。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `predicate` | `Callable[[Event], bool] \| None` | `None` | 过滤函数，`None` 接受任意事件 |
| `timeout` | `float \| None` | `None` | 超时秒数，`None` 无限等待 |

**返回值**：匹配的 `Event`

**异常**：`asyncio.TimeoutError` — 超时未匹配到事件

**示例**：

```python
# 等待特定用户的下一条消息，最多 30 秒
event = await self.wait_event(
    predicate=lambda e: e.user_id == 12345,
    timeout=30.0,
)
```

---

## 2. TimeTaskMixin

> 路径：`ncatbot/plugin/mixin/time_task_mixin.py`

代理 `TimeTaskService`，提供定时任务的添加、移除、查询接口。
卸载时自动清理本插件注册的所有定时任务。

### 2.1 add_scheduled_task()

```python
@final
def add_scheduled_task(
    self,
    name: str,
    interval: Union[str, int, float],
    conditions: Optional[List[Callable[[], bool]]] = None,
    max_runs: Optional[int] = None,
    callback: Optional[Callable] = None,
) -> bool
```

添加定时任务。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | — | 任务唯一名称 |
| `interval` | `str \| int \| float` | — | 调度参数（见下表） |
| `conditions` | `List[Callable[[], bool]] \| None` | `None` | 执行条件列表，全部为 True 时才执行 |
| `max_runs` | `int \| None` | `None` | 最大执行次数 |
| `callback` | `Callable \| None` | `None` | 自定义回调函数，覆盖默认的同名方法查找 |

**`interval` 支持的格式**：

| 格式 | 示例 | 说明 |
|------|------|------|
| 秒数 | `120`, `0.5` | 整数或浮点数 |
| 时间字符串 | `"30s"`, `"2h30m"`, `"0.5d"` | 人类可读的时间间隔 |
| 每日时间 | `"HH:MM"` | 每天定时执行 |
| 一次性 | `"YYYY-MM-DD HH:MM:SS"` | 指定时刻执行一次 |

**返回值**：`bool` — 是否添加成功

### 2.2 remove_scheduled_task()

```python
@final
def remove_scheduled_task(self, name: str) -> bool
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 任务名称 |

**返回值**：`bool` — 是否移除成功

### 2.3 get_task_status()

```python
@final
def get_task_status(self, name: str) -> Optional[Dict[str, Any]]
```

获取指定任务状态。返回包含 `name`、`next_run`、`run_count`、`max_runs` 的字典，
任务不存在返回 `None`。

### 2.4 list_scheduled_tasks()

```python
@final
def list_scheduled_tasks(self) -> List[str]
```

列出本插件注册的所有定时任务名称。

### 2.5 cleanup_scheduled_tasks()

```python
@final
def cleanup_scheduled_tasks(self) -> None
```

清理本插件的所有定时任务。通常无需手动调用，`_mixin_unload` 钩子会自动执行。

**示例**：

```python
class MyPlugin(NcatBotPlugin):
    name = "heartbeat"
    version = "1.0.0"

    async def on_load(self):
        self.add_scheduled_task("tick", "30s", max_runs=100)

    async def on_close(self):
        pass  # cleanup_scheduled_tasks() 由 _mixin_unload 自动调用
```

---

## 3. RBACMixin

> 路径：`ncatbot/plugin/mixin/rbac_mixin.py`

代理 `RBACService`，提供角色-权限管理的便捷接口。

### 3.1 check_permission()

```python
def check_permission(self, user: str, permission: str) -> bool
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `user` | `str` | 用户标识 |
| `permission` | `str` | 权限路径 |

**返回值**：`bool` — 是否拥有权限，RBAC 服务不可用时返回 `False`

### 3.2 add_permission()

```python
def add_permission(self, path: str) -> None
```

注册权限路径。

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 权限路径，如 `"plugin_name.feature"` |

### 3.3 remove_permission()

```python
def remove_permission(self, path: str) -> None
```

移除权限路径。

### 3.4 add_role()

```python
def add_role(self, role: str, exist_ok: bool = True) -> None
```

创建角色。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `role` | `str` | — | 角色名称 |
| `exist_ok` | `bool` | `True` | 角色已存在时是否忽略 |

### 3.5 user_has_role()

```python
def user_has_role(self, user: str, role: str) -> bool
```

检查用户是否拥有指定角色。RBAC 服务不可用时返回 `False`。

**示例**：

```python
class AdminPlugin(NcatBotPlugin):
    name = "admin"
    version = "1.0.0"

    async def on_load(self):
        self.add_permission("admin.manage")
        self.add_role("admin_role")

    def can_manage(self, user_id: int) -> bool:
        return self.check_permission(str(user_id), "admin.manage")
```

---

## 4. ConfigMixin

> 路径：`ncatbot/plugin/mixin/config_mixin.py`

管理插件 `config.yaml` 的加载、保存和便捷读写。

**生命周期行为**：

| 钩子 | 行为 |
|------|------|
| `_mixin_load` | 从 `workspace/config.yaml` 加载配置到 `self.config`，并合并全局配置覆盖 |
| `_mixin_unload` | 将 `self.config` 保存回 `workspace/config.yaml` |

> 全局配置覆盖：如果 `config.yaml` 中 `plugin.plugin_configs.<plugin_name>` 存在条目，
> 会在加载后覆盖对应配置项（全局优先）。

### 4.1 get_config()

```python
def get_config(self, key: str, default: Any = None) -> Any
```

读取配置值。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `key` | `str` | — | 配置键名 |
| `default` | `Any` | `None` | 键不存在时的默认值 |

### 4.2 set_config()

```python
def set_config(self, key: str, value: Any) -> None
```

设置配置值并**立即持久化**到 `config.yaml`。

### 4.3 remove_config()

```python
def remove_config(self, key: str) -> bool
```

移除配置项并持久化。键不存在返回 `False`。

### 4.4 update_config()

```python
def update_config(self, updates: Dict[str, Any]) -> None
```

批量更新配置并持久化。

**示例**：

```python
class MyPlugin(NcatBotPlugin):
    name = "my_plugin"
    version = "1.0.0"

    async def on_load(self):
        # 首次运行时设置默认配置
        if self.get_config("api_key") is None:
            self.set_config("api_key", "default_key")

        # 批量更新
        self.update_config({"timeout": 30, "retry": 3})

        # 读取
        key = self.get_config("api_key")
```

---

## 5. DataMixin

> 路径：`ncatbot/plugin/mixin/data_mixin.py`

管理插件 `data.json` 的加载和保存，提供 `self.data` 字典供自由读写。

**生命周期行为**：

| 钩子 | 行为 |
|------|------|
| `_mixin_load` | 从 `workspace/data.json` 加载数据到 `self.data` |
| `_mixin_unload` | 将 `self.data` 保存回 `workspace/data.json` |

### 5.1 self.data 字典操作

`self.data` 是一个 `Dict[str, Any]`，支持标准字典操作：

```python
class CounterPlugin(NcatBotPlugin):
    name = "counter"
    version = "1.0.0"

    async def on_load(self):
        # 读取（首次运行时 self.data 为空字典）
        self.data["counter"] = self.data.get("counter", 0) + 1

        # 写入
        self.data["last_online"] = "2026-01-01"

        # 删除
        self.data.pop("temp_key", None)

        # 插件卸载时框架自动保存到 data/<plugin_name>/data.json
```

> ⚠️ **注意**：`self.data` 的修改不会立即持久化，仅在插件卸载时（`_mixin_unload`）
> 自动保存。如需立即保存，可手动调用 `self._save_data()`。

**存储路径**：`data/<plugin_name>/data.json`

---

> **相关文档**：[基类详解](1_base_class.md) · [架构文档](../../architecture.md) · [开发指南](../../guide/)
