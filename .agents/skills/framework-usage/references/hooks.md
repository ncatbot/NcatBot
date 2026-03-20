# Hook 系统参考

> 参考文档：[guide/3. 插件开发/9. Hooks.md](docs/guide/3. 插件开发/9. Hooks.md), [reference/4. 核心模块/1. 内部实现.md](docs/reference/4. 核心模块/1. 内部实现.md)

## Hook 三阶段

| 阶段 | 枚举值 | 作用 | 可返回 |
|------|--------|------|--------|
| `BEFORE_CALL` | `HookStage.BEFORE_CALL` | handler 执行前，可跳过 | `CONTINUE` / `SKIP` |
| `AFTER_CALL` | `HookStage.AFTER_CALL` | handler 成功后 | `CONTINUE` |
| `ON_ERROR` | `HookStage.ON_ERROR` | handler 抛异常时 | `CONTINUE` |

同阶段按 `priority` **降序**执行（数字越大越先执行）。

## 内置 Hook 使用

```python
from ncatbot.core import registrar, add_hooks, group_only, private_only, non_self
from ncatbot.core import startswith, keyword, regex

# 预置单例
@group_only                        # priority=100
@non_self                          # priority=200
@registrar.on_message()
async def handler(self, event): ...

# 组合多个
@add_hooks(group_only, non_self)
@registrar.on_message()
async def handler(self, event): ...

# 文本匹配
@startswith("/")                   # priority=90
@registrar.on_group_message()
async def on_cmd(self, event): ...

@keyword("天气", "weather")         # priority=90
@registrar.on_group_message()
async def on_weather(self, event): ...

@regex(r"(\d+)\s*\+\s*(\d+)")     # priority=90，match 注入 kwargs
@registrar.on_group_message()
async def on_calc(self, event, match=None):
    a, b = int(match.group(1)), int(match.group(2))
    await event.reply(f"{a} + {b} = {a + b}")
```

## 命令参数自动绑定

```python
@registrar.on_group_command("add")
async def on_add(self, event, a: int, b: int):
    await event.reply(f"{a} + {b} = {a + b}")

@registrar.on_group_command("kick")
async def on_kick(self, event, target: At):
    await self.api.qq.manage.set_group_kick(event.group_id, target.qq)
```

**参数绑定规则**：

| 类型注解 | 绑定来源 | 说明 |
|---------|---------|------|
| `At` | `message.filter_at()` | 下一个 @ 对象 |
| `int` / `float` | 文本 token | 自动类型转换 |
| `str`（非最后参数） | 单个文本 token | 消费一个词 |
| `str`（最后参数） | 剩余全部文本 | 空格拼接 |
| 有默认值 | — | 缺失时使用默认值 |
| 必填且缺失 | — | 跳过 handler（SKIP） |

## 内置 Hook 完整清单

### 过滤器（BEFORE_CALL）

| Hook 类 | 构造参数 | 优先级 | 说明 |
|---------|---------|--------|------|
| `MessageTypeFilter(type)` | `"group"` \| `"private"` | 100 | 消息类型过滤 |
| `PostTypeFilter(type)` | `"message"` \| `"notice"` \| `"request"` \| `"meta_event"` | 100 | 事件大类过滤 |
| `SubTypeFilter(sub_type)` | `str` | 100 | 子类型过滤 |
| `SelfFilter()` | — | 200 | 过滤自己消息 |
| `NoticeTypeFilter(type)` | `"group_increase"` 等 | 100 | 通知类型过滤 |
| `RequestTypeFilter(type)` | `"friend"` \| `"group"` | 100 | 请求类型过滤 |

### 匹配器（BEFORE_CALL）

| Hook 类 | 构造参数 | 优先级 | 说明 |
|---------|---------|--------|------|
| `StartsWithHook(prefix)` | `str` | 90 | 前缀匹配 |
| `KeywordHook(*words)` | `str...` | 90 | 关键词（任一命中） |
| `RegexHook(pattern, flags)` | `str`, `int = 0` | 90 | 正则，`ctx.kwargs["match"]` |
| `CommandHook(*names, ignore_case)` | `str...`, `bool = False` | 95 | 命令 + 参数绑定 |

## 自定义 Hook

```python
from ncatbot.core import Hook, HookStage, HookAction, HookContext

class CooldownHook(Hook):
    stage = HookStage.BEFORE_CALL
    priority = 80

    def __init__(self, seconds: float = 5.0):
        self._seconds = seconds
        self._last_use: dict[str, float] = {}

    async def execute(self, ctx: HookContext) -> HookAction:
        import time
        user_id = getattr(ctx.event.data, "user_id", None)
        if user_id is None:
            return HookAction.CONTINUE
        now = time.time()
        last = self._last_use.get(user_id, 0)
        if now - last < self._seconds:
            return HookAction.SKIP
        self._last_use[user_id] = now
        return HookAction.CONTINUE
```

**HookContext 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `event` | `Event` | 原始事件 |
| `event_type` | `str` | 事件类型 |
| `handler_entry` | `HandlerEntry` | handler 信息 |
| `api` | `BotAPIClient` | API 客户端 |
| `services` | `Optional[ServiceManager]` | 服务管理器 |
| `kwargs` | `Dict[str, Any]` | 注入参数 |
| `result` | `Any` | handler 结果（AFTER_CALL） |
| `error` | `Optional[Exception]` | 异常（ON_ERROR） |

## 执行顺序示例

```python
@add_hooks(
    non_self,            # priority=200，最先
    group_only,          # priority=100
    keyword("天气"),      # priority=90
    CooldownHook(5.0),   # priority=80，最后
)
@registrar.on_message()
async def handler(self, event):
    # 不是自己发的 → 群消息 → 包含"天气" → 未在冷却中
    ...
```
