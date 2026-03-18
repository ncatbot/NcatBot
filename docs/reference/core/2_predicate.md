# Predicate DSL API 参考

> 完整的 Predicate DSL 类型签名与工厂函数参考。用户指南见 [Predicate DSL 入门](../../guide/plugin/4c.predicate-dsl.md)。

---

## P — 基类

```python
class P(ABC):
    @abstractmethod
    def __call__(self, event: BaseEventData) -> bool: ...

    def __and__(self, other: P) -> AndP: ...
    def __or__(self, other: P) -> OrP: ...
    def __invert__(self) -> NotP: ...

    @staticmethod
    def of(fn: Callable[[BaseEventData], bool]) -> P: ...
```

所有 Predicate 继承自 `P`，支持 `&`（与）、`|`（或）、`~`（非）运算符。

### P.of()

将任意 `Callable[[BaseEventData], bool]` 包装为 `P` 实例：

```python
from ncatbot.core import P
p = P.of(lambda e: e.user_id == "12345")
```

---

## 组合类型

| 类型 | 运算符 | 作用 |
|------|--------|------|
| `AndP(a, b)` | `a & b` | 两者都为 True |
| `OrP(a, b)` | `a \| b` | 任一为 True |
| `NotP(p)` | `~p` | 取反 |

---

## 工厂函数

所有工厂函数从 `ncatbot.core` 导出。

### 事件特征匹配

| 函数 | 签名 | 说明 |
|------|------|------|
| `same_user` | `(event: BaseEventData) -> P` | 匹配相同 `user_id` |
| `same_group` | `(event: BaseEventData) -> P` | 匹配相同 `group_id` |
| `is_private` | `() -> P` | 匹配私聊事件 |
| `is_group` | `() -> P` | 匹配群聊事件 |
| `is_message` | `() -> P` | 匹配类型为 message 的事件 |
| `event_type` | `(type_str: str) -> P` | 匹配指定 `event.type` |

### 消息内容匹配

| 函数 | 签名 | 说明 |
|------|------|------|
| `has_keyword` | `(*keywords: str) -> P` | 消息包含任一关键词 |
| `msg_equals` | `(text: str) -> P` | 消息纯文本完全等于 |
| `msg_in` | `(*texts: str) -> P` | 消息纯文本在指定集合内 |
| `msg_matches` | `(pattern: str) -> P` | 消息纯文本匹配正则 |

### 事件派生

| 函数 | 签名 | 说明 |
|------|------|------|
| `from_event` | `(event: BaseEventData) -> P` | 自动推导同 user + 同 group/私聊 |

`from_event` 规则：
- 如果事件有 `group_id` → `same_user(event) & same_group(event)`
- 否则 → `same_user(event) & is_private()`

---

## 导入

```python
from ncatbot.core import (
    P, AndP, OrP, NotP,
    same_user, same_group, is_private, is_group, is_message,
    has_keyword, msg_equals, msg_in, msg_matches,
    event_type, from_event,
)
```

---

## 延伸阅读

- [Predicate DSL 入门](../../guide/plugin/4c.predicate-dsl.md) — 用法示例与实战模式
- [Dispatcher 内部机制](1_internals.md) — 事件匹配与分发流程
