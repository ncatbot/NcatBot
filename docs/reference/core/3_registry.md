# Registrar 与 Hook/Filter API 参考

> HandlerDispatcher、Registrar 装饰器、Hook 抽象与所有内置 Hook/Filter 的完整签名。

---

## HandlerDispatcher

核心分发引擎，管理处理器注册与事件分发。

```python
class HandlerDispatcher:
    def __init__(self, api: BotAPIClient): ...
    def start(self, event_dispatcher: AsyncEventDispatcher) -> None: ...
    async def stop(self) -> None: ...

    def register(
        self,
        event_type: str,
        handler: Callable,
        *,
        priority: int = 0,
        hooks: List[Hook] = [],
        predicate: Optional[P] = None,
    ) -> None: ...

    def unregister(self, handler: Callable) -> bool: ...
```

| 参数 | 说明 |
|------|------|
| `event_type` | 事件类型字符串（如 `"message.group"`） |
| `handler` | 异步处理函数 `async def handler(ctx: EventContext)` |
| `priority` | 优先级（越大越先执行），默认 `0` |
| `hooks` | Hook 链，按顺序执行 |
| `predicate` | Predicate DSL 条件 |

---

## Registrar 装饰器

通过装饰器注册处理器，在插件中自动绑定到 `HandlerDispatcher`。

### 事件类型装饰器

| 装饰器 | 监听事件类型 | 说明 |
|--------|-------------|------|
| `on(event_type)` | 任意 | 通用注册 |
| `on_message()` | `message.*` | 所有消息 |
| `on_group_message()` | `message.group` | 群消息 |
| `on_private_message()` | `message.private` | 私聊消息 |
| `on_message_sent()` | `message_sent.*` | Bot 自身发出的消息 |
| `on_notice()` | `notice.*` | 所有通知 |
| `on_request()` | `request.*` | 所有请求 |
| `on_meta()` | `meta_event.*` | 元事件 |

### 便捷装饰器

| 装饰器 | 等价于 | 说明 |
|--------|--------|------|
| `on_command(cmd, ...)` | `on_message()` + `CommandHook` | 命令匹配 |
| `on_group_command(cmd, ...)` | `on_group_message()` + `CommandHook` | 群命令 |
| `on_private_command(cmd, ...)` | `on_private_message()` + `CommandHook` | 私聊命令 |
| `on_group_increase()` | `on_notice()` + `NoticeTypeFilter("group_increase")` | 入群 |
| `on_group_decrease()` | `on_notice()` + `NoticeTypeFilter("group_decrease")` | 退群 |
| `on_friend_request()` | `on_request()` + `RequestTypeFilter("friend")` | 加好友 |
| `on_group_request()` | `on_request()` + `RequestTypeFilter("group")` | 加群 |
| `on_poke()` | `on_notice()` + poke 过滤 | 戳一戳 |

### 通用参数

所有装饰器支持：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `priority` | `int` | `0` | 执行优先级 |
| `hooks` | `List[Hook]` | `[]` | Hook 链 |
| `predicate` | `P \| None` | `None` | Predicate DSL |
| `block` | `bool` | `True` | 是否阻止后续处理器 |

---

## Hook 抽象

### Hook 基类

```python
class Hook(ABC):
    @abstractmethod
    async def execute(self, ctx: HookContext) -> HookAction: ...
```

### HookStage — 执行阶段

```python
class HookStage(Enum):
    BEFORE_CALL = "before_call"   # handler 执行前
    AFTER_CALL = "after_call"     # handler 执行后
    ON_ERROR = "on_error"         # handler 抛出异常时
```

### HookAction — 返回动作

```python
class HookAction(Enum):
    CONTINUE = "continue"   # 继续执行
    SKIP = "skip"           # 仅 BEFORE_CALL: 跳过当前 handler
```

### HookContext — 执行上下文

```python
@dataclass
class HookContext:
    event: Event                           # 当前事件
    event_type: str                        # 事件类型字符串
    handler_entry: HandlerEntry            # handler 注册信息
    api: BotAPIClient                      # API 实例
    services: Optional[ServiceManager] = None  # 服务管理器
    kwargs: Dict[str, Any] = field(default_factory=dict)  # 共享参数字典
    result: Any = None                     # handler 返回值（AFTER_CALL 阶段）
    error: Optional[Exception] = None      # 异常对象（ON_ERROR 阶段）
```

---

## 内置 Hook / Filter

### 消息过滤

| 类 | 参数 | 说明 |
|----|------|------|
| `StartsWithHook(prefix)` | `prefix: str` | 消息以指定前缀开头 |
| `KeywordHook(*keywords)` | `*keywords: str` | 消息包含任一关键词 |
| `RegexHook(pattern)` | `pattern: str` | 消息匹配正则表达式 |
| `CommandHook(cmd, ...)` | `cmd: str, aliases=[], prefix="/"` | 命令匹配（含别名、前缀） |

### 类型过滤

| 类 | 参数 | 说明 |
|----|------|------|
| `MessageTypeFilter(type)` | `type: str` (`"group"` / `"private"`) | 按消息类型过滤 |
| `PostTypeFilter(type)` | `type: str` | 按 post_type 过滤 |
| `SubTypeFilter(type)` | `type: str` | 按 sub_type 过滤 |
| `NoticeTypeFilter(type)` | `type: str` | 按 notice_type 过滤 |
| `RequestTypeFilter(type)` | `type: str` | 按 request_type 过滤 |
| `PlatformFilter(platform)` | `platform: str` (`"qq"` / `"telegram"` 等) | 按平台过滤 |

### 特殊过滤

| 类 | 参数 | 说明 |
|----|------|------|
| `SelfFilter()` | — | 过滤 Bot 自身消息 |

---

## 延伸阅读

- [事件注册](../../guide/plugin/4a.event-registration.md) — 装饰器用法入门
- [Hooks 进阶](../../guide/plugin/6.hooks.md) — Hook 链实战
- [Predicate DSL](2_predicate.md) — 条件组合 API
- [Dispatcher 内部机制](1_internals.md) — 分发引擎详解
