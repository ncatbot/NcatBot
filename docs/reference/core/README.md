# 核心模块参考

> BotClient / Registry / Dispatcher 核心组件参考。核心引擎提供异步事件分发、处理器注册与 Hook 拦截三大能力，是框架事件驱动架构的基石。

---

## Quick Start

### 最小启动示例

```python
import asyncio
from ncatbot.core.dispatcher import AsyncEventDispatcher, EventType
from ncatbot.core.registry import HandlerDispatcher

async def main():
    # 1. 创建事件分发器
    event_dispatcher = AsyncEventDispatcher(stream_queue_size=500)

    # 2. 创建处理器分发器并启动
    handler_dispatcher = HandlerDispatcher(api=bot_api)
    handler_dispatcher.start(event_dispatcher)

    # 3. 消费事件流
    async with event_dispatcher.events(EventType.MESSAGE) as stream:
        async for event in stream:
            print(event.type, event.data)

    # 4. 关闭
    await handler_dispatcher.stop()
    await event_dispatcher.close()

asyncio.run(main())
```

### 一次性等待事件

```python
# 等待指定群的下一条消息，最多 30 秒
event = await event_dispatcher.wait_event(
    predicate=lambda e: (
        e.type == "message.group"
        and getattr(e.data, "group_id", None) == 12345
    ),
    timeout=30.0,
)
```

---

## 核心类速查

### AsyncEventDispatcher — 异步事件分发器

**模块**: `ncatbot.core.dispatcher.dispatcher`

纯事件路由器——生产端通过 `callback` 接收 `BaseEventData`，消费端通过事件流或一次性等待获取事件。

```python
class AsyncEventDispatcher:
    def __init__(self, stream_queue_size: int = 500): ...
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `stream_queue_size` | `int` | `500` | 每个事件流的内部队列大小，满时丢弃最旧事件 |

#### 核心方法

| 方法/属性 | 签名 | 说明 |
|---|---|---|
| `callback` | `@property → Callable[[BaseEventData], Awaitable[None]]` | 异步回调，供 Adapter 推送事件 |
| `events()` | `(event_type: str \| EventType \| None = None) → EventStream` | 创建事件流（支持类型过滤） |
| `wait_event()` | `(predicate, timeout) → Event` | 等待下一个满足条件的事件 |
| `close()` | `() → None` | 关闭 dispatcher，终止所有流和 waiter（幂等） |

#### callback 内部流程

接收 `BaseEventData` → `_resolve_type()` 推导事件类型字符串 → 构造 `Event` → 广播到所有流队列 + resolve 匹配的 waiter。

#### events() 详细参数

```python
def events(
    self,
    event_type: Optional[Union[str, EventType]] = None,
) -> EventStream: ...
```

**异常**: `RuntimeError` — dispatcher 已关闭时调用。

```python
# 仅消费消息事件
async with dispatcher.events(EventType.MESSAGE) as stream:
    async for event in stream:
        print(event.type, event.data)
```

#### wait_event() 详细参数

```python
async def wait_event(
    self,
    predicate: Optional[Callable[[Event], bool]] = None,
    timeout: Optional[float] = None,
) -> Event: ...
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `predicate` | `Callable[[Event], bool] \| None` | `None` | 过滤函数，`None` 接受任意事件 |
| `timeout` | `float \| None` | `None` | 超时秒数，`None` 无限等待 |

**异常**: `asyncio.TimeoutError`（超时）/ `RuntimeError`（已关闭）

---

### Event — 事件数据类

**模块**: `ncatbot.core.dispatcher.event`

```python
@dataclass(frozen=True, slots=True)
class Event:
    type: str              # resolved 类型字符串，如 "message.group"
    data: "BaseEventData"  # 原始 Pydantic 数据模型
```

`Event` 是 **frozen** 不可变数据类，使用 `__slots__` 优化内存。

#### 事件类型格式

格式为 `"{post_type}.{secondary_type}"`，由 `_resolve_type()` 自动推导：

| post_type | secondary 字段 | 示例 |
|---|---|---|
| `message` | `message_type` | `"message.group"`、`"message.private"` |
| `message_sent` | `message_type` | `"message_sent.group"` |
| `notice` | `notice_type`（`notify` 时取 `sub_type`） | `"notice.group_increase"`、`"notice.poke"` |
| `request` | `request_type` | `"request.friend"`、`"request.group"` |
| `meta_event` | `meta_event_type` | `"meta_event.heartbeat"` |

