# Mixin 详解参考

> 参考文档：`docs/docs/notes/guide/3. 插件开发/7. 配置与数据.md`、`docs/docs/notes/guide/3. 插件开发/8. RBAC 定时任务与事件.md`、`docs/docs/notes/reference/5. 插件系统/2. Mixins.md`

`NcatBotPlugin` 已包含全部 6 个 Mixin，按需使用。

## ConfigMixin — 配置持久化

> 双层模型：插件源码目录 `config.yaml`（低优先级默认值）→ 全局 `config.yaml` 的 `plugin.plugin_configs.<name>`（高优先级覆盖）

| 方法 | 签名 | 说明 |
|------|------|------|
| `get_config` | `(key: str, default: Any = None) -> Any` | 获取 |
| `set_config` | `(key: str, value: Any) -> None` | 设置（立即持久化到全局 config.yaml） |
| `remove_config` | `(key: str) -> bool` | 删除 |
| `update_config` | `(updates: Dict[str, Any]) -> None` | 批量更新 |
| `init_defaults` | `(defaults: Dict[str, Any]) -> None` | 补充缺失默认值（仅内存，不持久化） |

```python
async def on_load(self):
    self.init_defaults({"welcome_msg": "欢迎新成员！", "timeout": 30})

@registrar.on_group_command("set_welcome")
async def set_welcome(self, event, msg: str):
    self.set_config("welcome_msg", msg)
    await event.reply(f"欢迎语已设置为: {msg}")
```

**注意**：`set_config()` 立即写全局 config.yaml，批量用 `update_config()`。`init_defaults()` 仅补充内存中缺失的键，不写磁盘。

## DataMixin — 数据持久化

> 存储到 `{workspace}/data.json`，加载/卸载时自动读写

| 属性 | 说明 |
|------|------|
| `self.data` | `Dict[str, Any]`，直接当字典用 |

```python
async def on_load(self):
    self.data.setdefault("sign_in_count", {})

@registrar.on_group_command("sign")
async def sign_in(self, event):
    uid = event.user_id
    count = self.data["sign_in_count"]
    count[uid] = count.get(uid, 0) + 1
    await event.reply(f"签到成功！累计 {count[uid]} 次")
```

**注意**：用 `setdefault()` 初始化，避免覆盖重启前数据。中途持久化用 `self._save_data()`。

## RBACMixin — 权限控制

> 依赖 RBACService，数据存储在 `data/rbac.json`

| 方法 | 签名 | 说明 |
|------|------|------|
| `check_permission` | `(user: str, permission: str) -> bool` | 检查权限 |
| `add_permission` | `(path: str) -> None` | 注册权限路径 |
| `remove_permission` | `(path: str) -> None` | 移除权限 |
| `add_role` | `(role: str, exist_ok: bool = True) -> None` | 创建角色 |
| `user_has_role` | `(user: str, role: str) -> bool` | 检查角色 |
| `rbac` (property) | `Optional[RBACService]` | RBAC 服务实例 |

```python
async def on_load(self):
    self.add_permission("my_plugin.admin")
    self.add_role("admin", exist_ok=True)

@registrar.on_group_command("admin_cmd")
async def admin_cmd(self, event):
    if not self.check_permission(event.user_id, "my_plugin.admin"):
        await event.reply("权限不足")
        return
    await event.reply("管理员命令已执行")
```

**注意**：`self.rbac` 可能为 None（服务未启动时），`check_permission()` 此时返回 False。`user` 参数始终为 `str`。

## TimeTaskMixin — 定时任务

> 依赖 TimeTaskService

| 方法 | 签名 | 说明 |
|------|------|------|
| `add_scheduled_task` | `(name, interval, conditions=None, max_runs=None, callback=None) -> bool` | 添加 |
| `remove_scheduled_task` | `(name: str) -> bool` | 移除 |
| `get_task_status` | `(name: str) -> Optional[Dict]` | 状态 |
| `list_scheduled_tasks` | `() -> List[str]` | 列出所有 |

### interval 格式

| 格式 | 示例 | 说明 |
|------|------|------|
| 数字 | `60`, `3.5` | 秒数 |
| 时间字符串 | `"30s"`, `"2h30m"` | s/m/h/d 组合 |
| 每日时刻 | `"08:00"`, `"23:30"` | 每天执行 |
| 一次性 | `"2026-03-15 08:00:00"` | 指定时间执行一次 |

