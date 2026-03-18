# 核心模块参考

> BotClient / Registry / Dispatcher 核心组件参考。核心引擎提供异步事件分发、处理器注册与 Hook 拦截三大能力，是框架事件驱动架构的基石。

---

## Quick Reference

```python
from ncatbot.core import registrar, Hook
```

### 组件角色

| 组件 | 职责 | 关键方法 |
|------|------|---------|
| `AsyncEventDispatcher` | 事件广播 + 事件流 | `callback`, `events(type)`, `wait_event(predicate, timeout)`, `close()` |
| `HandlerDispatcher` | Handler 匹配与执行 | `start(dispatcher)`, `stop()`, `register_handler(...)`, `unregister_handler(entry)`, `revoke_plugin(name)` |
| `Registrar` | 装饰器注册 | `on_group_command(...)`, `on_message(...)`, `on(...)`, `fork(...)` |
| `Hook` (ABC) | 拦截链 | `execute(ctx) → HookAction` — CONTINUE / SKIP |

### Registrar 装饰器索引

| 装饰器 | 监听 |
|--------|------|
| `on(event_type, priority=, platform=)` | 通用 |
| `on_command(*names, ignore_case=)` | 群+私聊命令 |
| `on_group_command(*names, ignore_case=)` | 群命令 |
| `on_private_command(*names, ignore_case=)` | 私聊命令 |
| `on_message()` / `on_group_message()` / `on_private_message()` | 消息 |
| `on_notice()` / `on_request()` / `on_meta()` | 通知/请求/元 |
| `on_poke()` | 戳一戳 |
| `on_group_increase()` / `on_group_decrease()` | 群成员变动 |
| `on_friend_request()` / `on_group_request()` | 好友/群请求 |
| `on_message_sent()` | 消息发送 |

### Hook 系统

| 概念 | 说明 |
|------|------|
| `HookStage` | `BEFORE_CALL`、`AFTER_CALL`、`ON_ERROR` |
| `HookAction` | `CONTINUE`（继续）、`SKIP`（跳过当前 handler） |
| `HookContext` | `event`, `event_type`, `handler_entry`, `api`, `services`, `kwargs`, `result`, `error` |
| `add_hooks(*hooks)` | 批量添加 Hook 装饰器 |
| `get_hooks(func, stage=)` | 获取函数绑定的 hooks |

### 内置 Hook

| Hook 类 | 说明 |
|---------|------|
| `MessageTypeFilter(message_type)` | 过滤 group/private |
| `PostTypeFilter(post_type)` | 过滤 post_type |
| `SubTypeFilter(sub_type)` | 过滤 sub_type |
| `SelfFilter()` | 跳过 bot 自身消息 |
| `PlatformFilter(platform)` | 过滤平台 |
| `CommandHook(*names, ignore_case=)` | 命令匹配 + 参数绑定 |

### Predicate DSL 工厂函数

| 函数 | 说明 |
|------|------|
| `same_user(...)` | 同用户 |
| `same_group(...)` | 同群 |
| `is_private(...)` / `is_group(...)` | 私聊/群聊 |
| `is_message(...)` | 消息类型 |
| `has_keyword(...)` | 包含关键词 |
| `msg_equals(...)` | 精确匹配 |
| `msg_in(...)` | 匹配列表 |
| `msg_matches(...)` | 正则匹配 |
| `event_type(...)` | 事件类型 |
| `from_event(...)` | 同 session（同用户+同群） |

> 运算符：`p1 & p2`（AND）、`p1 | p2`（OR）、`~p`（NOT）

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1_internals.md](1_internals.md) | Dispatcher 分发引擎内部机制详解 |
| [2_predicate.md](2_predicate.md) | Predicate DSL 完整 API 参考 |
| [3_registry.md](3_registry.md) | Registrar + Hook/Filter 完整 API 参考 |