---

### EventStream — 事件流

**模块**: `ncatbot.core.dispatcher.stream`

通过 `AsyncEventDispatcher.events()` 创建，**不应直接实例化**。

实现了 **异步迭代器** + **异步上下文管理器** 协议：

```python
class EventStream:
    def __aiter__(self) -> "EventStream": ...
    async def __anext__(self) -> Event: ...
    async def __aenter__(self) -> "EventStream": ...
    async def __aexit__(self, ...) -> None: ...
    async def aclose(self) -> None: ...
```

#### 三种使用方式

```python
# 方式 1: async with（推荐，自动关闭）
async with dispatcher.events(EventType.MESSAGE) as stream:
    async for event in stream:
        ...

# 方式 2: 手动管理
stream = dispatcher.events()
async for event in stream:
    ...
await stream.aclose()

# 方式 3: 提前退出
stream = dispatcher.events()
try:
    async for event in stream:
        if should_stop(event):
            break
finally:
    await stream.aclose()
```

#### 类型过滤（前缀匹配）

| 传入类型 | 过滤规则 |
|---|---|
| `EventType.MESSAGE` | 匹配 `"message"` 及 `"message.*"` |
| `"message.group"` | 精确匹配 `"message.group"` |
| `None` | 不过滤，接收全部事件 |

`EventType` 枚举映射：`MESSAGE` → `"message"` / `MESSAGE_SENT` → `"message_sent"` / `NOTICE` → `"notice"` / `REQUEST` → `"request"` / `META` → `"meta_event"`

---

### HandlerDispatcher — 处理器分发器

**模块**: `ncatbot.core.registry.dispatcher`

订阅 `AsyncEventDispatcher` 的事件流，将事件分发到已注册的 handlers。

```python
class HandlerDispatcher:
    def __init__(
        self,
        api: Optional["IBotAPI"] = None,
        service_manager: Optional["ServiceManager"] = None,
    ): ...
```

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `api` | `IBotAPI \| None` | `None` | Bot API 实例，注入到 Hook 上下文和事件实体 |
| `service_manager` | `ServiceManager \| None` | `None` | 服务管理器，注入到 Hook 上下文 |

#### 核心方法

| 方法 | 签名 | 说明 |
|---|---|---|
| `start()` | `(event_dispatcher: AsyncEventDispatcher) → None` | 订阅事件流并启动后台消费循环 |
| `stop()` | `() → None` | 取消后台 task 并关闭事件流 |
| `revoke_plugin()` | `(plugin_name: str) → int` | 移除指定插件的所有 handler，返回移除数量（热重载用） |

---

## 启动流程

核心引擎的启动分为三个阶段：

```
1. 创建阶段
   AsyncEventDispatcher(stream_queue_size) → 初始化事件队列
   HandlerDispatcher(api, service_manager)  → 初始化 handler 存储

2. 连接阶段
   HandlerDispatcher.start(event_dispatcher) → 订阅事件流，启动后台 Task
   Adapter 获取 event_dispatcher.callback   → 建立事件推送通道

3. 运行阶段
   Adapter 推送 BaseEventData → callback → Event → 广播到流
   HandlerDispatcher 消费事件 → 匹配 handler → Hook 链 → 执行
```

关闭时按相反顺序：`HandlerDispatcher.stop()` → `AsyncEventDispatcher.close()`

---

## 深入阅读

| 文档 | 内容 |
|---|---|
| [内部机制](1_internals.md) | 事件匹配算法、分发执行流程、Hook 链执行、错误处理、扩展点 |

---

## 源码位置

| 模块 | 源码位置 |
|---|---|
| `AsyncEventDispatcher` | `ncatbot/core/dispatcher/dispatcher.py` |
| `Event` | `ncatbot/core/dispatcher/event.py` |
| `EventStream` | `ncatbot/core/dispatcher/stream.py` |
| `HandlerDispatcher` | `ncatbot/core/registry/dispatcher.py` |
| `Registrar` | `ncatbot/core/registry/registrar.py` |
| `Hook` / `HookContext` | `ncatbot/core/registry/hook.py` |
| 内置 Hooks | `ncatbot/core/registry/builtin_hooks.py` |