```python
async def on_load(self):
    self.add_scheduled_task("heartbeat", 60)
    self.add_scheduled_task("daily_report", "08:00")

async def heartbeat(self):
    print("heartbeat")

async def daily_report(self):
    groups = await self.api.qq.query.get_group_list()
    for g in groups:
        await self.api.qq.post_group_msg(g["group_id"], text="日报...")
```

**注意**：默认回调方法名须与 `add_scheduled_task(name)` 一致，找不到则报错。也可显式传入 `callback` 参数。任务在卸载时自动清理。

## EventMixin — 事件流

| 方法 | 签名 | 说明 |
|------|------|------|
| `events` | `(event_type=None) -> EventStream` | 创建事件流 |
| `wait_event` | `async (predicate=None, timeout=None) -> Event` | 等待单个事件 |
| `wait_session_event` | `async (event, *, timeout, extra_predicate, cancel_words) -> Event` | 同 session 等待，抛异常 |
| `wait_session_reply` | `async (event, *, timeout, cancel_words) -> SessionResult` | 同 session 等文本回复 |
| `session_prompt` | `async (prompt_text, event, *, timeout, cancel_words, timeout_reply, cancel_reply) -> SessionResult` | 发问题+等回复+自动回复 |
| `session_choose` | `async (prompt_text, event, *, choices, timeout, timeout_reply, invalid_reply, max_retries) -> SessionResult` | 选择题+重试 |

```python
import asyncio

async def on_load(self):
    self._task = asyncio.create_task(self._monitor())

async def on_close(self):
    if self._task:
        self._task.cancel()

async def _monitor(self):
    async with self.events("message.group") as stream:
        async for event in stream:
            if "广告" in event.data.message.text:
                await self.api.qq.messaging.delete_msg(event.data.message_id)
```

**Session 便利方法示例**：

```python
# 一站式问答
result = await self.session_prompt(
    "请输入名字：", event,
    timeout=30, cancel_words=["取消"],
    timeout_reply="⏰ 超时", cancel_reply="❌ 已取消",
)
if result.ok:
    name = result.text

# 选择题
result = await self.session_choose(
    "确认？", event,
    choices={"确认": "confirm", "取消": "cancel"},
    timeout=15, max_retries=2,
)
if result.ok and result.key == "confirm":
    ...
```

**注意**：`events()` 流在插件卸载时自动关闭。后台 task 需在 `on_close()` 取消。

## 相关示例

- 配置与数据：`docs/docs/examples/common/02_config_and_data/`
- RBAC 权限：`docs/docs/examples/common/04_rbac/`
- 定时任务：`docs/docs/examples/common/05_scheduled_tasks/`
- 分发过滤：`docs/docs/examples/common/08_dispatch_filter/`

## DispatchFilterMixin — 分发过滤

> 依赖 DispatchFilterService，数据存储在 `data/dispatch_filter.json`
> 参考文档：`docs/docs/notes/reference/5. 插件系统/2. Mixins.md`、`docs/docs/notes/reference/6. 服务层/3. 分发过滤服务.md`

无 RBAC 限制，任何插件均可自由调用。管理范围为全局（不限于本插件）。

| 方法 | 签名 | 说明 |
|------|------|------|
| `block_in_group` | `(group_id: str, plugin_name: str, commands=None) -> Optional[FilterRule]` | 在群中禁用插件或命令 |
| `unblock_in_group` | `(group_id: str, plugin_name: str, commands=None) -> int` | 解除群禁用 |
| `block_for_user` | `(user_id: str, plugin_name: str, commands=None) -> Optional[FilterRule]` | 对用户禁用 |
| `unblock_for_user` | `(user_id: str, plugin_name: str, commands=None) -> int` | 解除用户禁用 |
| `list_filters` | `(scope_type=None, scope_id=None, plugin_name=None) -> List[FilterRule]` | 查询规则 |
| `clear_filters` | `(plugin_name=None) -> int` | 批量清除 |
| `dispatch_filter` (property) | `Optional[DispatchFilterService]` | 服务实例 |

```python
# 在群中禁用某插件
self.block_in_group("12345", "weather_plugin")

# 对用户禁用某命令
self.block_for_user("67890", "my_plugin", commands=["echo"])

# 解除禁用
self.unblock_in_group("12345", "weather_plugin")

# 查询所有规则
rules = self.list_filters()
```

**注意**：`self.dispatch_filter` 可能为 None（服务未启动时），便捷方法此时返回 None 或 0。`plugin_name` 为 `"*"` 时匹配全部插件。
